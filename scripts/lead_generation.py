"""
Lead Generation Script
Creator: Md Jamil Islam
Purpose: Automate finding marketing agency leads
"""

import csv
import time
import random
from datetime import datetime


SEARCH_KEYWORDS = [
    "marketing agency",
    "digital marketing agency",
    "social media agency",
    "SEO agency",
    "content marketing agency",
]

TARGET_COUNTRIES = ["US", "UK", "CA", "AU"]


def generate_sample_leads(count: int = 50) -> list[dict]:
    """Generate sample lead data for demonstration."""
    agencies = [
        "Bright Digital Agency",
        "Peak Marketing Group",
        "Nexus Media Solutions",
        "Apex Growth Agency",
        "Vantage Digital",
        "Clarity Marketing",
        "Momentum Agency",
        "Elevate Media Group",
        "Catalyst Digital",
        "Pinnacle Marketing",
    ]
    domains = ["com", "co", "io", "agency"]
    countries = ["US", "UK", "CA", "AU"]

    leads = []
    for i in range(count):
        name = random.choice(agencies) + f" {i+1}"
        slug = name.lower().replace(" ", "").replace("-", "")[:20]
        domain = random.choice(domains)
        country = random.choice(countries)
        leads.append(
            {
                "company_name": name,
                "website": f"https://www.{slug}.{domain}",
                "email": f"contact@{slug}.{domain}",
                "country": country,
                "employees": random.randint(3, 50),
                "status": "new",
                "date_added": datetime.today().strftime("%Y-%m-%d"),
            }
        )
    return leads


def save_leads_to_csv(leads: list[dict], filename: str = "tracking/client_tracker.csv") -> None:
    """Save leads to CSV file."""
    if not leads:
        print("No leads to save.")
        return

    fieldnames = list(leads[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)
    print(f"Saved {len(leads)} leads to {filename}")


def filter_leads_by_country(leads: list[dict], country: str) -> list[dict]:
    """Filter leads by country code."""
    return [lead for lead in leads if lead.get("country") == country]


def main():
    print("=== Lead Generation Script ===")
    print(f"Creator: Md Jamil Islam")
    print(f"Date: {datetime.today().strftime('%Y-%m-%d')}")
    print()

    print("Generating sample leads...")
    leads = generate_sample_leads(count=50)
    print(f"Generated {len(leads)} leads")

    # Show breakdown by country
    for country in TARGET_COUNTRIES:
        filtered = filter_leads_by_country(leads, country)
        print(f"  {country}: {len(filtered)} leads")

    # Save to CSV
    save_leads_to_csv(leads)
    print("\nDone! Check tracking/client_tracker.csv for your leads.")


if __name__ == "__main__":
    main()
