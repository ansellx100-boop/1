"""State management for processed news items."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .types import ProcessedArticle


@dataclass(slots=True)
class StoredArticle:
    source_id: str
    title: str
    url: str
    published_at: str
    summary: str
    hash: str
    processed_at: str
    attachments: list[str]


class StateStore:
    """JSON-backed storage for processed articles."""

    def __init__(self, path: str = "state/rostekhnadzor_news.json") -> None:
        self.path = Path(path)
        self._entries: Dict[str, StoredArticle] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        for source_id, payload in data.get("items", {}).items():
            self._entries[source_id] = StoredArticle(**payload)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "items": {
                source_id: asdict(entry) for source_id, entry in self._entries.items()
            }
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_known(self, source_id: str) -> bool:
        return source_id in self._entries

    def get_hash(self, source_id: str) -> Optional[str]:
        entry = self._entries.get(source_id)
        return entry.hash if entry else None

    def record(self, article: ProcessedArticle) -> None:
        processed_at = datetime.utcnow().isoformat()
        self._entries[article.source_id] = StoredArticle(
            source_id=article.source_id,
            title=article.title,
            url=article.url,
            published_at=article.published_at.isoformat(),
            summary=article.summary,
            hash=article.hash,
            processed_at=processed_at,
            attachments=article.attachments,
        )
        self.save()

    def list_entries(self) -> Dict[str, StoredArticle]:
        return dict(self._entries)
