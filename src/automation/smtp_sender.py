"""
Pure Python SMTP Email Sender — No external API needed.
Works with Gmail (App Password), Outlook, or any SMTP server.

Setup (one-time, 2 minutes):
  1. Gmail account-এ 2FA চালু করো:
     myaccount.google.com → Security → 2-Step Verification
  2. App Password তৈরি করো:
     myaccount.google.com → Security → App Passwords → Select "Mail"
  3. config/api_keys.env ফাইলে:
     GMAIL_EMAIL=তোমার@gmail.com
     GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx   (16-digit app password)

Owner: Md Jamil Islam
"""
from __future__ import annotations

import logging
import smtplib
import ssl
import time
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SMTPResult:
    recipient_email: str
    status: str          # "sent" | "failed" | "skipped"
    error: Optional[str] = None


class SMTPEmailSender:
    """
    Sends emails via SMTP using Python's built-in smtplib.
    Supports Gmail (recommended), Outlook, Yahoo, or any SMTP server.
    No external libraries or API keys required.
    """

    # SMTP settings for common providers
    PROVIDERS = {
        "gmail": {"host": "smtp.gmail.com", "port": 587},
        "outlook": {"host": "smtp.office365.com", "port": 587},
        "yahoo": {"host": "smtp.mail.yahoo.com", "port": 587},
        "custom": {"host": "", "port": 587},
    }

    def __init__(
        self,
        email: str,
        password: str,
        sender_name: str = "Md Jamil Islam",
        provider: str = "gmail",
        smtp_host: str = "",
        smtp_port: int = 587,
        delay_seconds: float = 2.0,
    ) -> None:
        self.email = email
        self.password = password
        self.sender_name = sender_name
        self.delay = delay_seconds

        if provider in self.PROVIDERS and self.PROVIDERS[provider]["host"]:
            cfg = self.PROVIDERS[provider]
            self.smtp_host = cfg["host"]
            self.smtp_port = cfg["port"]
        else:
            self.smtp_host = smtp_host
            self.smtp_port = smtp_port

        self._configured = bool(email and password and self.smtp_host)

    def is_configured(self) -> bool:
        return self._configured

    def send_single(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str = "",
    ) -> SMTPResult:
        """Send a single email. Returns SMTPResult with status."""
        if not self._configured:
            logger.warning("SMTP not configured — email not sent to %s", to_email)
            return SMTPResult(
                recipient_email=to_email,
                status="skipped",
                error="SMTP credentials not configured. Add GMAIL_EMAIL + GMAIL_APP_PASSWORD to api_keys.env",
            )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.sender_name} <{self.email}>"
        msg["To"] = f"{to_name} <{to_email}>"
        msg["Reply-To"] = self.email

        plain = text_body or _html_to_plain(html_body)
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(self.email, self.password)
                server.sendmail(self.email, to_email, msg.as_string())
            logger.info("Email sent → %s", to_email)
            return SMTPResult(recipient_email=to_email, status="sent")
        except smtplib.SMTPAuthenticationError:
            err = (
                "Gmail authentication failed. "
                "Make sure you're using an App Password (not your Gmail password). "
                "Get one at: myaccount.google.com → Security → App Passwords"
            )
            logger.error(err)
            return SMTPResult(recipient_email=to_email, status="failed", error=err)
        except smtplib.SMTPRecipientsRefused:
            err = f"Recipient refused: {to_email}"
            logger.warning(err)
            return SMTPResult(recipient_email=to_email, status="failed", error=err)
        except Exception as exc:
            logger.error("SMTP error sending to %s: %s", to_email, exc)
            return SMTPResult(recipient_email=to_email, status="failed", error=str(exc))

    def send_bulk(
        self,
        leads: List[dict],
        subject_fn,
        html_fn,
        daily_limit: int = 100,
    ) -> List[SMTPResult]:
        """
        Send bulk personalized emails with per-email delay to avoid spam filters.

        Args:
            leads: list of lead dicts (must have 'email', 'name')
            subject_fn: callable(lead) → subject string
            html_fn: callable(lead) → HTML body string
            daily_limit: max emails to send in this batch
        """
        results: List[SMTPResult] = []
        sent = 0

        for lead in leads:
            if sent >= daily_limit:
                logger.info("Daily limit of %d reached.", daily_limit)
                break

            email = (lead.get("email") or "").strip()
            if not email or "@" not in email:
                continue

            name = lead.get("name", "Business Owner")
            subject = subject_fn(lead)
            html = html_fn(lead)

            result = self.send_single(email, name, subject, html)
            results.append(result)

            if result.status == "sent":
                sent += 1
                time.sleep(self.delay)  # Avoid spam flags
            elif result.status == "skipped":
                # SMTP not configured — log once and return early
                results.extend([
                    SMTPResult(recipient_email=l.get("email", ""), status="skipped")
                    for l in leads[leads.index(lead) + 1:]
                    if l.get("email")
                ])
                break

        ok = sum(1 for r in results if r.status == "sent")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        logger.info("Bulk SMTP send: %d sent, %d failed, %d skipped", ok, failed, skipped)
        return results

    def verify_connection(self) -> tuple[bool, str]:
        """
        Test SMTP connection without sending email.
        Returns (success, message).
        """
        if not self._configured:
            return False, "SMTP credentials not configured."
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(self.email, self.password)
            return True, f"✅ Connected to {self.smtp_host} as {self.email}"
        except smtplib.SMTPAuthenticationError:
            return False, (
                "❌ Authentication failed. Use Gmail App Password, not your Gmail password.\n"
                "Get it at: myaccount.google.com → Security → App Passwords"
            )
        except Exception as exc:
            return False, f"❌ Connection error: {exc}"


def _html_to_plain(html: str) -> str:
    """Strip HTML tags to produce a plain-text fallback."""
    import re
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
