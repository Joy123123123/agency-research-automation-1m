"""
Data Processor Script
Creator: Md Jamil Islam
Purpose: Process and analyze tracking data for revenue and client metrics
"""

import csv
import os
from datetime import datetime


def load_csv(filename: str) -> list[dict]:
    """Load data from a CSV file."""
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def calculate_revenue_stats(revenue_data: list[dict]) -> dict:
    """Calculate revenue statistics from tracker data."""
    if not revenue_data:
        return {"total": 0, "monthly_avg": 0, "entries": 0}

    def parse_amount(value: str) -> float:
        try:
            return float(str(value).replace("$", "").replace(",", "").strip())
        except ValueError:
            return 0.0

    total = sum(parse_amount(row.get("amount", 0)) for row in revenue_data)
    return {
        "total": total,
        "monthly_avg": total / max(len(revenue_data), 1),
        "entries": len(revenue_data),
    }


def calculate_client_stats(client_data: list[dict]) -> dict:
    """Calculate client pipeline statistics."""
    if not client_data:
        return {}

    status_counts: dict[str, int] = {}
    for row in client_data:
        status = row.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    return status_counts


def generate_summary_report(
    client_data: list[dict],
    revenue_data: list[dict],
) -> str:
    """Generate a text summary report of all metrics."""
    today = datetime.today().strftime("%B %d, %Y")
    revenue_stats = calculate_revenue_stats(revenue_data)
    client_stats = calculate_client_stats(client_data)

    lines = [
        "=" * 50,
        f"  BUSINESS SUMMARY REPORT",
        f"  Creator: Md Jamil Islam",
        f"  Date: {today}",
        "=" * 50,
        "",
        "📊 CLIENT PIPELINE",
        "-" * 30,
    ]

    for status, count in client_stats.items():
        lines.append(f"  {status.capitalize()}: {count}")

    lines += [
        "",
        "💰 REVENUE",
        "-" * 30,
        f"  Total Revenue: ${revenue_stats['total']:,.2f}",
        f"  Avg per Entry: ${revenue_stats['monthly_avg']:,.2f}",
        f"  Total Entries: {revenue_stats['entries']}",
        "",
        "=" * 50,
    ]

    return "\n".join(lines)


def main():
    print("=== Data Processor Script ===")
    print(f"Creator: Md Jamil Islam")
    print(f"Date: {datetime.today().strftime('%Y-%m-%d')}")
    print()

    client_data = load_csv("tracking/client_tracker.csv")
    revenue_data = load_csv("tracking/revenue_tracker.csv")

    if not client_data and not revenue_data:
        print("No data found yet. Run lead_generation.py first to create tracking data.")
        return

    report = generate_summary_report(client_data, revenue_data)
    print(report)

    # Save report
    report_filename = f"tracking/summary_{datetime.today().strftime('%Y%m%d')}.txt"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSummary saved to {report_filename}")


if __name__ == "__main__":
    main()
