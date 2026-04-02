#!/usr/bin/env python3
"""
Free Mode — Fully free, no-API automation (Termux / Android friendly).

Runs lead research + generates manual outreach guidance in Bangla + English
+ sends results to Telegram automatically.

Usage:
  # Run once (for testing):
  python scripts/free_mode.py

  # Run with custom niche/location:
  python scripts/free_mode.py --niche lawyer --location "Los Angeles, CA" --count 30

  # Run as a daily scheduler loop (default 09:00):
  python scripts/free_mode.py --loop

  # Run scheduler at a custom time:
  python scripts/free_mode.py --loop --time 08:30

Requirements:
  pip install requests schedule   (both are in requirements-minimal.txt)

Telegram setup:
  TELEGRAM_BOT_TOKEN=<your token>   in config/api_keys.env
  TELEGRAM_CHAT_ID=<your chat id>   in config/api_keys.env

Owner: Md Jamil Islam
"""
import sys
import os
import csv
import logging
import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / "api_keys.env")
except ModuleNotFoundError:
    pass  # dotenv optional; env vars may be exported directly

try:
    import requests as _requests
except ImportError:
    _requests = None  # type: ignore

try:
    import schedule as _schedule
except ImportError:
    _schedule = None  # type: ignore

from config.settings import TRACKING_DIR

# ─── Logging setup ────────────────────────────────────────────────────────────

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/free_mode.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# Telegram credentials (loaded from env / api_keys.env)
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")


# ─── Telegram helpers ─────────────────────────────────────────────────────────

def _tg_api(endpoint: str, **kwargs) -> dict:
    """Call a Telegram Bot API endpoint. Returns decoded JSON or {}."""
    if _requests is None:
        logger.error("'requests' not installed. Run: pip install requests")
        return {}
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram notifications disabled.")
        return {}
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{endpoint}"
    try:
        resp = _requests.post(url, timeout=30, **kwargs)
        data = resp.json()
        if not data.get("ok"):
            logger.error("Telegram API error: %s", data.get("description", "unknown"))
        return data
    except Exception as exc:
        logger.error("Telegram request failed: %s", exc)
        return {}


def send_telegram_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a text message to the configured Telegram chat. Returns True on success."""
    if not TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID not set — skipping Telegram message.")
        return False
    result = _tg_api(
        "sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": parse_mode},
    )
    return bool(result.get("ok"))


def send_telegram_document(file_path: str, caption: str = "") -> bool:
    """Upload a file to the configured Telegram chat. Returns True on success."""
    if not TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID not set — skipping file upload.")
        return False
    fp = Path(file_path)
    if not fp.exists():
        logger.warning("File not found, skipping upload: %s", file_path)
        return False
    with open(fp, "rb") as fh:
        result = _tg_api(
            "sendDocument",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"document": (fp.name, fh)},
        )
    return bool(result.get("ok"))


# ─── Research runner ──────────────────────────────────────────────────────────

def run_research(niche: str, location: str, count: int, skip_scrape: bool) -> tuple:
    """
    Invoke scripts/run_research.py as a subprocess.

    Returns:
        (success: bool, output_path: str)
    """
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(TRACKING_DIR / "leads.csv")
    cmd = [
        sys.executable, "scripts/run_research.py",
        "--niche", niche,
        "--location", location,
        "--count", str(count),
        "--output", output_path,
    ]
    if skip_scrape:
        cmd.append("--skip-scrape")
    logger.info("Running research: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        logger.info("Research stdout:\n%s", result.stdout.strip())
    if result.returncode != 0:
        logger.error("Research stderr:\n%s", result.stderr.strip())
        return False, output_path
    return True, output_path


# ─── Report generator ─────────────────────────────────────────────────────────

def generate_report() -> tuple:
    """
    Invoke scripts/generate_report.py (JSON format) as a subprocess.

    Returns:
        (success: bool, report_path: str)
    """
    report_path = "data/reports/summary_weekly.json"
    cmd = [
        sys.executable, "scripts/generate_report.py",
        "--period", "weekly",
        "--format", "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning("Report generation failed:\n%s", result.stderr.strip())
        return False, report_path
    return True, report_path


# ─── Summary helpers ──────────────────────────────────────────────────────────

def load_leads_summary(leads_csv: str) -> dict:
    """
    Read leads.csv and return a summary dict.

    Keys: total, grade_a, grade_b, grade_c, top_leads (list of dicts).
    """
    summary: dict = {
        "total": 0,
        "grade_a": 0,
        "grade_b": 0,
        "grade_c": 0,
        "top_leads": [],
    }
    try:
        with open(leads_csv, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        summary["total"] = len(rows)
        for row in rows:
            grade = row.get("grade", "C").upper()
            if grade == "A":
                summary["grade_a"] += 1
            elif grade == "B":
                summary["grade_b"] += 1
            else:
                summary["grade_c"] += 1
        # Top 5 best leads (grade A or B)
        top = [r for r in rows if r.get("grade", "").upper() in ("A", "B")][:5]
        summary["top_leads"] = [
            {
                "name": r.get("name", "N/A"),
                "phone": r.get("phone", "N/A"),
                "website": r.get("website", "N/A"),
                "grade": r.get("grade", "N/A"),
                "score": r.get("lead_score", "N/A"),
                "location": r.get("location", r.get("address", "N/A")),
            }
            for r in top
        ]
    except FileNotFoundError:
        logger.warning("Leads CSV not found: %s", leads_csv)
    except Exception as exc:
        logger.error("Error reading leads: %s", exc)
    return summary


def build_telegram_message(
    niche: str,
    location: str,
    summary: dict,
    run_date: str,
) -> str:
    """
    Build the full Telegram HTML message:
    daily summary + step-by-step manual outreach guide (Bangla + English).
    """
    total = summary["total"]
    grade_a = summary["grade_a"]
    grade_b = summary["grade_b"]
    top_leads = summary["top_leads"]

    leads_text = ""
    for i, lead in enumerate(top_leads, 1):
        leads_text += (
            f"\n  {i}. <b>{lead['name']}</b> "
            f"[Grade: {lead['grade']}, Score: {lead['score']}]\n"
            f"     📞 {lead['phone']}\n"
            f"     🌐 {lead['website']}\n"
            f"     📍 {lead['location']}"
        )

    message = (
        f"🤖 <b>Agency Research — Free Mode Report</b>\n"
        f"📅 {run_date}\n"
        f"🎯 Niche: {niche} | 📍 Location: {location}\n\n"
        f"📊 <b>আজকের ফলাফল (Today's Results):</b>\n"
        f"  • মোট লিড (Total Leads): <b>{total}</b>\n"
        f"  • গ্রেড A (Grade A — Best): <b>{grade_a}</b>\n"
        f"  • গ্রেড B (Grade B — Good): <b>{grade_b}</b>\n"
        f"  • ফাইল: <code>tracking/leads.csv</code>\n\n"
        f"🌟 <b>সেরা লিড (Top Leads):</b>"
        f"{leads_text if leads_text else chr(10) + '  (No leads found yet)'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>ম্যানুয়াল আউটরিচ গাইড (Manual Outreach Guide)</b>\n"
        f"<i>Phone-only, step-by-step:</i>\n\n"
        f"<b>ধাপ ১ (Step 1) — লিড খুলুন (Open leads.csv):</b>\n"
        f"  গ্রেড A/B লিড দেখুন। প্রতিদিন ১০–২০টি নিন।\n"
        f"  <i>(Open tracking/leads.csv, pick top 10-20 Grade A/B leads per day.)</i>\n\n"
        f"<b>ধাপ ২ (Step 2) — ওয়েবসাইট চেক করুন (Check their website):</b>\n"
        f"  দেখুন সাইট পুরনো/slow কিনা। সমস্যা খুঁজুন।\n"
        f"  <i>(Check if their website is slow, outdated, or missing online booking.)</i>\n\n"
        f"<b>ধাপ ৩ (Step 3) — ফোন বা WhatsApp দিন (Call or WhatsApp):</b>\n"
        f"  বাংলা স্ক্রিপ্ট:\n"
        f"  <i>\"হ্যালো, আমি [নাম]। আমরা {niche} ব্যবসায়ীদের অনলাইন লিড বাড়াতে সাহায্য করি। "
        f"আপনার ওয়েবসাইট দেখলাম — কিছু সুযোগ আছে। ৫ মিনিট কথা বলতে পারবেন?\"</i>\n\n"
        f"  English script:\n"
        f"  <i>\"Hi, I help {niche} businesses get more clients online. "
        f"I checked your website and found some improvement opportunities. "
        f"Can we talk for 5 minutes?\"</i>\n\n"
        f"<b>ধাপ ৪ (Step 4) — অফার বলুন (Give your offer):</b>\n"
        f"  • Month 1: Free local SEO audit\n"
        f"  • Month 2+: Lead generation retainer — $1,500–$3,000/month\n\n"
        f"<b>ধাপ ৫ (Step 5) — ফলো-আপ (Follow-up):</b>\n"
        f"  Reply না করলে ২–৩ দিন পরে আবার WhatsApp করুন।\n"
        f"  <i>(WhatsApp those who didn't reply after 2-3 days.)</i>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>টিপস (Tips):</b>\n"
        f"  • প্রতিদিন ১০–২০ outreach করুন।\n"
        f"  • Grade A লিড থেকে শুরু করুন।\n"
        f"  • Close rate ৫% হলেও মাসে ৩–৬ clients সম্ভব।\n"
        f"  • সব লিড: <code>tracking/leads.csv</code>\n\n"
        f"🔄 Next run: tomorrow (auto-scheduled if --loop used)"
    )
    return message


# ─── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(args: argparse.Namespace) -> bool:
    """
    Execute the full free-mode pipeline.

    Steps:
      1. Run lead research (run_research.py)
      2. Generate report (generate_report.py)
      3. Build summary + send Telegram message
      4. Attach leads CSV and report to Telegram

    Returns True on success, False on failure.
    """
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    niche: str = args.niche
    location: str = args.location
    count: int = args.count
    skip_scrape: bool = args.skip_scrape

    print(f"\n🚀 Free Mode Pipeline Starting — {run_date}")
    print(f"   Niche: {niche} | Location: {location} | Count: {count}")
    print(
        f"   Telegram: {'✅ configured' if TELEGRAM_BOT_TOKEN else '⚠️  not configured'}\n"
    )

    # ── Step 1: Research ──────────────────────────────────────────────────────
    print("📡 Step 1/3: Running lead research...")
    success, leads_path = run_research(niche, location, count, skip_scrape)
    if not success:
        err_msg = (
            f"❌ <b>Free Mode — Research Failed</b>\n"
            f"📅 {run_date}\n"
            f"Niche: {niche} | Location: {location}\n\n"
            f"Check <code>logs/free_mode.log</code> for details."
        )
        send_telegram_message(err_msg)
        return False
    print(f"   ✅ Leads saved to: {leads_path}")

    # ── Step 2: Report ────────────────────────────────────────────────────────
    print("📊 Step 2/3: Generating report...")
    _, report_path = generate_report()

    # ── Step 3: Telegram notification ─────────────────────────────────────────
    print("📬 Step 3/3: Sending Telegram notification...")
    summary = load_leads_summary(leads_path)
    message = build_telegram_message(niche, location, summary, run_date)
    msg_sent = send_telegram_message(message)
    if msg_sent:
        print("   ✅ Telegram message sent")
    else:
        print("   ⚠️  Telegram message not sent (check TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")

    # Attach leads CSV
    if Path(leads_path).exists():
        if send_telegram_document(leads_path, caption=f"📊 Leads CSV — {run_date}"):
            print("   ✅ Leads CSV sent to Telegram")

    # Attach report (if generated successfully)
    if Path(report_path).exists():
        send_telegram_document(report_path, caption=f"📈 Weekly Report — {run_date}")

    # ── Local summary printout ─────────────────────────────────────────────────
    print(f"\n{'=' * 50}")
    print("✅ Pipeline complete!")
    print(f"   Total leads: {summary['total']}")
    print(f"   Grade A: {summary['grade_a']} | Grade B: {summary['grade_b']}")
    print(f"   Leads file: {leads_path}")
    print("   Logs: logs/free_mode.log")
    print(f"{'=' * 50}\n")

    return True


# ─── Entrypoint ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Free Mode — no-API lead research + Telegram notifications "
            "(Termux / Android friendly)"
        )
    )
    parser.add_argument(
        "--niche",
        default="dentist",
        help="Business niche to research (default: dentist)",
    )
    parser.add_argument(
        "--location",
        default="New York, NY",
        help='Location to search in (default: "New York, NY")',
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Max leads to find per run (default: 50)",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip website scraping — faster and recommended for phone",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run as a daily scheduler loop (instead of running once)",
    )
    parser.add_argument(
        "--time",
        default="09:00",
        metavar="HH:MM",
        help="Time to run the daily job in HH:MM format (default: 09:00)",
    )
    args = parser.parse_args()

    if args.loop:
        # ── Scheduler loop mode ───────────────────────────────────────────────
        if _schedule is None:
            print("❌ 'schedule' library not installed. Run: pip install schedule")
            sys.exit(1)
        print(f"⏰ Scheduler mode: will run daily at {args.time}")
        print("   Press Ctrl+C to stop.\n")

        # Run immediately on startup so the user gets first results right away
        run_pipeline(args)

        # Schedule subsequent daily runs
        _schedule.every().day.at(args.time).do(run_pipeline, args)

        try:
            while True:
                _schedule.run_pending()
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n⛔ Scheduler stopped by user.")
    else:
        # ── Run-once mode ─────────────────────────────────────────────────────
        success = run_pipeline(args)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
