"""
Email Outreach Script
Sends personalized cold outreach emails to prospects.

Usage:
    python email_outreach.py --template cold_outreach --leads 20
    python email_outreach.py --template follow_up --leads-file ../tracking/client_tracker.csv
    python email_outreach.py --dry-run --template cold_outreach --leads 5
"""

import argparse
import csv
import os
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_NAME = os.getenv("FROM_NAME", "Your Name")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

LEADS_FILE = os.path.join(os.path.dirname(__file__), "../tracking/client_tracker.csv")
METRICS_FILE = os.path.join(os.path.dirname(__file__), "../tracking/metrics_tracker.csv")

# Delay between emails (seconds) to avoid spam filters
EMAIL_DELAY = float(os.getenv("EMAIL_DELAY", "60"))

# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, dict[str, str]] = {
    "cold_outreach": {
        "subject": "Quick question about {company_name}'s research process",
        "body": """Hi {contact_name},

I came across {company_name} and was impressed by your work in {industry}.

Quick question: how much time does your team currently spend on research and reporting each week?

Most agencies I speak with spend 15-20 hours/week on manual research — time that could go toward strategy and client work.

I run a Done-For-You research automation service specifically for marketing agencies. We handle:
✓ Competitor analysis
✓ Lead research (50-100 leads with full contact data)
✓ Industry trend reports
✓ Content research briefs

All delivered within 48 hours, on a monthly retainer.

I'd love to send you a sample report for {company_name} — completely free, no strings attached.

Would that be valuable? Just reply "yes" and I'll put it together.

Best,
{from_name}

P.S. Happy to hop on a quick 15-min call if you prefer — just let me know.
""",
    },
    "follow_up": {
        "subject": "Re: Quick question about {company_name}'s research process",
        "body": """Hi {contact_name},

Just circling back on my email from a few days ago.

I know your inbox is busy, so I'll be direct: I help marketing agencies save 15+ hours/week by automating their research and reporting.

Here's what one recent client said:
"We went from spending 20 hours/week on research to under 2 hours — and the quality is better than what we were doing manually."

I've put together a sample competitor analysis for {company_name} — want me to send it over?

Takes 30 seconds to reply — just say "send it" and it's yours.

Best,
{from_name}
""",
    },
    "value_add": {
        "subject": "Free resource for {company_name}",
        "body": """Hi {contact_name},

I put together a quick analysis of {company_name}'s top 3 competitors — thought it might be useful.

[ATTACH SAMPLE REPORT]

No pitch here, just thought it might give you some ideas.

If you're curious how I put this together in under 2 hours (fully automated), happy to share.

Best,
{from_name}
""",
    },
    "breakup": {
        "subject": "Closing the loop on {company_name}",
        "body": """Hi {contact_name},

I've reached out a few times about research automation for {company_name} — haven't heard back, so I'll assume the timing isn't right.

I'll stop reaching out, but if you ever want to explore how agencies are saving 15+ hours/week on research, you can reach me at {from_email}.

Best of luck with everything!

{from_name}
""",
    },
}


# ---------------------------------------------------------------------------
# Lead loading
# ---------------------------------------------------------------------------

def load_leads(leads_file: str, limit: int, status_filter: str = "new") -> list[dict]:
    """Load leads from CSV, filtering by status and limiting count."""
    leads = []
    if not os.path.isfile(leads_file):
        print(f"[WARNING] Leads file not found: {leads_file}")
        return leads

    with open(leads_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") == status_filter and row.get("email"):
                leads.append(row)
                if len(leads) >= limit:
                    break

    return leads


# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

def build_email(lead: dict, template_name: str) -> tuple[str, str]:
    """Build subject and body from a template and lead data."""
    template = TEMPLATES[template_name]
    context = {
        "contact_name": lead.get("contact_name", "there").split()[0],
        "company_name": lead.get("company_name", "your agency"),
        "industry": lead.get("industry", "marketing"),
        "from_name": FROM_NAME,
        "from_email": FROM_EMAIL,
    }
    subject = template["subject"].format(**context)
    body = template["body"].format(**context)
    return subject, body


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
    dry_run: bool = False,
) -> bool:
    """Send a single email via SMTP."""
    if dry_run:
        print(f"  [DRY RUN] Would send to: {to_name} <{to_email}>")
        print(f"  Subject: {subject}")
        return True

    if not SMTP_USER or not SMTP_PASSWORD:
        print("[ERROR] SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = f"{to_name} <{to_email}>"

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())

        return True
    except smtplib.SMTPException as exc:
        print(f"  [ERROR] Failed to send to {to_email}: {exc}")
        return False


# ---------------------------------------------------------------------------
# Status tracking
# ---------------------------------------------------------------------------

def update_lead_status(leads_file: str, lead_id: str, new_status: str) -> None:
    """Update the status of a lead in the CSV file."""
    if not os.path.isfile(leads_file):
        return

    rows = []
    with open(leads_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            if row.get("id") == lead_id:
                row["status"] = new_status
            rows.append(row)

    with open(leads_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def log_metric(template: str, sent: int, failed: int) -> None:
    """Append a metrics row to the metrics tracker CSV."""
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    file_exists = os.path.isfile(METRICS_FILE)

    with open(METRICS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "campaign", "emails_sent", "emails_failed"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d"), template, sent, failed])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Send personalized outreach emails")
    parser.add_argument(
        "--template",
        choices=list(TEMPLATES.keys()),
        default="cold_outreach",
        help="Email template to use",
    )
    parser.add_argument("--leads", type=int, default=20, help="Number of leads to email")
    parser.add_argument("--leads-file", default=LEADS_FILE, help="Path to client_tracker CSV")
    parser.add_argument("--dry-run", action="store_true", help="Print emails without sending")
    parser.add_argument("--delay", type=float, default=EMAIL_DELAY, help="Seconds between emails")
    args = parser.parse_args()

    leads = load_leads(args.leads_file, args.leads)
    if not leads:
        print(f"[INFO] No new leads found in {args.leads_file}")
        return

    print(f"[INFO] Sending '{args.template}' emails to {len(leads)} leads...")
    if args.dry_run:
        print("[INFO] DRY RUN MODE - no emails will be sent")

    sent = 0
    failed = 0

    for lead in leads:
        subject, body = build_email(lead, args.template)
        success = send_email(
            to_email=lead["email"],
            to_name=lead.get("contact_name", ""),
            subject=subject,
            body=body,
            dry_run=args.dry_run,
        )

        if success:
            sent += 1
            if not args.dry_run:
                update_lead_status(args.leads_file, lead["id"], "contacted")
            print(f"  [OK] {lead.get('company_name')} ({lead['email']})")
        else:
            failed += 1

        if not args.dry_run and lead != leads[-1]:
            print(f"  [INFO] Waiting {args.delay}s before next email...")
            time.sleep(args.delay)

    if not args.dry_run:
        log_metric(args.template, sent, failed)

    print(f"[DONE] Sent: {sent} | Failed: {failed}")


if __name__ == "__main__":
    main()
