"""Command-line entry point for the Rostekhnadzor research agent."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from .agent import RostekhnadzorAgent
from .exporters import MarkdownExporter
from .fetchers import FetcherConfig, RostekhnadzorFetcher
from .notifications import EmailNotifier, EmailSettings
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
    parser.add_argument("--email-to", action="append", help="Recipient email address; can be used multiple times")
    parser.add_argument("--email-from", default=None, help="Sender email address")
    parser.add_argument("--smtp-host", default=None, help="SMTP server host (or SMTP_HOST env var)")
    parser.add_argument("--smtp-port", type=int, default=587, help="SMTP server port")
    parser.add_argument("--smtp-user", default=None, help="SMTP username (or SMTP_USER env var)")
    parser.add_argument("--smtp-password", default=None, help="SMTP password (or SMTP_PASSWORD env var)")
    parser.add_argument("--smtp-timeout", type=int, default=60, help="SMTP connection timeout in seconds")
    parser.add_argument("--no-smtp-tls", action="store_true", help="Disable STARTTLS for SMTP connection")
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

        recipients = args.email_to or []
        if recipients:
            smtp_host = args.smtp_host or os.getenv("SMTP_HOST")
            smtp_user = args.smtp_user or os.getenv("SMTP_USER")
            smtp_password = args.smtp_password or os.getenv("SMTP_PASSWORD")
            email_from = args.email_from or smtp_user or "no-reply@example.com"
            if not smtp_host:
                logging.error("SMTP host is required to send email notifications")
            else:
                try:
                    run_date = datetime.utcnow()
                    renderer = MarkdownExporter(output_dir=args.output_dir)
                    body = renderer.render(result.processed, run_date)
                    subject = f"\u0420\u043e\u0441\u0442\u0435\u0445\u043d\u0430\u0434\u0437\u043e\u0440 \u2014 \u0434\u0430\u0439\u0434\u0436\u0435\u0441\u0442 {run_date.date().isoformat()}"
                    settings = EmailSettings(
                        smtp_host=smtp_host,
                        smtp_port=args.smtp_port,
                        use_tls=not args.no_smtp_tls,
                        username=smtp_user,
                        password=smtp_password,
                        sender=email_from,
                        recipients=recipients,
                        timeout=args.smtp_timeout,
                    )
                    notifier = EmailNotifier(settings)
                    notifier.send(subject, body)
                    logging.info("Email notification sent to %s", ", ".join(recipients))
                except Exception as exc:  # pylint: disable=broad-except
                    logging.error("Failed to send email notification: %s", exc)
                    return 1
        return 0 if not result.errors else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
