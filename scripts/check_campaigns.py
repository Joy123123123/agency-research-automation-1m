#!/usr/bin/env python3
"""
Check Campaigns Script — Review outreach campaign status and follow-up queue.

Usage:
  python scripts/check_campaigns.py               # show all campaigns
  python scripts/check_campaigns.py --status sent  # filter by status
  python scripts/check_campaigns.py --due          # show follow-ups due today

Owner: Md Jamil Islam
"""
import sys
import csv
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

LEADS_CSV = "tracking/leads.csv"
FOLLOW_UP_DIR = Path("data/follow_ups")


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


def load_follow_ups() -> list[dict]:
    """Load pending follow-up tasks from data/follow_ups/."""
    tasks: list[dict] = []
    if not FOLLOW_UP_DIR.exists():
        return tasks
    for path in sorted(FOLLOW_UP_DIR.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                task = json.load(f)
                task["_file"] = path.name
                tasks.append(task)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read %s: %s", path, exc)
    return tasks


def _fmt_date(iso: str) -> str:
    """Format ISO timestamp to readable date."""
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return iso[:10]


# ── report sections ───────────────────────────────────────────────────────────

def show_campaign_table(leads: list[dict], status_filter: str | None) -> None:
    """Print a table of contacted leads grouped by status."""
    contacted = [r for r in leads if r.get("contacted_at") or r.get("status") != "new"]

    if status_filter:
        contacted = [r for r in contacted if r.get("status", "").lower() == status_filter.lower()]

    if not contacted:
        if status_filter:
            print(f"\n  ℹ️  No leads with status='{status_filter}' found.")
        else:
            print("\n  ℹ️  No contacted leads yet. Run send_outreach.py first.")
        return

    header = f"  {'#':<4} {'Name':<28} {'Email':<30} {'Status':<12} {'Contacted':<12} {'Replied':<12}"
    print()
    print("  " + "─" * (len(header) - 2))
    print(header)
    print("  " + "─" * (len(header) - 2))
    for i, row in enumerate(contacted[:50], 1):
        name = row.get("name", "")[:27]
        email = row.get("email", "")[:29]
        status = row.get("status", "new")[:11]
        contacted_at = _fmt_date(row.get("contacted_at", ""))
        replied_at = _fmt_date(row.get("replied_at", ""))
        print(f"  {i:<4} {name:<28} {email:<30} {status:<12} {contacted_at:<12} {replied_at:<12}")

    if len(contacted) > 50:
        print(f"\n  … and {len(contacted) - 50} more (use --status to filter)")
    print("  " + "─" * (len(header) - 2))


def show_status_summary(leads: list[dict]) -> None:
    """Print a quick status count summary."""
    statuses = Counter(r.get("status", "new") for r in leads)
    total = len(leads)

    print("\n┌─────────────────────────────────────────┐")
    print("│         📬  CAMPAIGN STATUS SUMMARY     │")
    print("├─────────────────────────────────────────┤")
    for status, count in sorted(statuses.items()):
        pct = f"{count / total * 100:.1f}%" if total else "0%"
        print(f"│  {status:<16} {count:>4}  ({pct:>6})           │")
    print(f"├─────────────────────────────────────────┤")
    print(f"│  Total              {total:>4}  (100%)           │")
    print("└─────────────────────────────────────────┘")


def show_follow_ups_due(tasks: list[dict]) -> None:
    """Print follow-up tasks that are due today or overdue."""
    now = datetime.utcnow()
    due: list[dict] = []
    for task in tasks:
        due_at_str = task.get("due_at") or task.get("next_follow_up")
        if not due_at_str:
            continue
        try:
            due_at = datetime.fromisoformat(due_at_str)
            if due_at <= now + timedelta(hours=24):
                task["_due_at"] = due_at
                due.append(task)
        except (ValueError, TypeError):
            pass

    print()
    print("┌─────────────────────────────────────────┐")
    print("│       ⏰  FOLLOW-UPS DUE (next 24h)     │")
    print("├─────────────────────────────────────────┤")
    if not due:
        print("│  ✅  No follow-ups due — you're all caught up! │")
    else:
        for task in sorted(due, key=lambda t: t["_due_at"])[:20]:
            email = task.get("email", "unknown")[:28]
            name = task.get("name", "")[:20]
            due_str = task["_due_at"].strftime("%m-%d %H:%M")
            overdue = "⚠️ OVERDUE" if task["_due_at"] < now else ""
            print(f"│  {due_str}  {name:<20}  {email:<28} {overdue}")
    print("└─────────────────────────────────────────┘")

    if len(tasks) > 0:
        print(f"\n  📁  Total queued follow-up tasks: {len(tasks)}")


def show_niche_conversion(leads: list[dict]) -> None:
    """Print conversion rate per niche."""
    niche_data: dict[str, Counter] = defaultdict(Counter)
    for r in leads:
        niche = r.get("niche", "unknown")
        niche_data[niche]["total"] += 1
        if r.get("replied_at"):
            niche_data[niche]["replied"] += 1
        if r.get("converted_at"):
            niche_data[niche]["converted"] += 1

    if not niche_data:
        return

    print()
    print("┌──────────────────────────────────────────────────────┐")
    print("│              📈  CONVERSION BY NICHE                 │")
    print("├──────────────────────────────────────────────────────┤")
    print(f"│  {'Niche':<20} {'Total':>6} {'Replied':>8} {'Converted':>10}      │")
    print("├──────────────────────────────────────────────────────┤")
    for niche, counts in sorted(niche_data.items(), key=lambda x: -x[1]["total"]):
        replied_pct = f"{counts['replied'] / counts['total'] * 100:.0f}%" if counts["total"] else "0%"
        converted_pct = f"{counts['converted'] / counts['total'] * 100:.0f}%" if counts["total"] else "0%"
        print(
            f"│  {niche[:20]:<20} {counts['total']:>6} "
            f"{counts['replied']:>4}({replied_pct:>4}) "
            f"{counts['converted']:>5}({converted_pct:>4})      │"
        )
    print("└──────────────────────────────────────────────────────┘")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Campaign Status Checker")
    parser.add_argument(
        "--status",
        metavar="STATUS",
        help="Filter leads by status (e.g. new, sent, replied, converted)",
    )
    parser.add_argument(
        "--due",
        action="store_true",
        help="Show only follow-ups due in the next 24 hours",
    )
    parser.add_argument(
        "--niches",
        action="store_true",
        help="Show conversion breakdown by niche",
    )
    args = parser.parse_args()

    leads = load_leads()
    follow_ups = load_follow_ups()

    print("\n" + "=" * 54)
    print("   🔎  AGENCY RESEARCH — CAMPAIGN CHECKER")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 54)

    if not leads:
        print("\n⚠️  No leads found in tracking/leads.csv")
        print("   Run research first:")
        print("   python scripts/run_research.py --niche plumbing --location 'New York'")
        return

    if args.due:
        show_follow_ups_due(follow_ups)
        return

    show_status_summary(leads)
    show_campaign_table(leads, args.status)

    if args.niches:
        show_niche_conversion(leads)

    show_follow_ups_due(follow_ups)

    print()
    print("💡  Tips:")
    print("   python scripts/check_campaigns.py --status replied  — see replies")
    print("   python scripts/check_campaigns.py --due             — see follow-ups due")
    print("   python scripts/check_campaigns.py --niches          — conversion by niche")
    print("   python scripts/send_outreach.py --campaign follow_up — send follow-ups")
    print()


if __name__ == "__main__":
    main()
