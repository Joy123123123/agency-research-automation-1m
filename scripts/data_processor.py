"""
Data Processor Script — Agency Research Automation
Owner: Md Jamil Islam

Cleans, deduplicates, validates, and formats lead and research data
for use in outreach campaigns and client reports.
"""

import csv
import json
import logging
import argparse
import os
import re
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# VALIDATION HELPERS
# ─────────────────────────────────────────────


def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def is_valid_url(url: str) -> bool:
    """Check if a URL looks valid."""
    return url.strip().startswith(("http://", "https://"))


def normalize_phone(phone: str) -> str:
    """Normalize phone numbers to a consistent format."""
    digits = re.sub(r"[^\d+]", "", phone)
    if len(digits) == 10:
        return f"+1{digits}"
    return digits if digits else ""


def normalize_url(url: str) -> str:
    """Ensure URL has a proper scheme."""
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text."""
    return " ".join(text.strip().split()) if text else ""


# ─────────────────────────────────────────────
# LEAD DATA PROCESSING
# ─────────────────────────────────────────────


def validate_lead(lead: dict) -> tuple[bool, list[str]]:
    """
    Validate a lead record.

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    # Required fields
    if not lead.get("company_name"):
        issues.append("Missing company_name")
    if not lead.get("contact_email"):
        issues.append("Missing contact_email")
    elif not is_valid_email(lead["contact_email"]):
        issues.append(f"Invalid email: {lead['contact_email']}")

    # Optional but important
    if not lead.get("contact_name"):
        issues.append("Missing contact_name (warning)")
    if lead.get("website") and not is_valid_url(normalize_url(lead["website"])):
        issues.append(f"Suspicious website URL: {lead['website']}")

    return (len([i for i in issues if "warning" not in i]) == 0, issues)


def clean_lead(lead: dict) -> dict:
    """Clean and normalize a single lead record."""
    cleaned = {}

    # Text fields
    for field in ["company_name", "contact_name", "contact_title", "industry", "location"]:
        cleaned[field] = clean_text(lead.get(field, ""))

    # Email — lowercase and strip
    email = lead.get("contact_email", "").strip().lower()
    cleaned["contact_email"] = email

    # URL normalization
    cleaned["website"] = normalize_url(lead.get("website", ""))
    cleaned["linkedin_url"] = normalize_url(lead.get("linkedin_url", ""))

    # Phone normalization
    cleaned["phone"] = normalize_phone(lead.get("phone", ""))

    # Numeric fields
    try:
        cleaned["score"] = int(lead.get("score", 0))
    except (ValueError, TypeError):
        cleaned["score"] = 0

    # Pass-through fields
    cleaned["source"] = lead.get("source", "unknown")
    cleaned["date_added"] = lead.get("date_added", datetime.now().strftime("%Y-%m-%d"))

    return cleaned


def deduplicate_leads(leads: list[dict]) -> tuple[list[dict], int]:
    """
    Remove duplicate leads based on email address.

    Returns:
        (deduplicated_leads, count_removed)
    """
    seen_emails: set[str] = set()
    unique_leads = []
    duplicates = 0

    for lead in leads:
        email = lead.get("contact_email", "").strip().lower()
        if email and email in seen_emails:
            duplicates += 1
            logger.debug(f"Duplicate removed: {email}")
        else:
            if email:
                seen_emails.add(email)
            unique_leads.append(lead)

    return unique_leads, duplicates


# ─────────────────────────────────────────────
# BATCH PROCESSING
# ─────────────────────────────────────────────


def process_leads_csv(
    input_file: str,
    output_file: Optional[str] = None,
    min_score: int = 0,
) -> dict:
    """
    Process a leads CSV file: clean, validate, deduplicate, and filter.

    Args:
        input_file: Path to raw leads CSV
        output_file: Path to write cleaned CSV (defaults to input_clean.csv)
        min_score: Minimum score threshold to include lead

    Returns:
        Processing statistics dict
    """
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return {"error": "File not found"}

    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_clean{ext}"

    stats = {
        "input_count": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "duplicates_removed": 0,
        "below_score_threshold": 0,
        "output_count": 0,
        "output_file": output_file,
    }

    # Load raw data
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_leads = list(reader)

    stats["input_count"] = len(raw_leads)
    logger.info(f"Loaded {stats['input_count']} leads from {input_file}")

    # Clean each lead
    cleaned_leads = [clean_lead(lead) for lead in raw_leads]

    # Validate
    valid_leads = []
    for lead in cleaned_leads:
        is_valid, issues = validate_lead(lead)
        if is_valid:
            valid_leads.append(lead)
        else:
            stats["invalid_count"] += 1
            logger.debug(f"Invalid lead {lead.get('contact_email', 'unknown')}: {issues}")

    stats["valid_count"] = len(valid_leads)

    # Deduplicate
    deduped_leads, dup_count = deduplicate_leads(valid_leads)
    stats["duplicates_removed"] = dup_count

    # Filter by score
    if min_score > 0:
        filtered = [l for l in deduped_leads if l.get("score", 0) >= min_score]
        stats["below_score_threshold"] = len(deduped_leads) - len(filtered)
        deduped_leads = filtered

    stats["output_count"] = len(deduped_leads)

    # Sort by score descending
    deduped_leads.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Write output
    if deduped_leads:
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        fieldnames = list(deduped_leads[0].keys())

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(deduped_leads)

        logger.info(f"Wrote {stats['output_count']} clean leads to {output_file}")
    else:
        logger.warning("No leads to write after processing")

    return stats


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Agency Research Automation — Data Processor")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("--output", help="Output CSV file path")
    parser.add_argument("--min-score", type=int, default=40, help="Minimum lead score (default: 40)")
    args = parser.parse_args()

    stats = process_leads_csv(
        input_file=args.input,
        output_file=args.output,
        min_score=args.min_score,
    )

    if "error" in stats:
        print(f"\n❌ Error: {stats['error']}")
        return

    print(f"\n✅ Data processing complete!")
    print(f"   Input leads:         {stats['input_count']}")
    print(f"   Valid leads:         {stats['valid_count']}")
    print(f"   Invalid removed:     {stats['invalid_count']}")
    print(f"   Duplicates removed:  {stats['duplicates_removed']}")
    print(f"   Below score cutoff:  {stats['below_score_threshold']}")
    print(f"   ─────────────────────────────")
    print(f"   Output leads:        {stats['output_count']}")
    print(f"   Saved to:            {stats['output_file']}")


if __name__ == "__main__":
    main()
