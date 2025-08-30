"""Management command to fetch RSS/Atom feeds without external deps."""

from __future__ import annotations

import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Iterable, List, Tuple

from django.core.management.base import BaseCommand
from django.utils import timezone

from aggregator.models import Item, Source


def _text(el, path: str) -> str:
    found = el.find(path)
    if found is None:
        return ""
    return (found.text or "").strip()


def parse_feed(data: bytes, limit: int | None = None) -> Tuple[str, List[dict]]:
    """Return feed format and list of parsed item dictionaries."""

    root = ET.fromstring(data)
    tag = root.tag.lower()
    fmt = "atom" if tag.endswith("feed") else "rss"

    if fmt == "rss":
        channel = root.find("channel")
        entries: Iterable[ET.Element] = channel.findall("item") if channel is not None else []
    else:  # atom
        entries = root.findall("{*}entry")

    parsed: List[dict] = []
    for entry in list(entries)[: limit or None]:
        guid = _text(entry, "guid") or _text(entry, "{*}id")

        # link handling differs between RSS and Atom
        link = ""
        if fmt == "rss":
            link = _text(entry, "link")
        else:
            link_el = entry.find("{*}link[@rel='alternate']") or entry.find("{*}link")
            if link_el is not None:
                link = (link_el.attrib.get("href") or link_el.text or "").strip()

        title = _text(entry, "title")
        summary = _text(entry, "description") or _text(entry, "{*}summary")
        author = _text(entry, "author")
        category = _text(entry, "category")

        image = ""
        media = entry.find("{*}content") or entry.find("enclosure")
        if media is not None:
            image = media.attrib.get("url", "").strip()

        pub_raw = _text(entry, "pubDate") or _text(entry, "{*}updated")
        published_at = None
        if pub_raw:
            try:
                dt = parsedate_to_datetime(pub_raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                published_at = dt.astimezone(timezone.utc)
            except Exception:
                published_at = None

        content_hash = hashlib.sha1(f"{link}|{title}".encode("utf-8")).hexdigest()

        parsed.append(
            {
                "guid": guid,
                "link": link,
                "title": title,
                "summary": summary,
                "author": author,
                "category": category,
                "image_url": image,
                "published_at": published_at,
                "content_hash": content_hash,
            }
        )

    return fmt, parsed


class Command(BaseCommand):
    """Import RSS/Atom feeds into the database."""

    help = "Fetch configured RSS/Atom sources and store entries"  # noqa: A003

    def add_arguments(self, parser):  # pragma: no cover - argparse boilerplate
        parser.add_argument("--source", help="Filter by source id or URL")
        parser.add_argument("--limit", type=int, help="Limit items per source")
        parser.add_argument(
            "--dry-run", action="store_true", help="Parse but do not write"
        )

    def handle(self, *args, **opts):  # pragma: no cover - integration code
        qs = Source.objects.filter(is_active=True)
        src_opt = opts.get("source")
        if src_opt:
            if src_opt.isdigit():
                qs = qs.filter(pk=int(src_opt))
            else:
                qs = qs.filter(url=src_opt)

        limit = opts.get("limit")
        dry = opts.get("dry_run")

        for source in qs:
            created = updated = skipped = 0
            try:
                with urllib.request.urlopen(source.url, timeout=10) as resp:
                    data = resp.read()
            except Exception as exc:
                self.stderr.write(f"{source.url}: {exc}")
                continue

            fmt, items = parse_feed(data, limit=limit)
            fetched = len(items)
            if source.format != fmt:
                source.format = fmt
                if not dry:
                    source.save(update_fields=["format"])

            for info in items:
                if not info["link"] or not info["title"]:
                    skipped += 1
                    continue

                lookup = {"source": source}
                if info["guid"]:
                    lookup["guid"] = info["guid"]
                else:
                    lookup["link"] = info["link"]

                obj, was_created = Item.objects.get_or_create(
                    **lookup, defaults={"content_hash": info["content_hash"], "title": info["title"], "link": info["link"]}
                )
                if was_created:
                    created += 1
                else:
                    changed = False
                    for field in [
                        "link",
                        "title",
                        "summary",
                        "author",
                        "category",
                        "image_url",
                        "published_at",
                        "content_hash",
                    ]:
                        value = info.get(field)
                        if value and getattr(obj, field) != value:
                            setattr(obj, field, value)
                            changed = True
                    if changed and not dry:
                        obj.save()
                        updated += 1
                    elif not changed:
                        skipped += 1

                if was_created and not dry:
                    for field in [
                        "summary",
                        "author",
                        "category",
                        "image_url",
                        "published_at",
                    ]:
                        value = info.get(field)
                        if value:
                            setattr(obj, field, value)
                    obj.save()

            self.stdout.write(
                f"{source.url}: fetched={fetched} created={created} updated={updated} skipped={skipped}"
            )

