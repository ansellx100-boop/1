"""Summarization helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass


_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(slots=True)
class SimpleSummarizer:
    sentences: int = 3
    max_characters: int = 600

    def summarize(self, text: str, fallback: str | None = None) -> str:
        if not text:
            return fallback or ""
        candidates = _SENTENCE_BOUNDARY_RE.split(text.strip())
        if not candidates:
            return text.strip()[: self.max_characters]
        summary = " ".join(candidate.strip() for candidate in candidates[: self.sentences] if candidate.strip())
        summary = summary.strip()
        if not summary:
            summary = text.strip()
        if len(summary) > self.max_characters:
            truncated = summary[: self.max_characters].rsplit(" ", 1)[0]
            summary = truncated + "..."
        return summary
