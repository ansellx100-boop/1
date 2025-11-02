"""Utility helpers for the Rostekhnadzor agent."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import urljoin, urlparse


LISTING_DATE_FORMAT = "%d.%m.%Y"
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(value: str) -> str:
    """Collapse whitespace characters into single spaces."""

    return _WHITESPACE_RE.sub(" ", value.strip())


def make_absolute_url(base: str, url: str) -> str:
    """Join a potentially relative URL with the base host."""

    return urljoin(base, url)


def extract_source_id(url: str) -> str:
    """Build a stable ID from a Rostekhnadzor news URL."""

    parsed = urlparse(url)
    path = parsed.path.strip("/")
    # For URLs like /news/67/19595/ -> return news/67/19595
    return path.rstrip("/")


def parse_listing_date(value: str) -> datetime:
    """Parse a date coming from the HTML listing (format dd.mm.yyyy)."""

    return datetime.strptime(value.strip(), LISTING_DATE_FORMAT)


def parse_rss_date(value: str) -> Optional[datetime]:
    """Parse a date from RSS feed using email.utils."""

    if not value:
        return None
    parsed = parsedate_to_datetime(value)
    if parsed and parsed.tzinfo:
        return parsed.astimezone(tz=None).replace(tzinfo=None)
    return parsed


def hash_payload(*parts: str) -> str:
    """Generate SHA-256 hash from payload parts."""

    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
    return digest.hexdigest()
