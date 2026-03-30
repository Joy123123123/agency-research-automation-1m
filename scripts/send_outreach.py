#!/usr/bin/env python3
"""
Outreach Sender Script
Sends automated outreach emails to leads
Usage: python scripts/send_outreach.py --campaign initial --leads tracking/leads.csv
Owner: Md Jamil Islam
"""
import sys
import csv
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.automation.email_sender import EmailSender
from src.automation.follow_up import FollowUpManager
from src.ai.content_generator import ContentGenerator
from config.settings import (
    SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME,
    OPENAI_API_KEY, GOOGLE_API_KEY, EMAIL_DAILY_LIMIT, LOG_LEVEL
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_leads(filepath: str):
    """Load leads from CSV file."""
    leads = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("email") and row.get("status", "new") == "new":
                leads.append(row)
    return leads


def main():
    parser = argparse.ArgumentParser(description="Outreach Sender")
    parser.add_argument("--campaign", default="initial", help="Campaign type: initial, follow_up")
    parser.add_argument("--leads", default="tracking/leads.csv", help="Leads CSV file")
    parser.add_argument("--limit", type=int, default=None, help="Override daily email limit")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    args = parser.parse_args()

    daily_limit = args.limit or EMAIL_DAILY_LIMIT

    # Load leads
    if not Path(args.leads).exists():
        logger.error(f"Leads file not found: {args.leads}")
        return

    leads = load_leads(args.leads)
    logger.info(f"Loaded {len(leads)} new leads from {args.leads}")

    if not leads:
        logger.info("No new leads to contact. Exiting.")
        return

    # Initialize components
    sender = EmailSender(SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME)
    generator = ContentGenerator(OPENAI_API_KEY, GOOGLE_API_KEY)
    follow_up = FollowUpManager()

    sent_count = 0
    for lead in leads[:daily_limit]:
        email = lead.get("email", "")
        name = lead.get("name", "Business Owner")
        niche = lead.get("niche", "your business")
        location = lead.get("location", "your area")

        # Generate personalized content
        content = generator.generate_outreach_email(
            business_name=name,
            niche=niche,
            location=location,
            sender_name=SENDGRID_FROM_NAME
        )

        if args.dry_run:
            print(f"\n--- DRY RUN: {email} ---")
            print(f"Subject: {content.get('subject', 'N/A')}")
            print(f"Body preview: {content.get('body', '')[:100]}...")
            sent_count += 1
            continue

        # Send email
        result = sender.send_single(
            to_email=email,
            to_name=name,
            subject=content.get("subject", f"Quick question about {name}"),
            html_content=f"<p>{content.get('body', '').replace('\n', '<br>')}</p>"
        )

        if result.status == "sent":
            # Add to follow-up sequence
            follow_up.enqueue_lead(email, name, lead)
            sent_count += 1

    print(f"\n✅ Outreach complete!")
    print(f"   Emails {'previewed' if args.dry_run else 'sent'}: {sent_count}")
    print(f"   Daily limit: {daily_limit}")


if __name__ == "__main__":
    main()
