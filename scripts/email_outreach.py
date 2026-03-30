"""
Email Outreach Script
Creator: Md Jamil Islam
Purpose: Automate email outreach to marketing agencies
"""

import csv
import os
from datetime import datetime, timedelta


EMAIL_TEMPLATES = {
    "cold_outreach": """Subject: Save 15+ Hours/Week on Research - {agency_name}

Hi {first_name},

I noticed {agency_name} is doing great work in the {niche} space.

Quick question: How much time does your team spend on research, competitor analysis, and reporting each week?

Most agencies tell me it's 15-20 hours — time that could go toward client strategy and growth.

I help agencies like yours automate that work completely, delivering:
- Weekly competitor research reports
- Automated lead data enrichment
- Client-ready performance dashboards

I've helped agencies save 15+ hours/week while improving report quality.

Would you be open to a 15-minute call this week to see if it's a fit?

Best,
Md Jamil Islam
Agency Research Automation
""",
    "follow_up_day2": """Subject: Re: Save 15+ Hours/Week on Research - {agency_name}

Hi {first_name},

Just following up on my email from a couple days ago.

I know your inbox is busy, so I'll keep this short:

I help marketing agencies automate research and reporting, saving 15+ hours/week.

Would Tuesday or Thursday work for a quick 15-minute call?

Best,
Md Jamil Islam
""",
    "follow_up_day5": """Subject: Last follow-up - Research Automation for {agency_name}

Hi {first_name},

I don't want to keep bothering you, so this will be my last email.

If saving 15+ hours/week on research isn't a priority right now, no problem at all.

But if things change, you can always reach out at Riyadkhan00117@gmail.com.

Either way, I wish you and {agency_name} all the best!

Md Jamil Islam
""",
}


def load_leads(filename: str = "tracking/client_tracker.csv") -> list[dict]:
    """Load leads from CSV file."""
    if not os.path.exists(filename):
        print(f"File not found: {filename}. Run lead_generation.py first.")
        return []

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def personalize_email(template: str, lead: dict) -> str:
    """Personalize an email template with lead data."""
    company = lead.get("company_name", "Your Agency")
    first_name = company.split()[0]
    niche = "digital marketing"

    return template.format(
        agency_name=company,
        first_name=first_name,
        niche=niche,
    )


def generate_outreach_schedule(leads: list[dict]) -> list[dict]:
    """Generate a full outreach schedule with follow-ups."""
    schedule = []
    today = datetime.today()

    for lead in leads:
        company = lead.get("company_name", "Unknown")
        email = lead.get("email", "")

        if not email:
            continue

        schedule.append(
            {
                "date": today.strftime("%Y-%m-%d"),
                "company": company,
                "email": email,
                "type": "cold_outreach",
                "status": "pending",
            }
        )
        schedule.append(
            {
                "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "company": company,
                "email": email,
                "type": "follow_up_day2",
                "status": "pending",
            }
        )
        schedule.append(
            {
                "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
                "company": company,
                "email": email,
                "type": "follow_up_day5",
                "status": "pending",
            }
        )

    return schedule


def save_outreach_schedule(schedule: list[dict], filename: str = "tracking/outreach_schedule.csv") -> None:
    """Save outreach schedule to CSV."""
    if not schedule:
        print("No schedule to save.")
        return

    fieldnames = list(schedule[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(schedule)
    print(f"Saved {len(schedule)} email tasks to {filename}")


def preview_email(lead: dict, template_key: str = "cold_outreach") -> None:
    """Print a preview of a personalized email."""
    template = EMAIL_TEMPLATES[template_key]
    personalized = personalize_email(template, lead)
    print("=" * 60)
    print(f"EMAIL PREVIEW for: {lead.get('company_name')}")
    print("=" * 60)
    print(personalized)
    print("=" * 60)


def main():
    print("=== Email Outreach Script ===")
    print(f"Creator: Md Jamil Islam")
    print(f"Date: {datetime.today().strftime('%Y-%m-%d')}")
    print()

    leads = load_leads()
    if not leads:
        print("No leads found. Run scripts/lead_generation.py first.")
        return

    print(f"Loaded {len(leads)} leads.")

    # Preview first email
    if leads:
        preview_email(leads[0], "cold_outreach")

    # Generate full schedule
    schedule = generate_outreach_schedule(leads[:10])  # first 10 leads
    save_outreach_schedule(schedule)

    print(f"\nOutreach schedule generated for {len(leads[:10])} leads.")
    print("Check tracking/outreach_schedule.csv for your email schedule.")


if __name__ == "__main__":
    main()
