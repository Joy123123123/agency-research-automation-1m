# Data Processing Utilities
# Author: Md Jamil Islam

import csv
import json
from datetime import datetime
from typing import Optional


def calculate_metrics(metrics_csv: str) -> dict:
    """
    Calculate key business metrics from the tracking CSV.
    
    Args:
        metrics_csv: Path to metrics CSV file
    
    Returns:
        Dictionary of calculated metrics
    """
    try:
        with open(metrics_csv, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        return {}
    
    if not rows:
        return {}
    
    metrics = {
        "total_outreach": 0,
        "total_replies": 0,
        "total_calls": 0,
        "total_proposals": 0,
        "total_clients": 0,
        "total_revenue": 0.0,
        "reply_rate": 0.0,
        "call_conversion": 0.0,
        "close_rate": 0.0,
        "revenue_per_client": 0.0,
    }
    
    for row in rows:
        metrics["total_outreach"] += int(row.get("emails_sent", 0) or 0)
        metrics["total_replies"] += int(row.get("replies", 0) or 0)
        metrics["total_calls"] += int(row.get("calls", 0) or 0)
        metrics["total_proposals"] += int(row.get("proposals", 0) or 0)
        metrics["total_clients"] += int(row.get("new_clients", 0) or 0)
        metrics["total_revenue"] += float(row.get("revenue", 0) or 0)
    
    if metrics["total_outreach"] > 0:
        metrics["reply_rate"] = round(metrics["total_replies"] / metrics["total_outreach"] * 100, 1)
    
    if metrics["total_replies"] > 0:
        metrics["call_conversion"] = round(metrics["total_calls"] / metrics["total_replies"] * 100, 1)
    
    if metrics["total_calls"] > 0:
        metrics["close_rate"] = round(metrics["total_clients"] / metrics["total_calls"] * 100, 1)
    
    if metrics["total_clients"] > 0:
        metrics["revenue_per_client"] = round(metrics["total_revenue"] / metrics["total_clients"], 2)
    
    return metrics


def generate_weekly_summary(metrics_csv: str, output_file: Optional[str] = None) -> str:
    """
    Generate a weekly performance summary report.
    
    Args:
        metrics_csv: Path to metrics CSV
        output_file: Optional path to save the summary
    
    Returns:
        Formatted summary string
    """
    metrics = calculate_metrics(metrics_csv)
    
    summary = f"""
=== WEEKLY PERFORMANCE SUMMARY ===
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Author: Md Jamil Islam - Agency Research Automation

OUTREACH METRICS:
  Total emails sent:   {metrics.get('total_outreach', 0)}
  Total replies:       {metrics.get('total_replies', 0)}
  Reply rate:          {metrics.get('reply_rate', 0)}%

SALES METRICS:
  Discovery calls:     {metrics.get('total_calls', 0)}
  Proposals sent:      {metrics.get('total_proposals', 0)}
  New clients:         {metrics.get('total_clients', 0)}
  Close rate:          {metrics.get('close_rate', 0)}%

REVENUE:
  Total revenue:       ${metrics.get('total_revenue', 0):,.2f}
  Revenue per client:  ${metrics.get('revenue_per_client', 0):,.2f}
===================================
"""
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"Summary saved to {output_file}")
    
    return summary


def merge_csv_files(file_list: list, output_file: str):
    """
    Merge multiple CSV files into one.
    
    Args:
        file_list: List of CSV file paths
        output_file: Output merged CSV path
    """
    all_rows = []
    fieldnames = None
    
    for filepath in file_list:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if fieldnames is None:
                    fieldnames = reader.fieldnames
                all_rows.extend(list(reader))
        except FileNotFoundError:
            print(f"File not found: {filepath}")
    
    if all_rows and fieldnames:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"Merged {len(all_rows)} rows into {output_file}")


if __name__ == "__main__":
    summary = generate_weekly_summary("tracking/metrics_tracker.csv")
    print(summary)
