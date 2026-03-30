"""
Email Sender Module
Sends automated outreach emails via SendGrid
Owner: Md Jamil Islam
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, Personalization

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    recipient_email: str
    recipient_name: str
    status: str  # "sent", "failed", "bounced"
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailSender:
    """
    Sends personalized outreach emails using SendGrid.
    Handles rate limiting, bounce tracking, and analytics.
    """

    def __init__(self, api_key: str, from_email: str, from_name: str):
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name
        self.client = SendGridAPIClient(api_key) if api_key else None

    def send_single(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str = ""
    ) -> EmailResult:
        """Send a single email."""
        if not self.client:
            logger.warning("SendGrid not configured. Email not sent.")
            return EmailResult(
                recipient_email=to_email,
                recipient_name=to_name,
                status="failed",
                error="SendGrid API key not configured"
            )

        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=text_content or self._html_to_text(html_content),
        )

        try:
            response = self.client.send(message)
            if response.status_code in (200, 201, 202):
                logger.info(f"Email sent to {to_email} (status: {response.status_code})")
                return EmailResult(
                    recipient_email=to_email,
                    recipient_name=to_name,
                    status="sent",
                    message_id=response.headers.get("X-Message-Id"),
                )
            else:
                logger.error(f"SendGrid returned {response.status_code} for {to_email}")
                return EmailResult(
                    recipient_email=to_email,
                    recipient_name=to_name,
                    status="failed",
                    error=f"HTTP {response.status_code}"
                )
        except Exception as e:
            logger.error(f"Email send failed for {to_email}: {e}")
            return EmailResult(
                recipient_email=to_email,
                recipient_name=to_name,
                status="failed",
                error=str(e)
            )

    def send_bulk(
        self,
        leads: List[Dict],
        subject_template: str,
        html_template: str,
        daily_limit: int = 200
    ) -> List[EmailResult]:
        """
        Send bulk personalized emails with daily limit.
        """
        results = []
        sent_count = 0

        for lead in leads:
            if sent_count >= daily_limit:
                logger.info(f"Daily limit of {daily_limit} reached.")
                break

            email = lead.get("email")
            if not email:
                continue

            name = lead.get("name", "Business Owner")
            niche = lead.get("niche", "your business")
            location = lead.get("location", "your area")

            # Personalize templates
            subject = subject_template.format(
                name=name, niche=niche, location=location
            )
            html = html_template.format(
                name=name, niche=niche, location=location,
                sender_name=self.from_name
            )

            result = self.send_single(email, name, subject, html)
            results.append(result)
            sent_count += 1

        sent = sum(1 for r in results if r.status == "sent")
        failed = sum(1 for r in results if r.status == "failed")
        logger.info(f"Bulk send complete: {sent} sent, {failed} failed")
        return results

    def _html_to_text(self, html: str) -> str:
        """Basic HTML to plain text conversion."""
        import re
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text
