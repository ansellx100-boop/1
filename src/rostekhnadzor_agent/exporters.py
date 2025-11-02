"""Export utilities for processed news."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from .types import ProcessedArticle


class MarkdownExporter:
    def __init__(self, output_dir: str = "reports") -> None:
        self.output_dir = Path(output_dir)

    def export(self, articles: Iterable[ProcessedArticle], run_date: Optional[datetime] = None) -> Optional[Path]:
        articles = list(articles)
        if not articles:
            return None
        run_date = run_date or datetime.utcnow()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"rostekhnadzor_{run_date.date().isoformat()}.md"
        target = self.output_dir / filename
        content = self._render(articles, run_date)
        target.write_text(content, encoding="utf-8")
        return target

    def _render(self, articles: List[ProcessedArticle], run_date: datetime) -> str:
        lines = [
            f"# \u0420\u043e\u0441\u0442\u0435\u0445\u043d\u0430\u0434\u0437\u043e\u0440 \u2014 \u0434\u0430\u0439\u0434\u0436\u0435\u0441\u0442 {run_date.date().isoformat()}",
            "",
            f"\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u043d\u043e \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u043e\u0432: {len(articles)}",
            "",
        ]
        for article in sorted(articles, key=lambda a: a.published_at, reverse=True):
            lines.extend(self._render_article(article))
        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _render_article(article: ProcessedArticle) -> List[str]:
        lines = [
            f"## {article.title}",
            f"\u0414\u0430\u0442\u0430 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438: {article.published_at.date().isoformat()}",
            "",
        ]
        if article.summary:
            lines.extend([article.summary, ""])
        lines.append(f"\u0427\u0438\u0442\u0430\u0442\u044c \u043f\u043e\u043b\u043d\u043e\u0441\u0442\u044c\u044e: {article.url}")
        if article.attachments:
            lines.append("\u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f:")
            for attachment in article.attachments:
                lines.append(f"- {attachment}")
        lines.append("")
        return lines
