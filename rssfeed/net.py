# Путь: backend/rssfeed/net.py
# Назначение: Универсальный HTTP-клиент для RSS/HTML с ретраями, бэкоффом, корректным User-Agent
#             и пер-доменными таймаутами/заголовками. Возвращает bytes.
# Что внутри:
#   - build_session(): requests.Session с HTTPAdapter(Retry)
#   - get_timeouts_for(url): (connect/read/retries) с overrides из .env (JSON)
#   - fetch_url(): GET/HEAD с ретраями → FetchResult
#   - get_rss_bytes(): сахар для RSS (bytes, encoding, meta)
#
# Переменные окружения (.env):
#   RSS_CONNECT_TIMEOUT=5
#   RSS_READ_TIMEOUT=12
#   RSS_MAX_RETRIES=3
#   RSS_BACKOFF=0.8
#   RSS_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
#   RSS_TIMEOUT_OVERRIDES={"aif.ru":{"read":28,"connect":5,"retries":4},"www.aif.ru":{"read":28,"connect":5,"retries":4}}
#   RSS_HEADERS_OVERRIDES={"aif.ru":{"Accept":"application/rss+xml, application/xml;q=0.9, */*;q=0.8"}}
from __future__ import annotations

import json
import logging
import os
import socket
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v is not None else default

DEFAULT_CONNECT_TIMEOUT = float(_env("RSS_CONNECT_TIMEOUT", "5"))
DEFAULT_READ_TIMEOUT = float(_env("RSS_READ_TIMEOUT", "12"))
DEFAULT_MAX_RETRIES = int(_env("RSS_MAX_RETRIES", "3"))
DEFAULT_BACKOFF = float(_env("RSS_BACKOFF", "0.8"))
DEFAULT_UA = _env(
    "RSS_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

def _load_json_env(name: str) -> Dict:
    raw = _env(name, "")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        log.warning("Не удалось распарсить %s, используем пустой словарь", name)
        return {}

TIMEOUT_OVERRIDES: Dict[str, Dict] = _load_json_env("RSS_TIMEOUT_OVERRIDES")
HEADERS_OVERRIDES: Dict[str, Dict] = _load_json_env("RSS_HEADERS_OVERRIDES")


@dataclass
class FetchResult:
    url: str
    status: int
    headers: Dict[str, str]
    data: bytes
    elapsed_s: float


def build_session(pool_maxsize: int = 20) -> requests.Session:
    """Создаёт Session с ретраями и адекватными параметрами для парсинга RSS/HTML."""
    sess = requests.Session()

    retry = Retry(
        total=DEFAULT_MAX_RETRIES,
        connect=DEFAULT_MAX_RETRIES,
        read=DEFAULT_MAX_RETRIES,
        status=DEFAULT_MAX_RETRIES,
        allowed_methods=frozenset({"GET", "HEAD"}),
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=DEFAULT_BACKOFF,
        raise_on_status=False,
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=pool_maxsize, pool_connections=pool_maxsize)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)

    sess.headers.update({
        "User-Agent": DEFAULT_UA,
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        "Accept-Language": "ru,en;q=0.8",
        "Connection": "keep-alive",
    })
    return sess


_session = build_session()


def get_timeouts_for(url: str) -> Tuple[float, float, int]:
    """Возвращает (connect, read, retries) с учётом overrides по домену."""
    host = (urlparse(url).hostname or "").lower()
    o = TIMEOUT_OVERRIDES.get(host, {})
    connect = float(o.get("connect", DEFAULT_CONNECT_TIMEOUT))
    read = float(o.get("read", DEFAULT_READ_TIMEOUT))
    retries = int(o.get("retries", DEFAULT_MAX_RETRIES))
    return connect, read, retries


def get_extra_headers_for(url: str) -> Dict[str, str]:
    host = (urlparse(url).hostname or "").lower()
    return HEADERS_OVERRIDES.get(host, {})


def fetch_url(url: str, method: str = "GET", stream: bool = False, timeout: Optional[Tuple[float, float]] = None) -> FetchResult:
    """
    Универсальный HTTP-фетч с ретраями и корректными таймаутами.
    Возвращает bytes (не текст) — безопаснее для feedparser/HTML-парсинга.
    """
    connect_t, read_t, retries = get_timeouts_for(url)
    if timeout:
        connect_t, read_t = timeout

    # Если для домена задано иное число ретраев — создаём локальную сессию
    if retries != DEFAULT_MAX_RETRIES:
        local = build_session()
        retry = Retry(
            total=retries, connect=retries, read=retries, status=retries,
            allowed_methods=frozenset({"GET", "HEAD"}),
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=DEFAULT_BACKOFF,
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=20, pool_connections=20)
        local.mount("https://", adapter)
        local.mount("http://", adapter)
        sess = local
    else:
        sess = _session

    headers = get_extra_headers_for(url)
    start = time.time()
    try:
        resp = sess.request(method.upper(), url, timeout=(connect_t, read_t), stream=stream, headers=headers)
        content = resp.content if not stream else b"".join(resp.iter_content(chunk_size=65536))
        elapsed = time.time() - start
        return FetchResult(
            url=str(resp.url),
            status=resp.status_code,
            headers={k.lower(): v for k, v in resp.headers.items()},
            data=content,
            elapsed_s=elapsed,
        )
    except requests.exceptions.ReadTimeout:
        # Для «тугодумов» (например, aif.ru) дадим один повтор с большим read-timeout
        log.warning("ReadTimeout для %s при read=%s — пробуем ещё раз с read=%s", url, read_t, read_t + 10)
        resp = _session.request(method.upper(), url, timeout=(connect_t, read_t + 10), stream=stream, headers=headers)
        content = resp.content if not stream else b"".join(resp.iter_content(chunk_size=65536))
        elapsed = time.time() - start
        return FetchResult(
            url=str(resp.url),
            status=resp.status_code,
            headers={k.lower(): v for k, v in resp.headers.items()},
            data=content,
            elapsed_s=elapsed,
        )
    except (requests.exceptions.ConnectionError, socket.gaierror) as e:
        log.error("Connection error for %s: %s", url, e)
        raise
    except Exception:
        log.exception("Неожиданная ошибка при запросе %s", url)
        raise


def get_rss_bytes(url: str) -> Tuple[bytes, Optional[str], FetchResult]:
    """
    Упрощённый хелпер для RSS:
      Возвращает (data_bytes, apparent_encoding, fetch_result)
    """
    res = fetch_url(url, method="GET", stream=False)
    enc = None
    ctype = res.headers.get("content-type", "")
    if "charset=" in ctype:
        try:
            enc = ctype.split("charset=", 1)[1].split(";")[0].strip()
        except Exception:
            enc = None
    return res.data, enc, res
