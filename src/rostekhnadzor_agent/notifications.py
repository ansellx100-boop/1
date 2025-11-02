"""Notification helpers for the Rostekhnadzor agent."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import List


@dataclass(slots=True)
class EmailSettings:
    smtp_host: str
    smtp_port: int = 587
    use_tls: bool = True
    username: str | None = None
    password: str | None = None
    sender: str = "no-reply@example.com"
    recipients: List[str] = None  # type: ignore[assignment]
    timeout: int = 60

    def __post_init__(self) -> None:
        if self.recipients is None:
            self.recipients = []


class EmailNotifier:
    def __init__(self, settings: EmailSettings) -> None:
        if not settings.recipients:
            raise ValueError("Email recipients list must not be empty")
        self.settings = settings

    def send(self, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.sender
        message["To"] = ", ".join(self.settings.recipients)
        message.set_content(body)

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=self.settings.timeout) as smtp:
            if self.settings.use_tls:
                smtp.starttls()
            if self.settings.username:
                smtp.login(self.settings.username, self.settings.password or "")
            smtp.send_message(message)
