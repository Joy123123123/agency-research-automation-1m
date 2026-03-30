"""
Email Outreach Script — Agency Research Automation
Owner: Md Jamil Islam

Automates email outreach campaigns including cold emails,
follow-ups, and sequence management.
"""

import csv
import logging
import argparse
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/email_outreach.log", mode="a") if os.path.exists("logs") else logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# EMAIL TEMPLATES
# ─────────────────────────────────────────────

EMAIL_TEMPLATES = {
    "cold_intro": {
        "subject": "Quick question about {company_name}'s research process",
        "body": """Hi {first_name},

I came across {company_name} and noticed you're in the {industry} space — impressive work.

I run an agency that helps companies like yours automate their market research and lead generation, saving 20-40 hours per week while getting better quality data.

Quick question: is manual research or inconsistent leads currently a challenge for your team?

I'd love to share a few ideas specific to {company_name} — would a 15-minute call this week work?

Best,
Md Jamil Islam
Agency Research Automation
""",
    },
    "follow_up_1": {
        "subject": "Re: Quick question about {company_name}'s research process",
        "body": """Hi {first_name},

Just following up on my email from a few days ago.

I put together a quick sample of what a research report for {company_name} might look like — happy to send it over if you're curious.

Would Tuesday or Wednesday work for a 15-minute call?

Best,
Md Jamil Islam
""",
    },
    "follow_up_2": {
        "subject": "Last note — {company_name} research automation",
        "body": """Hi {first_name},

I'll keep this short — I know your inbox is busy.

I have one spot left this month for a new research automation client. Thought of {company_name} because of [specific reason].

If the timing isn't right, no worries at all. But if you'd like to explore how we could save you 20+ hours/week on research, just reply "yes" and I'll send over details.

Either way, best of luck with everything.

Md Jamil Islam
""",
    },
    "proposal_follow_up": {
        "subject": "Following up on the {company_name} proposal",
        "body": """Hi {first_name},

I hope you've had a chance to review the proposal I sent over.

I wanted to check in and see if you have any questions or if there's anything I can clarify. I'm also happy to adjust the scope or pricing to better fit your needs.

I have a few client slots opening up next week — would love to save one for {company_name} if the timing works.

Looking forward to your thoughts!

Best,
Md Jamil Islam
""",
    },
}

# ─────────────────────────────────────────────
# SMTP CONFIGURATION
# ─────────────────────────────────────────────

# Load from environment variables — NEVER hardcode credentials
SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "username": os.getenv("SMTP_USERNAME", ""),
    "password": os.getenv("SMTP_PASSWORD", ""),
    "from_name": os.getenv("FROM_NAME", "Md Jamil Islam"),
    "from_email": os.getenv("FROM_EMAIL", ""),
}


# ─────────────────────────────────────────────
# EMAIL BUILDER
# ─────────────────────────────────────────────


def build_email(template_key: str, recipient: dict) -> tuple[str, str]:
    """Build email subject and body from template and recipient data."""
    template = EMAIL_TEMPLATES.get(template_key)
    if not template:
        raise ValueError(f"Unknown email template: {template_key}")

    # Merge recipient data into template
    first_name = recipient.get("contact_name", "there").split()[0]
    vars_map = {
        "first_name": first_name,
        "company_name": recipient.get("company_name", "your company"),
        "industry": recipient.get("industry", "your industry"),
    }

    subject = template["subject"].format(**vars_map)
    body = template["body"].format(**vars_map)

    return subject, body


def build_mime_message(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
    from_name: str,
    from_email: str,
) -> MIMEMultipart:
    """Construct a MIME email message."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = f"{to_name} <{to_email}>"

    # Plain text version
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # HTML version (basic formatting)
    html_body = body.replace("\n", "<br>")
    html_content = f"<html><body><p>{html_body}</p></body></html>"
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    return msg


# ─────────────────────────────────────────────
# EMAIL SENDING
# ─────────────────────────────────────────────


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
    dry_run: bool = True,
) -> bool:
    """
    Send an email. Use dry_run=True to preview without sending.
    Set dry_run=False to actually send (requires SMTP credentials in .env).
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would send to: {to_name} <{to_email}>")
        logger.info(f"[DRY RUN] Subject: {subject}")
        logger.info(f"[DRY RUN] Body preview: {body[:100]}...")
        return True

    if not SMTP_CONFIG["username"] or not SMTP_CONFIG["password"]:
        logger.error("SMTP credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD in .env")
        return False

    try:
        msg = build_mime_message(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body=body,
            from_name=SMTP_CONFIG["from_name"],
            from_email=SMTP_CONFIG["from_email"] or SMTP_CONFIG["username"],
        )

        with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
            server.sendmail(
                SMTP_CONFIG["username"],
                [to_email],
                msg.as_string(),
            )

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to {to_email}: {e}")
        return False


# ─────────────────────────────────────────────
# CAMPAIGN RUNNER
# ─────────────────────────────────────────────


def run_campaign(
    leads_file: str,
    template_key: str = "cold_intro",
    dry_run: bool = True,
    delay_seconds: int = 30,
    max_sends: int = 50,
) -> dict:
    """
    Run an email campaign from a CSV leads file.

    Args:
        leads_file: Path to CSV file with leads (from lead_generation.py output)
        template_key: Which email template to use
        dry_run: If True, preview emails without sending
        delay_seconds: Wait time between emails (avoid spam filters)
        max_sends: Maximum emails to send in this run

    Returns:
        Campaign results summary dict
    """
    os.makedirs("logs", exist_ok=True)

    if not os.path.exists(leads_file):
        logger.error(f"Leads file not found: {leads_file}")
        return {"error": "Leads file not found"}

    results = {"sent": 0, "failed": 0, "skipped": 0, "total": 0}

    with open(leads_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    logger.info(f"Loaded {len(leads)} leads from {leads_file}")
    logger.info(f"Template: {template_key} | Dry run: {dry_run} | Max sends: {max_sends}")

    for i, lead in enumerate(leads):
        if results["sent"] >= max_sends:
            logger.info(f"Reached max sends limit ({max_sends})")
            break

        results["total"] += 1
        email = lead.get("contact_email", "").strip()

        if not email or "@" not in email:
            logger.warning(f"Skipping {lead.get('company_name', 'unknown')} — no valid email")
            results["skipped"] += 1
            continue

        try:
            subject, body = build_email(template_key, lead)
            success = send_email(
                to_email=email,
                to_name=lead.get("contact_name", ""),
                subject=subject,
                body=body,
                dry_run=dry_run,
            )

            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1

            # Delay between sends to avoid spam filters
            if not dry_run and i < len(leads) - 1:
                time.sleep(delay_seconds)

        except Exception as e:
            logger.error(f"Error processing {email}: {e}")
            results["failed"] += 1

    logger.info(
        f"Campaign complete — Sent: {results['sent']}, "
        f"Failed: {results['failed']}, "
        f"Skipped: {results['skipped']}"
    )

    return results


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Agency Research Automation — Email Outreach")
    parser.add_argument("--leads", default="output/leads.csv", help="Path to leads CSV file")
    parser.add_argument(
        "--template",
        default="cold_intro",
        choices=list(EMAIL_TEMPLATES.keys()),
        help="Email template to use",
    )
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview emails without sending")
    parser.add_argument("--send", action="store_true", help="Actually send emails (requires .env credentials)")
    parser.add_argument("--max", type=int, default=50, help="Maximum emails to send")
    parser.add_argument("--delay", type=int, default=30, help="Delay in seconds between emails")
    args = parser.parse_args()

    dry_run = not args.send

    if not dry_run:
        confirm = input("⚠️  You are about to send real emails. Type 'YES' to confirm: ")
        if confirm != "YES":
            print("Cancelled.")
            return

    results = run_campaign(
        leads_file=args.leads,
        template_key=args.template,
        dry_run=dry_run,
        delay_seconds=args.delay,
        max_sends=args.max,
    )

    print(f"\n✅ Campaign complete!")
    print(f"   Sent: {results.get('sent', 0)}")
    print(f"   Failed: {results.get('failed', 0)}")
    print(f"   Skipped: {results.get('skipped', 0)}")

    if dry_run:
        print(f"\n💡 This was a DRY RUN — no emails were actually sent.")
        print(f"   To send for real, run with --send flag (requires SMTP credentials in .env)")


if __name__ == "__main__":
    main()
