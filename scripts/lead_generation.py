"""
Lead Generation Script
Scrapes and enriches marketing agency leads from various sources.

Usage:
    python lead_generation.py --industry marketing --country US --count 50
    python lead_generation.py --help
"""

import argparse
import csv
import json
import os
import time
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../tracking/client_tracker.csv")

CSV_HEADERS = [
    "id",
    "company_name",
    "website",
    "contact_name",
    "contact_title",
    "email",
    "phone",
    "linkedin_url",
    "industry",
    "employee_count",
    "location",
    "annual_revenue_estimate",
    "lead_score",
    "source",
    "date_added",
    "status",
    "notes",
]


# ---------------------------------------------------------------------------
# Apollo.io integration
# ---------------------------------------------------------------------------

def search_apollo(industry: str, country: str, count: int) -> list[dict]:
    """Search for leads using Apollo.io API."""
    if not APOLLO_API_KEY:
        print("[WARNING] APOLLO_API_KEY not set. Using mock data.")
        return _mock_leads(industry, country, count)

    url = "https://api.apollo.io/v1/mixed_people/search"
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY,
    }
    payload = {
        "page": 1,
        "per_page": min(count, 100),
        "person_titles": ["CEO", "Owner", "Founder", "Director of Marketing"],
        "organization_industry_tag_ids": [],
        "q_keywords": industry,
        "contact_email_status": ["verified"],
        "organization_locations": [country],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("people", [])
    except requests.RequestException as exc:
        print(f"[ERROR] Apollo API request failed: {exc}")
        return []


def enrich_email_hunter(domain: str) -> Optional[str]:
    """Try to find an email for a domain using Hunter.io."""
    if not HUNTER_API_KEY:
        return None

    url = "https://api.hunter.io/v2/domain-search"
    params = {"domain": domain, "api_key": HUNTER_API_KEY, "limit": 1}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        emails = data.get("data", {}).get("emails", [])
        if emails:
            return emails[0].get("value")
    except requests.RequestException as exc:
        print(f"[WARNING] Hunter.io request failed for {domain}: {exc}")

    return None


# ---------------------------------------------------------------------------
# Lead scoring
# ---------------------------------------------------------------------------

def score_lead(lead: dict) -> int:
    """
    Score a lead from 1-10 based on fit criteria.
    Higher = better fit for the service.
    """
    score = 5  # baseline

    # Employee count (sweet spot: 5-50)
    emp = lead.get("employee_count", 0)
    if isinstance(emp, str):
        emp = 0
    if 5 <= emp <= 20:
        score += 2
    elif 21 <= emp <= 50:
        score += 1
    elif emp > 100:
        score -= 1

    # Has verified email
    if lead.get("email"):
        score += 1

    # Has LinkedIn
    if lead.get("linkedin_url"):
    	score += 1

    # Title match (decision maker)
    title = (lead.get("contact_title") or "").lower()
    if any(t in title for t in ["ceo", "founder", "owner", "director", "vp"]):
        score += 1

    return max(1, min(10, score))


# ---------------------------------------------------------------------------
# Data normalization
# ---------------------------------------------------------------------------

def normalize_apollo_lead(raw: dict, idx: int) -> dict:
    """Convert Apollo.io API response to our CSV format."""
    org = raw.get("organization", {}) or {}
    return {
        "id": f"LEAD-{idx:04d}",
        "company_name": org.get("name", ""),
        "website": org.get("website_url", ""),
        "contact_name": f"{raw.get('first_name', '')} {raw.get('last_name', '')}".strip(),
        "contact_title": (raw.get("title") or ""),
        "email": raw.get("email", ""),
        "phone": (raw.get("phone_numbers") or [{}])[0].get("raw_number", ""),
        "linkedin_url": raw.get("linkedin_url", ""),
        "industry": (org.get("industry") or ""),
        "employee_count": org.get("estimated_num_employees", ""),
        "location": f"{raw.get('city', '')}, {raw.get('state', '')}, {raw.get('country', '')}".strip(", "),
        "annual_revenue_estimate": org.get("annual_revenue_printed", ""),
        "lead_score": "",  # filled after scoring
        "source": "Apollo.io",
        "date_added": datetime.now().strftime("%Y-%m-%d"),
        "status": "new",
        "notes": "",
    }


def _mock_leads(industry: str, country: str, count: int) -> list[dict]:
    """Return mock leads when no API key is configured (for testing)."""
    mock = []
    for i in range(1, count + 1):
        mock.append({
            "id": f"LEAD-{i:04d}",
            "company_name": f"Sample {industry.title()} Agency {i}",
            "website": f"https://sampleagency{i}.com",
            "contact_name": f"Contact Person {i}",
            "contact_title": "CEO",
            "email": f"contact{i}@sampleagency{i}.com",
            "phone": "+1-555-000-0000",
            "linkedin_url": f"https://linkedin.com/in/contact{i}",
            "industry": industry,
            "employee_count": 10,
            "location": f"{country}",
            "annual_revenue_estimate": "$500K",
            "lead_score": 7,
            "source": "Mock Data",
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "status": "new",
            "notes": "Mock lead for testing",
        })
    return mock


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def save_leads(leads: list[dict], output_path: str) -> None:
    """Append leads to the CSV tracker file."""
    file_exists = os.path.isfile(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(leads)

    print(f"[OK] Saved {len(leads)} leads to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate marketing agency leads")
    parser.add_argument("--industry", default="marketing agency", help="Industry keyword")
    parser.add_argument("--country", default="US", help="Country code (US, GB, CA, AU)")
    parser.add_argument("--count", type=int, default=50, help="Number of leads to fetch")
    parser.add_argument("--output", default=OUTPUT_FILE, help="Output CSV file path")
    args = parser.parse_args()

    print(f"[INFO] Searching for {args.count} leads in '{args.industry}' ({args.country})...")

    raw_leads = search_apollo(args.industry, args.country, args.count)
    print(f"[INFO] Found {len(raw_leads)} raw leads from Apollo.io")

    processed: list[dict] = []
    for idx, raw in enumerate(raw_leads, start=1):
        lead = normalize_apollo_lead(raw, idx)

        # Enrich missing email via Hunter.io
        if not lead["email"] and lead["website"]:
            domain = lead["website"].replace("https://", "").replace("http://", "").split("/")[0]
            lead["email"] = enrich_email_hunter(domain) or ""

        lead["lead_score"] = score_lead(lead)
        processed.append(lead)
        time.sleep(0.1)  # rate limiting

    if not processed and isinstance(raw_leads[0], dict) and raw_leads[0].get("source") == "Mock Data":
        # raw_leads already normalized (mock path)
        processed = raw_leads

    # Sort by score descending
    processed.sort(key=lambda x: int(x.get("lead_score", 0) or 0), reverse=True)

    save_leads(processed, args.output)
    print(f"[DONE] Lead generation complete. Top lead score: {processed[0]['lead_score'] if processed else 'N/A'}")


if __name__ == "__main__":
    main()
