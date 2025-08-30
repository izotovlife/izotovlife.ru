"""Unit tests for feed parsing logic."""

from pathlib import Path
import hashlib
import os
import sys

import pytest
import django

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from aggregator.management.commands.pull_feeds import parse_feed


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_rss_sample():
    data = (FIXTURES / "sample_rss.xml").read_bytes()
    fmt, items = parse_feed(data)
    assert fmt == "rss"
    assert len(items) == 2
    first = items[0]
    assert first["title"] == "First"
    assert first["link"] == "http://example.com/1"
    assert first["content_hash"] == hashlib.sha1(
        b"http://example.com/1|First"
    ).hexdigest()

