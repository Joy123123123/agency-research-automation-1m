#!/usr/bin/env python3
"""
Scheduler Script — Runs automated daily tasks
Usage: python scripts/scheduler.py --start
Owner: Md Jamil Islam
"""
import sys
import logging
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.automation.scheduler import AgencyScheduler
from config.settings import LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)


def run_research():
    subprocess.run([sys.executable, "scripts/run_research.py", "--count", "100"], check=False)


def run_outreach():
    subprocess.run([sys.executable, "scripts/send_outreach.py", "--campaign", "initial"], check=False)


def run_follow_ups():
    subprocess.run([sys.executable, "scripts/send_outreach.py", "--campaign", "follow_up"], check=False)


def run_report():
    subprocess.run([sys.executable, "scripts/generate_report.py", "--period", "weekly"], check=False)


def main():
    parser = argparse.ArgumentParser(description="Agency Scheduler")
    parser.add_argument("--start", action="store_true", help="Start the scheduler")
    args = parser.parse_args()

    if not args.start:
        parser.print_help()
        return

    scheduler = AgencyScheduler()
    scheduler.add_daily_research(run_research, hour=9, minute=0)
    scheduler.add_daily_outreach(run_outreach, hour=10, minute=0)
    scheduler.add_follow_up_check(run_follow_ups, interval_hours=6)
    scheduler.add_weekly_report(run_report, day="monday", hour=8)

    print("🚀 Agency Scheduler Started!")
    print("   📅 Daily research: 9:00 AM")
    print("   📧 Daily outreach: 10:00 AM")
    print("   🔄 Follow-up check: every 6 hours")
    print("   📊 Weekly report: Monday 8:00 AM")
    print("\nPress Ctrl+C to stop.\n")

    scheduler.run()


if __name__ == "__main__":
    main()
