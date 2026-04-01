#!/usr/bin/env python3
"""
Dashboard Script — Terminal overview of leads, campaigns, and pipeline health.

Usage:
  python scripts/dashboard.py            # show full dashboard
  python scripts/dashboard.py --watch    # refresh every 30 seconds

Owner: Md Jamil Islam
"""
import sys
import csv
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

LEADS_CSV = "tracking/leads.csv"
FOLLOW_UP_DIR = Path("data/follow_ups")
REPORTS_DIR = Path("data/reports")


# ── helpers ───────────────────────────────────────────────────────────────────

def load_leads(filepath: str = LEADS_CSV) -> list[dict]:
    """Load all leads from CSV, skipping comment lines."""
    leads: list[dict] = []
    try:
        with open(filepath, encoding="utf-8") as f:
            for row in csv.DictReader(
                (line for line in f if not line.startswith("#"))
            ):
                leads.append(row)
    except FileNotFoundError:
        logger.warning("Leads file not found: %s", filepath)
    return leads


def _bar(value: int, total: int, width: int = 20) -> str:
    """Return a simple ASCII progress bar."""
    filled = int(width * value / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def _pct(value: int, total: int) -> str:
    if not total:
        return "0%"
    return f"{value / total * 100:.1f}%"


# ── sections ──────────────────────────────────────────────────────────────────

def show_leads_overview(leads: list[dict]) -> None:
    total = len(leads)
    statuses = Counter(r.get("status", "new") for r in leads)
    grades = Counter(r.get("grade", "?") for r in leads)

    print("┌─────────────────────────────────────────────────────┐")
    print("│                   📊  LEADS OVERVIEW                │")
    print("├─────────────────────────────────────────────────────┤")
    print(f"│  Total leads      : {total:<32}│")
    print("├─────────────────────────────────────────────────────┤")
    print("│  STATUS BREAKDOWN                                   │")
    for status, count in sorted(statuses.items()):
        bar = _bar(count, total)
        print(f"│  {status:<12} {bar}  {count:>4} ({_pct(count, total):>6})  │")
    print("├─────────────────────────────────────────────────────┤")
    print("│  GRADE BREAKDOWN                                    │")
    for grade in ("A+", "A", "B", "C", "?"):
        count = grades.get(grade, 0)
        if count:
            bar = _bar(count, total)
            print(f"│  Grade {grade:<4}  {bar}  {count:>4} ({_pct(count, total):>6})  │")
    print("└─────────────────────────────────────────────────────┘")


def show_campaign_stats(leads: list[dict]) -> None:
    now = datetime.utcnow()
    contacted = [r for r in leads if r.get("contacted_at")]
    replied = [r for r in leads if r.get("replied_at")]
    converted = [r for r in leads if r.get("converted_at")]
    total = len(leads)

    # last-7-day contacted
    recent: list[dict] = []
    for r in contacted:
        try:
            ts = datetime.fromisoformat(r["contacted_at"])
            if now - ts <= timedelta(days=7):
                recent.append(r)
        except (ValueError, TypeError):
            pass

    print()
    print("┌─────────────────────────────────────────────────────┐")
    print("│                 📧  CAMPAIGN STATS                  │")
    print("├─────────────────────────────────────────────────────┤")
    print(f"│  Contacted        : {len(contacted):<5}  ({_pct(len(contacted), total):>6} of total)    │")
    print(f"│  Replied          : {len(replied):<5}  ({_pct(len(replied), len(contacted)):>6} reply rate)  │")
    print(f"│  Converted        : {len(converted):<5}  ({_pct(len(converted), len(replied)):>6} close rate) │")
    print(f"│  Sent (last 7d)   : {len(recent):<32}│")
    print("└─────────────────────────────────────────────────────┘")


def show_niche_breakdown(leads: list[dict]) -> None:
    niches = Counter(r.get("niche", "unknown") for r in leads)
    total = len(leads)
    if not niches:
        return
    print()
    print("┌─────────────────────────────────────────────────────┐")
    print("│                  🏷️   TOP NICHES                    │")
    print("├─────────────────────────────────────────────────────┤")
    for niche, count in niches.most_common(8):
        bar = _bar(count, total, width=16)
        label = niche[:16].ljust(16)
        print(f"│  {label}  {bar}  {count:>4}              │")
    print("└─────────────────────────────────────────────────────┘")


def show_files_status() -> None:
    files = {
        "tracking/leads.csv": "Leads database",
        "config/api_keys.env": "API keys / credentials",
        "requirements.txt": "Python dependencies",
    }
    print()
    print("┌─────────────────────────────────────────────────────┐")
    print("│                  🗂️   FILE STATUS                   │")
    print("├─────────────────────────────────────────────────────┤")
    for path, label in files.items():
        icon = "✅" if Path(path).exists() else "❌"
        print(f"│  {icon}  {label:<42}│")
    follow_up_count = len(list(FOLLOW_UP_DIR.glob("*.json"))) if FOLLOW_UP_DIR.exists() else 0
    report_count = len(list(REPORTS_DIR.glob("*"))) if REPORTS_DIR.exists() else 0
    print(f"│  📁  Follow-up tasks queued: {follow_up_count:<22}│")
    print(f"│  📄  Reports generated     : {report_count:<22}│")
    print("└─────────────────────────────────────────────────────┘")


def show_dashboard() -> None:
    print("\n" + "=" * 55)
    print("     🤖  AGENCY RESEARCH AUTOMATION — DASHBOARD")
    print(f"     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    leads = load_leads()
    if not leads:
        print("\n⚠️  No leads found. Run research first:")
        print("   python scripts/run_research.py --niche plumbing --location 'New York'")
    else:
        show_leads_overview(leads)
        show_campaign_stats(leads)
        show_niche_breakdown(leads)

    show_files_status()

    print()
    print("💡  Quick commands:")
    print("   python scripts/run_research.py --help")
    print("   python scripts/send_outreach.py --dry-run")
    print("   python scripts/check_campaigns.py")
    print("   python scripts/generate_report.py --period weekly")
    print()


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Agency Automation Dashboard")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Auto-refresh dashboard every 30 seconds",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Refresh interval for --watch (default: 30)",
    )
    args = parser.parse_args()

    if args.watch:
        print("📡  Watch mode — press Ctrl+C to exit")
        try:
            while True:
                show_dashboard()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n👋  Dashboard stopped.")
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
