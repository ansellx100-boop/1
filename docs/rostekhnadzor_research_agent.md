## Goal

Deliver an autonomous research agent that monitors the official Rostekhnadzor web site (`https://www.gosnadzor.ru`), extracts fresh publications, and prepares a concise digest for internal knowledge bases, reports, or alerts.

## Data Sources

- `https://www.gosnadzor.ru/news/` - main HTML listing with 20 recent news items.
- `https://www.gosnadzor.ru/news/rss/` - RSS feed for early change detection.
- Article detail pages `/news/<section>/<id>/` - full text, metadata, and attachments (PDF, DOC, XLS).

## System Architecture

- **Scheduler / Runner**: cron, systemd timer, Airflow, or CI job that calls the agent on schedule.
- **Fetcher**: `requests` client with retries, backoff, custom user-agent, optional proxy.
- **Parser**: `BeautifulSoup` for HTML nodes (`p.news-item`, `div.news-detail`), `xml.etree` for RSS.
- **State Store**: JSON/SQLite keyed by `source_id`, stores published date, hash, and status.
- **Summarizer**: lightweight heuristic summary (first N sentences) with optional LLM provider adapter.
- **Exporter / Notifier**: Markdown reports, Slack/Telegram webhooks, e-mail.
- **Observability**: structured logs, counters (new items, errors, latency).

## Processing Flow

1. Scheduler invokes `Agent.run()` with configuration parameters.
2. Agent initialises fetcher, parser, summariser, state store, exporter.
3. Fetcher downloads RSS; if nothing new is found, it falls back to the HTML listing.
4. New or updated items are compared against the state store.
5. Detail pages are fetched; the parser extracts full text, metadata, and attachments.
6. Summariser produces a short brief (title + 2-3 key sentences).
7. State store records the processed item with a SHA-256 hash of the content.
8. Exporter assembles a digest and dispatches notifications.
9. Agent emits a run report (JSON/Markdown) and exits.

## Current Repository Layout

- `src/rostekhnadzor_agent/fetchers.py` - HTTP client with retries and user-agent control.
- `src/rostekhnadzor_agent/parsers.py` - RSS/HTML parsing, attachment discovery.
- `src/rostekhnadzor_agent/storage.py` - JSON state store with content hashes.
- `src/rostekhnadzor_agent/summarizer.py` - simple sentence-based summariser.
- `src/rostekhnadzor_agent/exporters.py` - Markdown report generation.
- `src/rostekhnadzor_agent/agent.py` - orchestration logic.
- `src/rostekhnadzor_agent/cli.py` - `python -m rostekhnadzor_agent.cli run` entry point.

Quick local run without installing the package: `PYTHONPATH=src python3 -m rostekhnadzor_agent.cli run --limit 5`.

## Configuration Blueprint

```yaml
interval_minutes: 60
sources:
  - type: rss
    url: "https://www.gosnadzor.ru/news/rss/"
    enabled: true
  - type: html
    url: "https://www.gosnadzor.ru/news/"
    enabled: true
http:
  timeout_seconds: 15
  retries: 3
  user_agent: "RostekhnadzorAgent/1.0 (+contact@example.com)"
storage:
  kind: json
  path: "state/rostekhnadzor_news.json"
summariser:
  provider: "simple"
  sentences: 3
export:
  markdown:
    enabled: true
    output_dir: "reports"
notifications:
  telegram:
    enabled: false
```

## Technology Stack

- Python 3.12+
- `requests`, `beautifulsoup4`
- Optional: `feedparser`, `schedule`/`APScheduler`, `tenacity`, `rich`

## Operator Experience

- CLI command `python -m rostekhnadzor_agent.cli run --limit 10` for ad-hoc runs.
- `--since YYYY-MM-DD` (future enhancement) to restrict the timeframe.
- Digest stored in `reports/<YYYY-MM-DD>.md` with links to originals.
- Logs contain actionable diagnostics for failed fetch or parse steps.

## Risks and Mitigations

- **Markup drift**: keep HTML fixtures for unit tests, fall back to RSS.
- **Rate limits**: throttle requests, support HTTP caching and proxy rotation.
- **Duplicate content**: content hash plus published timestamp.
- **Legal accuracy**: archive raw article text alongside summaries.
- **Binary attachments**: download on demand and index asynchronously.

## Roadmap Ideas

- Cover additional sections (documents, inspection plans).
- Integrate with a knowledge base (Confluence, Notion, corporate wiki).
- Automatic translation of critical news into English.
- Topic tagging and trend analysis (energy, industrial safety, etc.).
- Minimal web UI for search and status monitoring.
