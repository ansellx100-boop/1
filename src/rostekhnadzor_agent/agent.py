"""High-level orchestration for the Rostekhnadzor research agent."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .exporters import MarkdownExporter
from .fetchers import RostekhnadzorFetcher
from .parsers import parse_detail, parse_listing, parse_rss
from .storage import StateStore
from .summarizer import SimpleSummarizer
from .types import NewsStub, ProcessedArticle
from .utils import hash_payload


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AgentRunResult:
    processed: List[ProcessedArticle]
    report_path: Optional[Path]
    skipped: int
    errors: List[str]


_UNSET = object()


class RostekhnadzorAgent:
    """Pulls updates from Rostekhnadzor news feeds and produces summaries."""

    def __init__(
        self,
        fetcher: Optional[RostekhnadzorFetcher] = None,
        store: Optional[StateStore] = None,
        summarizer: Optional[SimpleSummarizer] = None,
        exporter: Optional[MarkdownExporter] = _UNSET,
    ) -> None:
        self.fetcher = fetcher or RostekhnadzorFetcher()
        self.store = store or StateStore()
        self.summarizer = summarizer or SimpleSummarizer()
        if exporter is _UNSET:
            self.exporter: Optional[MarkdownExporter] = MarkdownExporter()
        else:
            self.exporter = exporter  # type: ignore[assignment]

    def run(self, limit: Optional[int] = None, force: bool = False) -> AgentRunResult:
        stubs = self._collect_news(limit)
        processed: List[ProcessedArticle] = []
        skipped = 0
        errors: List[str] = []

        for stub in stubs:
            if not force and self.store.is_known(stub.source_id):
                skipped += 1
                continue
            try:
                detail_html = self.fetcher.fetch_detail(stub.url)
                article = parse_detail(
                    detail_html,
                    self.fetcher.config.base_url,
                    fallback_published_at=stub.published_at,
                    source_id=stub.source_id,
                    source_url=stub.url,
                )
                title = stub.title or article.title
                summary = self.summarizer.summarize(
                    article.full_text,
                    fallback=article.lead or stub.summary or title,
                )
                content_hash = hash_payload(article.full_text, summary)
                known_hash = self.store.get_hash(stub.source_id)
                if not force and known_hash and known_hash == content_hash:
                    skipped += 1
                    continue
                processed_article = ProcessedArticle(
                    source_id=stub.source_id,
                    title=title,
                    url=stub.url,
                    published_at=article.published_at,
                    summary=summary,
                    lead=article.lead,
                    full_text=article.full_text,
                    attachments=article.attachments,
                    hash=content_hash,
                )
                self.store.record(processed_article)
                processed.append(processed_article)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Failed to process article %s", stub.url)
                errors.append(f"{stub.url}: {exc}")

        report_path = self.exporter.export(processed) if self.exporter else None
        return AgentRunResult(processed=processed, report_path=report_path, skipped=skipped, errors=errors)

    def _collect_news(self, limit: Optional[int]) -> List[NewsStub]:
        collected: Dict[str, NewsStub] = {}
        base_url = self.fetcher.config.base_url

        # Try RSS first for efficiency
        try:
            rss_content = self.fetcher.fetch_rss()
            for stub in parse_rss(rss_content, base_url):
                collected.setdefault(stub.source_id, stub)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("RSS fetch failed, falling back to HTML: %s", exc)

        # Fallback to HTML listing if needed or to enrich existing stubs
        if not collected:
            try:
                listing_html = self.fetcher.fetch_listing()
                for stub in parse_listing(listing_html, base_url):
                    collected.setdefault(stub.source_id, stub)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Listing fetch failed: %s", exc)
        else:
            try:
                listing_html = self.fetcher.fetch_listing()
                for stub in parse_listing(listing_html, base_url):
                    collected.setdefault(stub.source_id, stub)
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("Listing enrichment failed: %s", exc)

        stubs = sorted(collected.values(), key=lambda item: item.published_at, reverse=True)
        if limit is not None:
            stubs = stubs[:limit]
        return stubs
