"""
Data Processor Script
Cleans, deduplicates, and enriches data in tracking CSV files.

Usage:
    python data_processor.py --input ../tracking/client_tracker.csv --dedupe
    python data_processor.py --input ../tracking/client_tracker.csv --enrich
    python data_processor.py --report metrics
"""

import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TRACKING_DIR = os.path.join(os.path.dirname(__file__), "../tracking")
CLIENT_TRACKER = os.path.join(TRACKING_DIR, "client_tracker.csv")
METRICS_TRACKER = os.path.join(TRACKING_DIR, "metrics_tracker.csv")
REVENUE_TRACKER = os.path.join(TRACKING_DIR, "revenue_tracker.csv")


# ---------------------------------------------------------------------------
# CSV utilities
# ---------------------------------------------------------------------------

def read_csv(filepath: str) -> tuple[list[str], list[dict]]:
    """Read a CSV file and return (headers, rows)."""
    if not os.path.isfile(filepath):
        return [], []

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)

    return list(headers), rows


def write_csv(filepath: str, headers: list[str], rows: list[dict]) -> None:
    """Write rows to a CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Written {len(rows)} rows to {filepath}")


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate(rows: list[dict], key_field: str = "email") -> tuple[list[dict], int]:
    """Remove duplicate rows based on a key field."""
    seen: set[str] = set()
    unique: list[dict] = []
    removed = 0

    for row in rows:
        key = (row.get(key_field) or "").strip().lower()
        if not key or key in seen:
            removed += 1
            continue
        seen.add(key)
        unique.append(row)

    return unique, removed


# ---------------------------------------------------------------------------
# Data cleaning
# ---------------------------------------------------------------------------

def clean_email(email: str) -> str:
    """Basic email cleaning."""
    return email.strip().lower()


def clean_phone(phone: str) -> str:
    """Strip non-digit characters for uniformity."""
    import re
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return phone.strip()


def clean_url(url: str) -> str:
    """Ensure URLs have a scheme."""
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def clean_row(row: dict) -> dict:
    """Apply cleaning functions to a single row."""
    cleaned = dict(row)
    if cleaned.get("email"):
        cleaned["email"] = clean_email(cleaned["email"])
    if cleaned.get("phone"):
        cleaned["phone"] = clean_phone(cleaned["phone"])
    if cleaned.get("website"):
        cleaned["website"] = clean_url(cleaned["website"])
    if cleaned.get("linkedin_url"):
        cleaned["linkedin_url"] = clean_url(cleaned["linkedin_url"])
    return cleaned


# ---------------------------------------------------------------------------
# Analytics / reporting
# ---------------------------------------------------------------------------

def compute_metrics_summary(metrics_rows: list[dict]) -> dict:
    """Summarize email metrics from metrics_tracker.csv."""
    total_sent = sum(int(r.get("emails_sent", 0) or 0) for r in metrics_rows)
    total_failed = sum(int(r.get("emails_failed", 0) or 0) for r in metrics_rows)
    by_campaign: dict[str, int] = defaultdict(int)
    for r in metrics_rows:
        by_campaign[r.get("campaign", "unknown")] += int(r.get("emails_sent", 0) or 0)

    return {
        "total_sent": total_sent,
        "total_failed": total_failed,
        "by_campaign": dict(by_campaign),
    }


def compute_revenue_summary(revenue_rows: list[dict]) -> dict:
    """Summarize revenue from revenue_tracker.csv."""
    def _to_float(value: str) -> float:
        return float(str(value).replace("$", "").replace(",", "").strip() or 0)

    total_mrr = sum(_to_float(r.get("mrr", 0)) for r in revenue_rows if r.get("status") == "active")
    total_collected = sum(_to_float(r.get("amount_collected", 0)) for r in revenue_rows)
    client_count = len({r.get("client_name") for r in revenue_rows if r.get("status") == "active"})

    return {
        "active_clients": client_count,
        "mrr": round(total_mrr, 2),
        "total_collected": round(total_collected, 2),
        "annual_run_rate": round(total_mrr * 12, 2),
    }


def compute_pipeline_summary(client_rows: list[dict]) -> dict:
    """Summarize lead pipeline from client_tracker.csv."""
    status_counts: dict[str, int] = defaultdict(int)
    for row in client_rows:
        status_counts[row.get("status", "unknown")] += 1

    return dict(status_counts)


def print_report(report_type: str) -> None:
    """Print a summary report to stdout."""
    print(f"\n{'='*60}")
    print(f"  Agency Research Automation - {report_type.upper()} REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    if report_type in ("metrics", "all"):
        _, metrics_rows = read_csv(METRICS_TRACKER)
        summary = compute_metrics_summary(metrics_rows)
        print("📧 EMAIL METRICS")
        print(f"   Total Sent:   {summary['total_sent']}")
        print(f"   Total Failed: {summary['total_failed']}")
        print("   By Campaign:")
        for campaign, count in summary["by_campaign"].items():
            print(f"     - {campaign}: {count}")
        print()

    if report_type in ("revenue", "all"):
        _, revenue_rows = read_csv(REVENUE_TRACKER)
        summary = compute_revenue_summary(revenue_rows)
        print("💰 REVENUE SUMMARY")
        print(f"   Active Clients:    {summary['active_clients']}")
        print(f"   MRR:               ${summary['mrr']:,.2f}")
        print(f"   Total Collected:   ${summary['total_collected']:,.2f}")
        print(f"   Annual Run Rate:   ${summary['annual_run_rate']:,.2f}")
        target = 1_000_000
        pct = summary["annual_run_rate"] / target * 100
        print(f"   Progress to $1M:   {pct:.1f}%")
        print()

    if report_type in ("pipeline", "all"):
        _, client_rows = read_csv(CLIENT_TRACKER)
        summary = compute_pipeline_summary(client_rows)
        print("🎯 LEAD PIPELINE")
        for status, count in sorted(summary.items()):
            print(f"   {status:20s}: {count}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Process and analyze tracking data")
    parser.add_argument("--input", default=CLIENT_TRACKER, help="Input CSV file to process")
    parser.add_argument("--dedupe", action="store_true", help="Remove duplicate rows")
    parser.add_argument("--clean", action="store_true", help="Clean and normalize data")
    parser.add_argument(
        "--report",
        choices=["metrics", "revenue", "pipeline", "all"],
        help="Print a summary report",
    )
    args = parser.parse_args()

    if args.report:
        print_report(args.report)
        return

    headers, rows = read_csv(args.input)
    if not rows:
        print(f"[INFO] No data found in {args.input}")
        return

    original_count = len(rows)
    print(f"[INFO] Loaded {original_count} rows from {args.input}")

    if args.clean:
        rows = [clean_row(r) for r in rows]
        print(f"[OK] Cleaned {len(rows)} rows")

    if args.dedupe:
        rows, removed = deduplicate(rows)
        print(f"[OK] Removed {removed} duplicates. Remaining: {len(rows)}")

    if args.clean or args.dedupe:
        write_csv(args.input, headers, rows)

    print(f"[DONE] Processed {original_count} → {len(rows)} rows")


if __name__ == "__main__":
    main()
