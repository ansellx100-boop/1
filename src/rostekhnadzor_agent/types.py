"""Domain models for the Rostekhnadzor research agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True, slots=True)
class NewsStub:
    """Metadata about a news item extracted from RSS or the listing page."""

    source_id: str
    title: str
    url: str
    published_at: datetime
    summary: Optional[str] = None
    section: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(slots=True)
class ArticleContent:
    """Full article content parsed from the detail page."""

    source_id: str
    url: str
    title: str
    published_at: datetime
    lead: Optional[str]
    full_text: str
    attachments: List[str]
    raw_html: str


@dataclass(slots=True)
class ProcessedArticle:
    """Final representation after summarisation and enrichment."""

    source_id: str
    title: str
    url: str
    published_at: datetime
    summary: str
    lead: Optional[str]
    full_text: str
    attachments: List[str]
    hash: str
