"""Command-line entry point for the Rostekhnadzor research agent."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from .agent import RostekhnadzorAgent
from .exporters import MarkdownExporter
from .fetchers import FetcherConfig, RostekhnadzorFetcher
from .storage import StateStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rostekhnadzor research agent")
    parser.add_argument("command", choices=["run"], help="Command to execute")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of news items to process")
    parser.add_argument("--force", action="store_true", help="Reprocess even known items")
    parser.add_argument("--state-path", default="state/rostekhnadzor_news.json", help="Path to state JSON store")
    parser.add_argument("--base-url", default="https://www.gosnadzor.ru", help="Base URL of the website")
    parser.add_argument("--output-dir", default="reports", help="Directory for markdown reports")
    parser.add_argument("--no-report", action="store_true", help="Do not generate markdown reports")
    parser.add_argument("--log-level", default="INFO", help="Logging level (INFO, DEBUG, WARNING)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )

    if args.command == "run":
        fetcher = RostekhnadzorFetcher(FetcherConfig(base_url=args.base_url))
        store = StateStore(path=args.state_path)
        exporter = None if args.no_report else MarkdownExporter(output_dir=args.output_dir)
        agent = RostekhnadzorAgent(fetcher=fetcher, store=store, exporter=exporter)
        result = agent.run(limit=args.limit, force=args.force)

        logging.info("Processed items: %s", len(result.processed))
        logging.info("Skipped items: %s", result.skipped)
        if result.report_path:
            logging.info("Report saved to %s", result.report_path)
        if result.errors:
            logging.error("Encountered %s errors", len(result.errors))
            for error in result.errors:
                logging.error(error)
        return 0 if not result.errors else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
