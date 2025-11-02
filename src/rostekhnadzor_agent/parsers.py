"""HTML and RSS parsing utilities."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Iterable, List

from bs4 import BeautifulSoup

from .types import ArticleContent, NewsStub
from .utils import (
    extract_source_id,
    make_absolute_url,
    normalize_whitespace,
    parse_listing_date,
    parse_rss_date,
)


_READ_MORE_RE = re.compile(
    r"(?iu)\u0427\u0438\u0442\u0430\u0442\u044c\s+\u0434\u0430\u043b\u0435\u0435.*"
)


def parse_listing(html_content: str, base_url: str) -> List[NewsStub]:
    soup = BeautifulSoup(html_content, "html.parser")
    items: List[NewsStub] = []
    for node in soup.select("p.news-item"):
        link = node.find("a", href=True)
        date_node = node.select_one(".news-date-time")
        if not link or not date_node:
            continue
        published_at = parse_listing_date(date_node.get_text())
        url = make_absolute_url(base_url, link["href"])
        title = normalize_whitespace(link.get_text())
        summary = _extract_summary(node, date_node)
        items.append(
            NewsStub(
                source_id=extract_source_id(url),
                title=title,
                url=url,
                published_at=published_at,
                summary=summary,
                raw={"source": "listing"},
            )
        )
    return items


def parse_detail(
    html_content: str,
    base_url: str,
    fallback_published_at: datetime,
    source_id: str,
    source_url: str,
) -> ArticleContent:
    soup = BeautifulSoup(html_content, "html.parser")
    container = soup.select_one("div.news-detail")
    if container is None:
        raise ValueError("Unable to locate article body (div.news-detail)")

    title_node = container.find(["h1", "h2"])
    title = normalize_whitespace(title_node.get_text()) if title_node else ""

    date_node = container.select_one(".news-date-time")
    if date_node:
        try:
            published_at = parse_listing_date(date_node.get_text())
        except ValueError:
            published_at = fallback_published_at
    else:
        published_at = fallback_published_at

    paragraphs: List[str] = []
    for element in container.find_all(["p", "li"]):
        text = normalize_whitespace(element.get_text(" "))
        if text:
            paragraphs.append(text)

    lead = paragraphs[0] if paragraphs else None
    full_text = "\n\n".join(paragraphs)

    attachments = _extract_attachments(container, base_url)

    return ArticleContent(
        source_id=source_id,
        url=source_url,
        title=title,
        published_at=published_at,
        lead=lead,
        full_text=full_text,
        attachments=attachments,
        raw_html=html_content,
    )


def parse_rss(xml_content: str, base_url: str) -> List[NewsStub]:
    root = ET.fromstring(xml_content)
    items: List[NewsStub] = []
    for item in root.findall("./channel/item"):
        title = _node_text(item.find("title"))
        link = _node_text(item.find("link"))
        pub_date_raw = _node_text(item.find("pubDate"))
        description = _node_text(item.find("description"))
        if not link:
            continue
        url = make_absolute_url(base_url, link)
        published_at = parse_rss_date(pub_date_raw) or datetime.utcnow()
        summary = _clean_description(description)
        items.append(
            NewsStub(
                source_id=extract_source_id(url),
                title=normalize_whitespace(title),
                url=url,
                published_at=published_at,
                summary=summary,
                raw={"source": "rss"},
            )
        )
    return items


def _extract_summary(node, date_node) -> str:
    text = normalize_whitespace(node.get_text(" "))
    date_text = normalize_whitespace(date_node.get_text())
    if text.startswith(date_text):
        text = text[len(date_text) :].strip()
    text = _READ_MORE_RE.sub("", text)
    return text.strip()


def _extract_attachments(container, base_url: str) -> List[str]:
    attachments: List[str] = []
    for link in container.find_all("a", href=True):
        href = link["href"]
        if _is_document(href):
            attachments.append(make_absolute_url(base_url, href))
    return attachments


def _is_document(href: str) -> bool:
    lowered = href.lower()
    return lowered.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx"))


def _node_text(element) -> str:
    if element is None:
        return ""
    return normalize_whitespace(html.unescape(element.text or ""))


def _clean_description(text: str) -> str:
    if not text:
        return ""
    cleaned = normalize_whitespace(html.unescape(text))
    return _READ_MORE_RE.sub("", cleaned)
