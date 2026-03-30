#!/usr/bin/env python3
"""
Report Generator Script
Generates weekly/monthly performance reports
Usage: python scripts/generate_report.py --period weekly
Owner: Md Jamil Islam
"""
import sys
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporting.report_generator import ReportGenerator
from config.settings import LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Report Generator")
    parser.add_argument("--period", default="weekly", choices=["weekly", "monthly"], help="Report period")
    parser.add_argument("--format", default="html", choices=["html", "csv", "json"], help="Output format")
    args = parser.parse_args()

    generator = ReportGenerator()
    summary = generator.generate_weekly_summary()

    if args.format == "html":
        output = generator.generate_html_report(summary)
        print(f"\n✅ HTML report saved: {output}")
    elif args.format == "csv":
        output = generator.export_to_csv([], filename=f"summary_{args.period}.csv")
        print(f"\n✅ CSV exported: {output}")
    elif args.format == "json":
        import json
        output = f"data/reports/summary_{args.period}.json"
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n✅ JSON report saved: {output}")

    print("\n📊 Summary:")
    for key, value in summary.items():
        if key != "generated_at":
            print(f"   {key}: {value}")


if __name__ == "__main__":
    main()
