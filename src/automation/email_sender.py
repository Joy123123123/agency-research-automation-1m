"""
Email Sender Module
Sends automated outreach emails.
Priority: SendGrid API (if key set) → Gmail SMTP (if credentials set) → dry-run log.
Owner: Md Jamil Islam
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    recipient_email: str
    recipient_name: str
    status: str          # "sent", "failed", "bounced", "skipped"
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailSender:
    """
    Sends personalised outreach emails.
    Automatically selects the best available backend:
      1. SendGrid (if SENDGRID_API_KEY is set)
      2. Gmail SMTP (if GMAIL_EMAIL + GMAIL_APP_PASSWORD are set)
      3. Dry-run / log-only (no credentials — prints preview, marks as "skipped")
    """

    def __init__(
        self,
        sendgrid_api_key: str = "",
        from_email: str = "",
        from_name: str = "Md Jamil Islam",
        gmail_email: str = "",
        gmail_app_password: str = "",
    ) -> None:
        self.from_email = from_email or gmail_email
        self.from_name = from_name

        # Try SendGrid first
        self._sendgrid_client = None
        if sendgrid_api_key:
            try:
                from sendgrid import SendGridAPIClient
                self._sendgrid_client = SendGridAPIClient(sendgrid_api_key)
                logger.info("EmailSender: using SendGrid backend")
            except ImportError:
                logger.warning("sendgrid package not installed; falling back to SMTP.")

        # Fall back to Gmail SMTP
        self._smtp_sender = None
        if not self._sendgrid_client:
            from src.automation.smtp_sender import SMTPEmailSender
            smtp = SMTPEmailSender(
                email=gmail_email,
                password=gmail_app_password,
                sender_name=from_name,
            )
            if smtp.is_configured():
                self._smtp_sender = smtp
                logger.info("EmailSender: using Gmail SMTP backend (%s)", gmail_email)
            else:
                logger.warning(
                    "EmailSender: no credentials configured. "
                    "Set SENDGRID_API_KEY or GMAIL_EMAIL+GMAIL_APP_PASSWORD in config/api_keys.env"
                )

    @property
    def _backend(self) -> str:
        if self._sendgrid_client:
            return "sendgrid"
        if self._smtp_sender:
            return "smtp"
        return "none"

    def is_configured(self) -> bool:
        return self._backend != "none"

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def send_single(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str = "",
    ) -> EmailResult:
        """Send a single email using the best available backend."""
        if self._backend == "sendgrid":
            return self._send_sendgrid(to_email, to_name, subject, html_content, text_content)
        if self._backend == "smtp":
            assert self._smtp_sender is not None, "smtp_sender must be set when backend is 'smtp'"
            from src.automation.smtp_sender import SMTPResult
            r: SMTPResult = self._smtp_sender.send_single(
                to_email, to_name, subject, html_content, text_content
            )
            return EmailResult(
                recipient_email=r.recipient_email,
                recipient_name=to_name,
                status=r.status,
                error=r.error,
            )
        # No backend — log and skip
        logger.warning("No email backend configured — skipping email to %s", to_email)
        return EmailResult(
            recipient_email=to_email,
            recipient_name=to_name,
            status="skipped",
            error=(
                "No email credentials. Add GMAIL_EMAIL + GMAIL_APP_PASSWORD "
                "to config/api_keys.env for free email sending."
            ),
        )

    def send_bulk(
        self,
        leads: List[Dict],
        subject_template: str,
        html_template: str,
        daily_limit: int = 100,
    ) -> List[EmailResult]:
        """Send bulk personalised emails with daily limit."""
        results: List[EmailResult] = []
        sent_count = 0

        for lead in leads:
            if sent_count >= daily_limit:
                logger.info("Daily limit of %d reached.", daily_limit)
                break

            email = lead.get("email", "").strip()
            if not email:
                continue

            name = lead.get("name", "Business Owner")
            niche = lead.get("niche", "your business")
            location = lead.get("location", "your area")

            subject = subject_template.format(name=name, niche=niche, location=location)
            html = html_template.format(
                name=name, niche=niche, location=location, sender_name=self.from_name
            )

            result = self.send_single(email, name, subject, html)
            results.append(result)
            if result.status == "sent":
                sent_count += 1

        sent = sum(1 for r in results if r.status == "sent")
        failed = sum(1 for r in results if r.status == "failed")
        logger.info("Bulk send complete: %d sent, %d failed", sent, failed)
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _send_sendgrid(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> EmailResult:
        """Send via SendGrid API."""
        assert self._sendgrid_client is not None, "sendgrid_client must be set when backend is 'sendgrid'"
        from sendgrid.helpers.mail import Mail
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=text_content or _html_to_text(html_content),
        )
        try:
            response = self._sendgrid_client.send(message)
            if response.status_code in (200, 201, 202):
                return EmailResult(
                    recipient_email=to_email,
                    recipient_name=to_name,
                    status="sent",
                    message_id=response.headers.get("X-Message-Id"),
                )
            return EmailResult(
                recipient_email=to_email,
                recipient_name=to_name,
                status="failed",
                error=f"HTTP {response.status_code}",
            )
        except Exception as exc:
            logger.error("SendGrid error for %s: %s", to_email, exc)
            return EmailResult(
                recipient_email=to_email,
                recipient_name=to_name,
                status="failed",
                error=str(exc),
            )


def _html_to_text(html: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text
