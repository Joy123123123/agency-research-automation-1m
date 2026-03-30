"""
Lead Generation Script — Agency Research Automation
Owner: Md Jamil Islam

Automates the process of finding and qualifying potential clients
from multiple sources including web scraping and API integration.
"""

import csv
import json
import time
import logging
import argparse
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/lead_generation.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

DEFAULT_CONFIG = {
    "output_file": "output/leads.csv",
    "max_leads": 100,
    "niches": [
        "digital marketing agency",
        "SaaS company",
        "e-commerce brand",
        "consulting firm",
        "recruiting agency",
    ],
    "target_employee_range": (5, 200),
    "target_regions": ["United States", "United Kingdom", "Canada", "Australia"],
}

OUTPUT_FIELDS = [
    "company_name",
    "website",
    "industry",
    "employee_count",
    "location",
    "contact_name",
    "contact_title",
    "contact_email",
    "linkedin_url",
    "phone",
    "score",
    "source",
    "date_added",
]


# ─────────────────────────────────────────────
# LEAD SCORING
# ─────────────────────────────────────────────


def score_lead(lead: dict) -> int:
    """Score a lead from 0–100 based on fit criteria."""
    score = 0

    # Has verified email → +30
    if lead.get("contact_email") and "@" in lead["contact_email"]:
        score += 30

    # Employee count in target range → +20
    emp = lead.get("employee_count", 0)
    if isinstance(emp, (int, float)) and 5 <= emp <= 200:
        score += 20

    # Has LinkedIn URL → +15
    if lead.get("linkedin_url"):
        score += 15

    # Has phone number → +10
    if lead.get("phone"):
        score += 10

    # Has website → +10
    if lead.get("website"):
        score += 10

    # Decision-maker title → +15
    title = (lead.get("contact_title") or "").lower()
    if any(t in title for t in ["ceo", "founder", "owner", "director", "head of", "vp", "president"]):
        score += 15

    return min(score, 100)


# ─────────────────────────────────────────────
# SAMPLE DATA GENERATOR (replace with real API)
# ─────────────────────────────────────────────


def generate_sample_leads(count: int = 10) -> list[dict]:
    """
    Generate sample lead data for demonstration.
    In production, replace this with Apollo.io API, Hunter.io API,
    or web scraping logic.
    """
    sample_leads = [
        {
            "company_name": "Bright Digital Agency",
            "website": "https://brightdigital.com",
            "industry": "Digital Marketing",
            "employee_count": 25,
            "location": "New York, USA",
            "contact_name": "Sarah Johnson",
            "contact_title": "CEO",
            "contact_email": "sarah@brightdigital.com",
            "linkedin_url": "https://linkedin.com/in/sarahjohnson",
            "phone": "+1-555-0101",
        },
        {
            "company_name": "CloudFlow SaaS",
            "website": "https://cloudflow.io",
            "industry": "SaaS",
            "employee_count": 50,
            "location": "San Francisco, USA",
            "contact_name": "Mark Chen",
            "contact_title": "Founder",
            "contact_email": "mark@cloudflow.io",
            "linkedin_url": "https://linkedin.com/in/markchen",
            "phone": "+1-555-0202",
        },
        {
            "company_name": "NexaTrade E-commerce",
            "website": "https://nexatrade.com",
            "industry": "E-commerce",
            "employee_count": 15,
            "location": "London, UK",
            "contact_name": "Emily Williams",
            "contact_title": "Head of Growth",
            "contact_email": "emily@nexatrade.com",
            "linkedin_url": "https://linkedin.com/in/emilywilliams",
            "phone": "+44-20-7946-0958",
        },
    ]
    return sample_leads[:count]


# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────


def export_to_csv(leads: list[dict], output_file: str) -> None:
    """Export leads list to a CSV file."""
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)

    logger.info(f"Exported {len(leads)} leads to {output_file}")


def export_to_json(leads: list[dict], output_file: str) -> None:
    """Export leads list to a JSON file."""
    json_file = output_file.replace(".csv", ".json")
    os.makedirs(os.path.dirname(json_file) if os.path.dirname(json_file) else ".", exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    logger.info(f"Exported {len(leads)} leads to {json_file}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────


def run_lead_generation(config: dict | None = None) -> list[dict]:
    """Run the lead generation pipeline and return qualified leads."""
    if config is None:
        config = DEFAULT_CONFIG

    os.makedirs("logs", exist_ok=True)
    logger.info("Starting lead generation pipeline...")
    logger.info(f"Target niches: {', '.join(config['niches'])}")

    raw_leads = generate_sample_leads(config["max_leads"])
    logger.info(f"Found {len(raw_leads)} raw leads")

    # Score and filter leads
    qualified_leads = []
    for lead in raw_leads:
        lead["score"] = score_lead(lead)
        lead["source"] = "sample_generator"
        lead["date_added"] = datetime.now().strftime("%Y-%m-%d")
        if lead["score"] >= 40:  # Only keep leads with score ≥ 40
            qualified_leads.append(lead)

    qualified_leads.sort(key=lambda x: x["score"], reverse=True)

    logger.info(f"Qualified leads (score ≥ 40): {len(qualified_leads)}")

    # Export results
    export_to_csv(qualified_leads, config["output_file"])
    export_to_json(qualified_leads, config["output_file"])

    # Summary
    avg_score = sum(l["score"] for l in qualified_leads) / len(qualified_leads) if qualified_leads else 0
    logger.info(f"Pipeline complete — {len(qualified_leads)} leads, avg score: {avg_score:.1f}")

    return qualified_leads


def main():
    parser = argparse.ArgumentParser(description="Agency Research Automation — Lead Generation")
    parser.add_argument("--max-leads", type=int, default=100, help="Maximum leads to generate")
    parser.add_argument("--output", type=str, default="output/leads.csv", help="Output CSV file path")
    parser.add_argument("--niche", type=str, help="Specific niche to target")
    args = parser.parse_args()

    config = DEFAULT_CONFIG.copy()
    config["max_leads"] = args.max_leads
    config["output_file"] = args.output
    if args.niche:
        config["niches"] = [args.niche]

    leads = run_lead_generation(config)

    print(f"\n✅ Lead generation complete!")
    print(f"   Total qualified leads: {len(leads)}")
    print(f"   Saved to: {config['output_file']}")
    print(f"\nTop 5 leads by score:")
    for i, lead in enumerate(leads[:5], 1):
        print(f"   {i}. {lead['company_name']} ({lead['contact_email']}) — Score: {lead['score']}")


if __name__ == "__main__":
    main()
