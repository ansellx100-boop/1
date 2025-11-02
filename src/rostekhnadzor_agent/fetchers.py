"""HTTP clients responsible for fetching Rostekhnadzor content."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import requests


DEFAULT_BASE_URL = "https://www.gosnadzor.ru"
DEFAULT_USER_AGENT = "RostekhnadzorAgent/0.1 (+https://example.com/contact)"


@dataclass(slots=True)
class FetcherConfig:
    base_url: str = DEFAULT_BASE_URL
    timeout: int = 15
    retries: int = 3
    backoff_seconds: float = 1.0
    user_agent: str = DEFAULT_USER_AGENT


class RostekhnadzorFetcher:
    """Wrapper around `requests` with retry/backoff."""

    def __init__(self, config: Optional[FetcherConfig] = None) -> None:
        self.config = config or FetcherConfig()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.config.user_agent})

    def fetch_listing(self) -> str:
        return self._request(f"{self.config.base_url}/news/")

    def fetch_rss(self) -> str:
        return self._request(f"{self.config.base_url}/news/rss/")

    def fetch_detail(self, url: str) -> str:
        if not url.startswith("http"):
            url = f"{self.config.base_url.rstrip('/')}/{url.lstrip('/')}"
        return self._request(url)

    def _request(self, url: str) -> str:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.config.retries + 1):
            try:
                response = self._session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or response.encoding
                return response.text
            except Exception as exc:  # pylint: disable=broad-except
                last_exc = exc
                if attempt < self.config.retries:
                    time.sleep(self.config.backoff_seconds * attempt)
        if last_exc:
            raise last_exc
        raise RuntimeError(f"Failed to fetch URL: {url}")
