#!/usr/bin/env python3
"""
Outreach Sender Script — Sends automated outreach emails to leads.
Works with: SendGrid API OR Gmail SMTP (free) OR dry-run (no credentials needed).

Usage:
  python scripts/send_outreach.py --campaign initial    # send emails
  python scripts/send_outreach.py --dry-run             # preview without sending
  python scripts/send_outreach.py --campaign follow_up  # send follow-ups

Owner: Md Jamil Islam
"""
import sys
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.automation.email_sender import EmailSender
from src.automation.follow_up import FollowUpManager
from src.ai.content_generator import ContentGenerator
from config.settings import (
    SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME,
    OPENAI_API_KEY, GOOGLE_API_KEY, EMAIL_DAILY_LIMIT, LOG_LEVEL,
    GMAIL_EMAIL, GMAIL_APP_PASSWORD, GMAIL_SENDER_NAME,
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_leads(filepath: str) -> list[dict]:
    """Load new leads with email addresses from CSV."""
    leads = []
    try:
        with open(filepath, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("email") and row.get("status", "new") == "new":
                    leads.append(row)
    except FileNotFoundError:
        logger.error("Leads file not found: %s", filepath)
    return leads


def main() -> None:
    parser = argparse.ArgumentParser(description="Outreach Sender")
    parser.add_argument("--campaign", default="initial",
                        help="Campaign type: initial, follow_up")
    parser.add_argument("--leads", default="tracking/leads.csv",
                        help="Leads CSV file")
    parser.add_argument("--limit", type=int, default=None,
                        help="Override daily email limit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview emails without sending")
    args = parser.parse_args()

    daily_limit = args.limit or EMAIL_DAILY_LIMIT

    # ── Determine email backend ───────────────────────────────────────────────
    sender = EmailSender(
        sendgrid_api_key=SENDGRID_API_KEY,
        from_email=SENDGRID_FROM_EMAIL or GMAIL_EMAIL,
        from_name=SENDGRID_FROM_NAME or GMAIL_SENDER_NAME,
        gmail_email=GMAIL_EMAIL,
        gmail_app_password=GMAIL_APP_PASSWORD,
    )

    if args.dry_run:
        backend_label = "DRY RUN (preview only)"
    elif sender.is_configured():
        backend_label = f"Sending via {sender._backend.upper()}"
    else:
        backend_label = "⚠️  No email credentials — showing preview only"

    print(f"\n📧 Outreach: {backend_label}")
    print(f"   Campaign : {args.campaign}")
    print(f"   Leads    : {args.leads}")
    print(f"   Limit    : {daily_limit}/day\n")

    # ── Load leads ────────────────────────────────────────────────────────────
    leads = load_leads(args.leads)
    logger.info("Loaded %d new leads with email from %s", len(leads), args.leads)

    if not leads:
        print("ℹ️  No new leads with email addresses found.")
        print("   Run research first: python scripts/run_research.py")
        return

    # ── Content generator ─────────────────────────────────────────────────────
    generator = ContentGenerator(OPENAI_API_KEY, GOOGLE_API_KEY)
    follow_up = FollowUpManager()

    sent_count = 0
    for lead in leads[:daily_limit]:
        email = lead.get("email", "").strip()
        name = lead.get("name", "Business Owner")
        niche = lead.get("niche", "your business")
        location = lead.get("location", "your area")

        content = generator.generate_outreach_email(
            business_name=name,
            niche=niche,
            location=location,
            sender_name=SENDGRID_FROM_NAME or GMAIL_SENDER_NAME,
        )

        subject = content.get("subject", f"Quick question about {name}'s online presence")
        body = content.get("body", "")
        html_body = f"<p>{body.replace(chr(10), '<br>')}</p>"

        if args.dry_run:
            print(f"  📬 To: {email}")
            print(f"     Subject: {subject}")
            print(f"     Body: {body[:120]}...")
            print()
            sent_count += 1
            continue

        result = sender.send_single(email, name, subject, html_body)

        if result.status == "sent":
            follow_up.enqueue_lead(email, name, lead)
            sent_count += 1
            print(f"  ✅ Sent → {email}")
        elif result.status == "skipped":
            # No credentials — show preview
            print(f"  📬 Preview → {email}: {subject}")
            print(f"     {body[:100]}...")
            sent_count += 1
        else:
            print(f"  ❌ Failed → {email}: {result.error}")

    print(f"\n✅ Done! Emails {'previewed' if args.dry_run else 'processed'}: {sent_count}")
    if not sender.is_configured() and not args.dry_run:
        print("\n💡 To send real emails (FREE):")
        print("   1. config/api_keys.env এ যোগ করো:")
        print("      GMAIL_EMAIL=তোমার@gmail.com")
        print("      GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        print("   2. App Password পাবে: myaccount.google.com → Security → App Passwords")


if __name__ == "__main__":
    main()
