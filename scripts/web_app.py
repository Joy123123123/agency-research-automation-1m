#!/usr/bin/env python3
"""
Agency Research Automation — Mobile Web App
Owner: Md Jamil Islam
Goal: মোবাইল browser-এ সব tools একসাথে, auto-run, Bengali UI

Usage (Replit / Termux / PC):
    pip install flask
    python scripts/web_app.py
    → Browser: http://localhost:5000

Features:
    - 📱 Mobile-responsive dark UI (Bootstrap 5 CDN)
    - 🏠 Dashboard — today's tasks, progress, reminders
    - 🔍 Research Tool — niche/location picker, auto-runs run_research.py
    - 📧 Outreach Tool — dry-run + live send, auto-runs send_outreach.py
    - 👥 Lead Manager — view/filter all leads from CSV
    - 📊 Report Generator — weekly/monthly, auto-runs generate_report.py
    - 🤖 AI Assistant — API-free, Bengali-first intelligent guide
    - ⚡ Real-time terminal output (Server-Sent Events)
    - 💾 Progress tracking with resume (tracking/app_progress.json)
    - 🔔 Reminder: pending daily tasks shown on dashboard
"""

from __future__ import annotations

import csv
import json
import logging
import os
import queue
import subprocess
import sys
import threading
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Generator

# ── Bootstrap Flask (friendly error if missing) ──────────────────────────────
try:
    from flask import (
        Flask, Response, jsonify, redirect,
        render_template_string, request, session, url_for,
    )
except ImportError:
    print("\n❌  Flask পাওয়া যায়নি। ইনস্টল করুন:\n    pip install flask\n")
    sys.exit(1)

# ── AI Assistant (local, no external API) ────────────────────────────────────
# Dynamically import so the app still works even if the file is missing
try:
    _scripts_dir = Path(__file__).parent
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from ai_assistant import AgencyAI  # type: ignore[import]
    _AI_AVAILABLE = True
except ImportError:
    _AI_AVAILABLE = False
    AgencyAI = None  # type: ignore[assignment,misc]

# ── Allowed values (input validation) ────────────────────────────────────────
ALLOWED_NICHES = {
    "restaurant", "dentist", "lawyer", "real estate", "gym",
    "salon", "hotel", "pharmacy", "plumber", "electrician",
}
ALLOWED_LOCATIONS = {
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX",
    "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA",
    "Dallas, TX", "Miami, FL",
}
ALLOWED_CAMPAIGNS = {"initial", "follow_up"}
ALLOWED_PERIODS = {"weekly", "monthly"}
ALLOWED_FORMATS = {"html", "json", "csv"}

# Research count bounds
MIN_LEAD_COUNT = 1
MAX_LEAD_COUNT = 500
DEFAULT_LEAD_COUNT = 50

# Outreach daily limit bounds
MIN_EMAIL_LIMIT = 1
MAX_EMAIL_LIMIT = 200
DEFAULT_EMAIL_LIMIT = 50
BASE_DIR = Path(__file__).parent.parent
TRACKING_DIR = BASE_DIR / "tracking"
PROGRESS_FILE = TRACKING_DIR / "app_progress.json"
LEADS_FILE = TRACKING_DIR / "leads.csv"
REPORTS_DIR = BASE_DIR / "data" / "reports"

TRACKING_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# ── Global job output queue ───────────────────────────────────────────────────
_job_output: queue.Queue[str] = queue.Queue()
_job_running = threading.Event()

# ── Per-session AI instances (keyed by session ID) ───────────────────────────
_ai_instances: dict[str, "AgencyAI"] = {}
_ai_lock = threading.Lock()


def get_ai() -> "AgencyAI | None":
    """Return or create an AgencyAI instance for the current session."""
    if not _AI_AVAILABLE or AgencyAI is None:
        return None
    sid = session.get("_id")
    if not sid:
        import secrets
        sid = secrets.token_hex(16)
        session["_id"] = sid
    with _ai_lock:
        if sid not in _ai_instances:
            _ai_instances[sid] = AgencyAI(BASE_DIR)
        return _ai_instances[sid]


# ═════════════════════════════════════════════════════════════════════════════
# Progress helpers
# ═════════════════════════════════════════════════════════════════════════════

def load_progress() -> dict[str, Any]:
    """Load saved progress from JSON."""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_progress(data: dict[str, Any]) -> None:
    """Persist progress to JSON."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def mark_done(task_id: str) -> None:
    """Mark a task as done today."""
    progress = load_progress()
    today = date.today().isoformat()
    progress[task_id] = {
        "done": True,
        "last_done": today,
        "done_count": progress.get(task_id, {}).get("done_count", 0) + 1,
    }
    save_progress(progress)


def mark_undone(task_id: str) -> None:
    """Un-mark a task."""
    progress = load_progress()
    if task_id in progress:
        progress[task_id]["done"] = False
    save_progress(progress)


def is_done(task_id: str, freq: str) -> bool:
    """Return True if this task is considered done."""
    progress = load_progress()
    record = progress.get(task_id, {})
    if not record.get("done"):
        return False
    if freq == "daily":
        return record.get("last_done", "") == date.today().isoformat()
    return True  # once / weekly / monthly


# ═════════════════════════════════════════════════════════════════════════════
# Task & Section definitions
# ═════════════════════════════════════════════════════════════════════════════

SECTIONS: list[dict[str, Any]] = [
    {
        "id": "setup",
        "icon": "⚙️",
        "title": "প্রথম সেটআপ",
        "color": "#6c757d",
        "desc": "একবারই করতে হবে",
        "tasks": [
            {
                "id": "setup_venv",
                "title": "Virtual Environment তৈরি",
                "freq": "once",
                "guide": "Python Virtual Environment তৈরি করো:\n\npython -m venv venv\nsource venv/bin/activate  # Linux/Mac/Termux\nvenv\\Scripts\\activate      # Windows\n\nTermux-এ:\npkg install python\npip install virtualenv\nvirtualenv venv && source venv/bin/activate",
                "script": None,
                "tool_link": None,
            },
            {
                "id": "setup_deps",
                "title": "Dependencies Install",
                "freq": "once",
                "guide": "requirements.txt থেকে সব library install করো:\n\npip install flask\npip install -r requirements.txt",
                "script": "pip install flask && pip install -r requirements.txt",
                "tool_link": None,
            },
            {
                "id": "setup_apikeys",
                "title": "API কী সেটআপ",
                "freq": "once",
                "guide": (
                    "config/api_keys.env ফাইলে API কী দাও:\n\n"
                    "OPENAI_API_KEY=your_key\n"
                    "GOOGLE_API_KEY=your_key\n"
                    "SENDGRID_API_KEY=your_key\n"
                    "AIRTABLE_API_KEY=your_key\n\n"
                    "কোথায় পাবে:\n"
                    "• OpenAI: platform.openai.com\n"
                    "• Google: console.cloud.google.com (Places API)\n"
                    "• SendGrid: sendgrid.com (free 100/day)\n"
                    "• Airtable: airtable.com/create/tokens"
                ),
                "script": None,
                "tool_link": None,
            },
            {
                "id": "setup_dirs",
                "title": "Folders তৈরি",
                "freq": "once",
                "guide": "logs/ এবং data/reports/ folder তৈরি করো।",
                "script": "mkdir -p logs data/reports && echo 'Folders ready!'",
                "tool_link": None,
            },
        ],
    },
    {
        "id": "morning",
        "icon": "🌅",
        "title": "সকালের কাজ",
        "color": "#fd7e14",
        "desc": "9:00–10:00 AM — প্রতিদিন",
        "tasks": [
            {
                "id": "morning_research",
                "title": "নতুন লিড রিসার্চ",
                "freq": "daily",
                "guide": "Google Maps API দিয়ে নতুন লিড খোঁজো। নিচের Research Tool বাটন চাপো।",
                "script": None,
                "tool_link": "/research",
            },
            {
                "id": "morning_inbox",
                "title": "Inbox চেক করো",
                "freq": "daily",
                "guide": (
                    "আউটরিচ পাঠানো ইমেইলের inbox দেখো:\n"
                    "• Gmail: gmail.com\n"
                    "• SendGrid Stats: app.sendgrid.com/statistics\n\n"
                    "কেউ reply করলে:\n"
                    "✅ আগ্রহী → call schedule করো\n"
                    "❌ Unsubscribe → leads.csv update করো"
                ),
                "script": None,
                "tool_link": None,
            },
            {
                "id": "morning_review",
                "title": "Lead List Review",
                "freq": "daily",
                "guide": "আজকের নতুন lead গুলো দেখো — grade A/B leads-এ focus করো।",
                "script": None,
                "tool_link": "/leads",
            },
        ],
    },
    {
        "id": "outreach",
        "icon": "📧",
        "title": "আউটরিচ",
        "color": "#0d6efd",
        "desc": "10:00–11:00 AM — ইমেইল পাঠাও",
        "tasks": [
            {
                "id": "outreach_initial",
                "title": "Initial Email পাঠাও",
                "freq": "daily",
                "guide": (
                    "নতুন leads-দের প্রথম ইমেইল পাঠাও।\n\n"
                    "Outreach Tool:\n"
                    "• প্রথমে Dry Run করো (preview)\n"
                    "• ঠিক থাকলে Send করো\n"
                    "• প্রতিদিন limit: 200 ইমেইল"
                ),
                "script": None,
                "tool_link": "/outreach",
            },
            {
                "id": "outreach_followup",
                "title": "Follow-up পাঠাও",
                "freq": "daily",
                "guide": (
                    "আগে ইমেইল পাঠানো হয়েছে কিন্তু reply নেই — তাদের follow-up দাও।\n\n"
                    "• 1st follow-up: 3 দিন পর\n"
                    "• 2nd follow-up: 7 দিন পর\n"
                    "• 3rd follow-up: 14 দিন পর"
                ),
                "script": None,
                "tool_link": "/outreach",
            },
        ],
    },
    {
        "id": "analytics",
        "icon": "📊",
        "title": "Analytics",
        "color": "#198754",
        "desc": "11:00 AM–12:00 PM — Performance",
        "tasks": [
            {
                "id": "analytics_stats",
                "title": "Lead Stats দেখো",
                "freq": "daily",
                "guide": "আজকের lead performance দেখো।",
                "script": None,
                "tool_link": "/leads",
            },
            {
                "id": "analytics_sendgrid",
                "title": "Email Stats চেক করো",
                "freq": "daily",
                "guide": (
                    "SendGrid: app.sendgrid.com/statistics\n\n"
                    "Good benchmark:\n"
                    "• Open rate > 30% ✅\n"
                    "• Reply rate > 5% ✅\n"
                    "• Click rate > 10% ✅"
                ),
                "script": None,
                "tool_link": None,
            },
            {
                "id": "analytics_update",
                "title": "Lead Status আপডেট",
                "freq": "daily",
                "guide": "leads.csv-এ status আপডেট করো:\nnew → contacted → replied → interested → converted",
                "script": None,
                "tool_link": "/leads",
            },
        ],
    },
    {
        "id": "followup",
        "icon": "🔄",
        "title": "বিকেলের Follow-up",
        "color": "#6f42c1",
        "desc": "3:00–4:00 PM — Reply manage করো",
        "tasks": [
            {
                "id": "followup_replies",
                "title": "Reply-দের উত্তর দাও",
                "freq": "daily",
                "guide": (
                    "আজকের replies:\n"
                    "1. আগ্রহী lead-দের ব্যক্তিগতভাবে reply করো\n"
                    "2. 15 মিনিট discovery call offer করো\n"
                    "3. Calendly link দাও: calendly.com (free)\n\n"
                    "Script:\n'ধন্যবাদ reply করার জন্য! আপনার business-এর\n"
                    "জন্য specific ideas আছে। ১৫ মিনিট কথা বলবেন?'"
                ),
                "script": None,
                "tool_link": None,
            },
            {
                "id": "followup_crm",
                "title": "CRM/Airtable Update",
                "freq": "daily",
                "guide": (
                    "প্রতিটি lead-এর latest status update করো:\n\n"
                    "Airtable: airtable.com → Import leads.csv\n"
                    "অথবা সরাসরি leads.csv edit করো।"
                ),
                "script": None,
                "tool_link": "/leads",
            },
        ],
    },
    {
        "id": "weekly",
        "icon": "📅",
        "title": "সাপ্তাহিক কাজ",
        "color": "#dc3545",
        "desc": "প্রতি সোমবার",
        "tasks": [
            {
                "id": "weekly_report",
                "title": "Weekly Report তৈরি",
                "freq": "weekly",
                "guide": "গত সপ্তাহের performance summary report তৈরি করো।",
                "script": None,
                "tool_link": "/reports",
            },
            {
                "id": "weekly_a_leads",
                "title": "A-Grade Leads Review",
                "freq": "weekly",
                "guide": (
                    "Grade A lead যারা reply করেনি তাদের:\n"
                    "1. LinkedIn-এ connect করো\n"
                    "2. ভিন্ন subject line দিয়ে ইমেইল করো\n"
                    "3. Social media-তে engage করো"
                ),
                "script": None,
                "tool_link": "/leads",
            },
            {
                "id": "weekly_niche",
                "title": "নতুন Niche Research",
                "freq": "weekly",
                "guide": "নতুন niche/location-এ research চালাও।",
                "script": None,
                "tool_link": "/research",
            },
            {
                "id": "weekly_backup",
                "title": "Data Backup",
                "freq": "weekly",
                "guide": (
                    "tracking/ data backup করো:\n"
                    "cp -r tracking/ tracking_backup_$(date +%Y%m%d)/\n\n"
                    "অথবা Google Drive-এ leads.csv upload করো।"
                ),
                "script": None,
                "tool_link": None,
            },
        ],
    },
    {
        "id": "monthly",
        "icon": "📆",
        "title": "মাসিক কাজ",
        "color": "#20c997",
        "desc": "প্রতি মাসের শেষে",
        "tasks": [
            {
                "id": "monthly_revenue",
                "title": "Revenue Review",
                "freq": "monthly",
                "guide": (
                    "Revenue vs Target check করো.\n\n"
                    "Year 1 targets:\n"
                    "মাস ১-৩: $10,000–$20,000\n"
                    "মাস ৪-৬: $30,000–$50,000\n"
                    "মাস ৭-৯: $60,000–$80,000\n"
                    "মাস ১০-১২: $90,000–$100,000"
                ),
                "script": None,
                "tool_link": "/reports",
            },
            {
                "id": "monthly_templates",
                "title": "Email Template Optimize",
                "freq": "monthly",
                "guide": (
                    "সবচেয়ে ভালো performing template-এর pattern বের করো:\n"
                    "• Subject line A/B test\n"
                    "• Email length optimize\n"
                    "• CTA পরিবর্তন\n\n"
                    "Templates: templates/ folder"
                ),
                "script": None,
                "tool_link": None,
            },
            {
                "id": "monthly_scoring",
                "title": "Lead Scoring Update",
                "freq": "monthly",
                "guide": (
                    "কোন ধরনের lead বেশি convert হচ্ছে দেখে scoring criteria আপডেট করো.\n"
                    "File: src/ai/lead_scorer.py"
                ),
                "script": None,
                "tool_link": None,
            },
            {
                "id": "monthly_plan",
                "title": "পরের মাসের Plan",
                "freq": "monthly",
                "guide": (
                    "পরের মাসের target:\n"
                    "□ কতটি lead? (50–500/সপ্তাহ)\n"
                    "□ কোন niche focus?\n"
                    "□ কোন location expand?\n"
                    "□ নতুন service add?\n"
                    "□ Budget কত?"
                ),
                "script": None,
                "tool_link": None,
            },
        ],
    },
]


# ── Helper functions ──────────────────────────────────────────────────────────

def all_tasks() -> list[dict[str, Any]]:
    """Flatten all tasks with section info injected."""
    result = []
    for sec in SECTIONS:
        for task in sec["tasks"]:
            result.append({**task, "section_id": sec["id"], "section_title": sec["title"]})
    return result


def get_task(task_id: str) -> dict[str, Any] | None:
    """Find a task by ID."""
    for t in all_tasks():
        if t["id"] == task_id:
            return t
    return None


def pending_today() -> list[dict[str, Any]]:
    """Tasks not yet done for today."""
    today = date.today().isoformat()
    progress = load_progress()
    pending = []
    for task in all_tasks():
        freq = task["freq"]
        rec = progress.get(task["id"], {})
        if freq == "once":
            if not rec.get("done"):
                pending.append(task)
        elif freq == "daily":
            if rec.get("last_done", "") != today:
                pending.append(task)
    return pending


def section_progress(section: dict[str, Any]) -> dict[str, int]:
    """Return done/total count for a section."""
    total = len(section["tasks"])
    done = sum(1 for t in section["tasks"] if is_done(t["id"], t["freq"]))
    return {"done": done, "total": total}


# ── Lead helpers ──────────────────────────────────────────────────────────────

def load_leads() -> list[dict[str, str]]:
    """Load leads from CSV, skipping comment lines."""
    if not LEADS_FILE.exists():
        return []
    try:
        with open(LEADS_FILE, encoding="utf-8") as f:
            # Skip lines starting with '#' (comment lines in the CSV)
            lines = [ln for ln in f if not ln.startswith("#")]
        rows = list(csv.DictReader(lines))
        # Filter out rows where the key is None (malformed rows)
        return [
            {k: (v or "") for k, v in row.items() if k is not None}
            for row in rows
        ]
    except (OSError, csv.Error):
        return []


def lead_stats(leads: list[dict[str, str]]) -> dict[str, Any]:
    """Compute summary stats for leads."""
    if not leads:
        return {
            "total": 0, "new": 0, "contacted": 0, "replied": 0,
            "converted": 0, "grade_a": 0, "grade_b": 0, "reply_rate": 0.0,
        }
    status_counts = Counter(r.get("status", "new") for r in leads)
    grade_counts = Counter(r.get("grade", "") for r in leads)
    contacted = status_counts.get("contacted", 0) + status_counts.get("replied", 0)
    replied = status_counts.get("replied", 0)
    reply_rate = round((replied / max(contacted, 1)) * 100, 1)
    return {
        "total": len(leads),
        "new": status_counts.get("new", 0),
        "contacted": status_counts.get("contacted", 0),
        "replied": replied,
        "converted": status_counts.get("converted", 0),
        "grade_a": grade_counts.get("A", 0),
        "grade_b": grade_counts.get("B", 0),
        "reply_rate": reply_rate,
    }


# ── Script runner (SSE) ───────────────────────────────────────────────────────

def _run_script(cmd: str, cwd: str) -> None:
    """Run *cmd* in background; push output lines to _job_output."""
    _job_running.set()
    try:
        proc = subprocess.Popen(  # noqa: S603
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:  # type: ignore[union-attr]
            _job_output.put(line.rstrip())
        proc.wait()
        _job_output.put(f"__EXIT__{proc.returncode}")
    except Exception as exc:  # noqa: BLE001
        _job_output.put(f"ERROR: {exc}")
        _job_output.put("__EXIT__1")
    finally:
        _job_running.clear()


def stream_job(cmd: str) -> Generator[str, None, None]:
    """Generator: yield SSE data lines for a shell command."""
    import time

    if _job_running.is_set():
        yield "data: ⚠️ আরেকটি task চলছে। একটু অপেক্ষা করুন।\n\n"
        yield "data: __DONE__\n\n"
        return

    # Drain stale queue entries
    while not _job_output.empty():
        try:
            _job_output.get_nowait()
        except queue.Empty:
            break

    thread = threading.Thread(target=_run_script, args=(cmd, str(BASE_DIR)), daemon=True)
    thread.start()

    while True:
        try:
            line = _job_output.get(timeout=30)
            if line.startswith("__EXIT__"):
                code = line.split("__EXIT__")[1]
                yield "data: \n\n"
                if code == "0":
                    yield "data: ✅ সম্পন্ন হয়েছে!\n\n"
                else:
                    yield f"data: ⚠️ Completed (exit code: {code})\n\n"
                yield "data: __DONE__\n\n"
                break
            else:
                escaped = line.replace("\\", "\\\\")
                yield f"data: {escaped}\n\n"
        except queue.Empty:
            yield "data: (timeout — process may still be running)\n\n"
            yield "data: __DONE__\n\n"
            break
        time.sleep(0.01)


# ═════════════════════════════════════════════════════════════════════════════
# Shared CSS / JS (injected into every page)
# ═════════════════════════════════════════════════════════════════════════════

COMMON_HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="theme-color" content="#0a0e1a">
<title>Agency App — Md Jamil Islam</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
:root{--bg:#0a0e1a;--card:#131929;--border:#1e2a40;--accent:#4f8ef7;
  --success:#2ecc71;--warn:#f39c12;--danger:#e74c3c;--text:#e8ecf1;--muted:#6c8099;}
*{box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;
  padding-bottom:80px;font-size:15px;}
.app-header{background:linear-gradient(135deg,#0d1b2e,#1a2f4e);padding:14px 16px;
  border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;}
.app-header h1{font-size:1.05rem;margin:0;color:var(--accent);font-weight:700;}
.app-header small{color:var(--muted);font-size:0.72rem;}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;margin-bottom:12px;}
.card-header{padding:13px 15px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;}
.card-body{padding:15px;}
.btn{border-radius:8px;font-weight:600;font-size:0.88rem;padding:10px 18px;
  border:none;cursor:pointer;transition:all .2s;display:inline-block;text-align:center;}
.btn-primary{background:var(--accent);color:#fff;}
.btn-primary:hover{background:#3a7de5;color:#fff;}
.btn-success{background:var(--success);color:#fff;}
.btn-warning{background:var(--warn);color:#1a1a1a;}
.btn-danger{background:var(--danger);color:#fff;}
.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text);}
.btn-outline:hover{background:var(--border);}
.btn-sm{padding:5px 12px;font-size:0.78rem;}
.w-100{width:100%;}
.badge-c{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.72rem;font-weight:700;}
.bg-done{background:rgba(46,204,113,.18);color:var(--success);}
.bg-pend{background:rgba(243,156,.18);color:var(--warn);}
.bg-once{background:rgba(108,128,153,.18);color:var(--muted);}
.bg-daily{background:rgba(79,142,247,.18);color:var(--accent);}
.bg-weekly{background:rgba(231,76,60,.18);color:var(--danger);}
.bg-monthly{background:rgba(46,204,113,.18);color:var(--success);}
.pb{background:var(--border);border-radius:6px;height:8px;overflow:hidden;}
.pb-inner{background:var(--accent);height:100%;border-radius:6px;transition:width .4s;}
.stat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;}
.stat-box{background:#0d1525;border:1px solid var(--border);border-radius:10px;
  padding:13px;text-align:center;}
.stat-num{font-size:1.75rem;font-weight:800;color:var(--accent);}
.stat-lbl{font-size:.72rem;color:var(--muted);margin-top:2px;}
.task-row{display:flex;align-items:flex-start;gap:11px;padding:11px 0;
  border-bottom:1px solid var(--border);cursor:pointer;}
.task-row:last-child{border-bottom:none;}
.task-check{width:22px;height:22px;min-width:22px;border-radius:50%;
  border:2px solid var(--border);display:flex;align-items:center;
  justify-content:center;font-size:.68rem;margin-top:1px;}
.task-check.done{background:var(--success);border-color:var(--success);color:#fff;}
.task-title{font-weight:600;font-size:.88rem;margin-bottom:3px;}
.task-meta{font-size:.72rem;color:var(--muted);}
.terminal{background:#030810;border:1px solid var(--border);border-radius:8px;
  padding:13px;font-family:'Courier New',monospace;font-size:.78rem;color:#7ecb7e;
  min-height:110px;max-height:340px;overflow-y:auto;white-space:pre-wrap;word-break:break-word;}
.form-lbl{font-size:.82rem;color:var(--muted);margin-bottom:5px;}
.form-ctrl,.form-sel{background:#0d1525;border:1px solid var(--border);color:var(--text);
  border-radius:8px;padding:9px 13px;font-size:.88rem;width:100%;margin-bottom:12px;}
.form-ctrl:focus,.form-sel:focus{outline:none;border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(79,142,247,.2);}
.form-sel option{background:#131929;}
.nav-bot{position:fixed;bottom:0;left:0;right:0;background:#0d1525;
  border-top:1px solid var(--border);display:flex;z-index:200;}
.nav-it{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:9px 3px;color:var(--muted);text-decoration:none;font-size:.62rem;
  transition:all .2s;border:none;background:none;cursor:pointer;}
.nav-it.on,.nav-it:hover{color:var(--accent);}
.nav-it i{font-size:1.25rem;margin-bottom:2px;}
.reminder-box{background:rgba(243,156,18,.1);border:1px solid rgba(243,156,18,.3);
  border-radius:10px;padding:12px 15px;margin-bottom:12px;}
.all-done-box{background:rgba(46,204,113,.1);border:1px solid rgba(46,204,113,.3);
  border-radius:10px;padding:12px 15px;margin-bottom:12px;}
.guide-box{background:#050c1a;border-left:3px solid var(--accent);border-radius:6px;
  padding:13px;font-size:.83rem;color:#aec6e8;white-space:pre-wrap;
  word-break:break-word;line-height:1.75;}
.toggle-row{display:flex;align-items:center;gap:10px;margin-bottom:13px;}
.switch{position:relative;display:inline-block;width:44px;height:24px;}
.switch input{opacity:0;width:0;height:0;}
.slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;
  background:var(--border);transition:.4s;border-radius:24px;}
.slider:before{position:absolute;content:"";height:18px;width:18px;left:3px;bottom:3px;
  background:#fff;transition:.4s;border-radius:50%;}
input:checked+.slider{background:var(--success);}
input:checked+.slider:before{transform:translateX(20px);}
.table-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:.78rem;}
th{background:#0d1525;padding:9px 11px;text-align:left;color:var(--muted);
  font-weight:600;border-bottom:2px solid var(--border);}
td{padding:9px 11px;border-bottom:1px solid var(--border);color:var(--text);}
tr:hover td{background:rgba(255,255,255,.02);}
.ga{color:#2ecc71;font-weight:700;} .gb{color:#3498db;font-weight:700;}
.gc{color:#f39c12;} .gd{color:#e74c3c;}
.s-new{color:var(--muted);} .s-cont{color:var(--accent);}
.s-repl{color:var(--warn);} .s-conv{color:var(--success);}
.page{padding:13px;}
.page-title{font-size:1.15rem;font-weight:700;margin-bottom:15px;}
a{color:var(--accent);text-decoration:none;}
a:hover{color:#7ab3ff;}
.warn-box{background:rgba(243,156,18,.1);border-radius:8px;padding:10px 13px;
  margin-bottom:14px;font-size:.8rem;color:var(--warn);}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
/* ── AI Chat styles ────────────────────────────────────────────────────── */
.chat-wrap{display:flex;flex-direction:column;height:calc(100vh - 180px);min-height:300px;}
.chat-msgs{flex:1;overflow-y:auto;padding:10px 0;display:flex;flex-direction:column;gap:10px;}
.msg{max-width:88%;padding:11px 14px;border-radius:14px;font-size:.85rem;line-height:1.65;
  word-break:break-word;}
.msg-ai{background:#0d1f35;border:1px solid var(--border);align-self:flex-start;
  border-bottom-left-radius:4px;color:var(--text);}
.msg-user{background:var(--accent);color:#fff;align-self:flex-end;
  border-bottom-right-radius:4px;}
.msg-ai h1,.msg-ai h2,.msg-ai h3{font-size:.95rem;color:var(--accent);
  margin-top:10px;margin-bottom:5px;font-weight:700;}
.msg-ai h1:first-child,.msg-ai h2:first-child{margin-top:0;}
.msg-ai ul,.msg-ai ol{padding-left:18px;margin:5px 0;}
.msg-ai li{margin-bottom:3px;}
.msg-ai code{background:#05111f;padding:1px 5px;border-radius:4px;
  font-family:monospace;font-size:.82rem;color:#7ecb7e;}
.msg-ai pre{background:#05111f;padding:10px;border-radius:7px;
  overflow-x:auto;font-size:.78rem;color:#7ecb7e;margin:7px 0;}
.msg-ai pre code{background:none;padding:0;}
.msg-ai table{font-size:.78rem;margin:7px 0;}
.msg-ai strong{color:#c8d8f0;}
.msg-ai em{color:var(--muted);}
.msg-ai hr{border-color:var(--border);margin:8px 0;}
.msg-ai blockquote{border-left:3px solid var(--accent);padding-left:10px;
  color:var(--muted);margin:5px 0;}
.quick-btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}
.quick-btn{background:#0d1525;border:1px solid var(--border);color:var(--text);
  border-radius:20px;padding:5px 12px;font-size:.75rem;cursor:pointer;
  transition:all .15s;white-space:nowrap;}
.quick-btn:hover,.quick-btn:active{background:var(--accent);border-color:var(--accent);color:#fff;}
.quick-btn.goto{background:rgba(79,142,247,.15);border-color:var(--accent);color:var(--accent);}
.chat-input-row{display:flex;gap:8px;padding:10px 0 5px;}
.chat-input{flex:1;background:#0d1525;border:1px solid var(--border);color:var(--text);
  border-radius:24px;padding:10px 16px;font-size:.9rem;outline:none;resize:none;
  font-family:inherit;max-height:110px;overflow-y:auto;}
.chat-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(79,142,247,.15);}
.send-btn{background:var(--accent);border:none;color:#fff;width:44px;height:44px;
  border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;flex-shrink:0;transition:all .2s;}
.send-btn:hover{background:#3a7de5;}
.typing-dot{display:inline-block;width:6px;height:6px;background:var(--muted);
  border-radius:50%;animation:blink 1.2s infinite;margin:0 2px;}
.typing-dot:nth-child(2){animation-delay:.2s;}
.typing-dot:nth-child(3){animation-delay:.4s;}
@keyframes blink{0%,80%,100%{opacity:.2;}40%{opacity:1;}}
@media(max-width:380px){.stat-num{font-size:1.35rem;}body{font-size:14px;}}
</style>
"""

COMMON_SCRIPTS = """
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
/* ── SSE stream runner ─────────────────────────────────────────────────── */
function runStream(url, termId, onDone) {
  var term = document.getElementById(termId);
  if (!term) return;
  term.textContent = '⏳ চালু হচ্ছে...\\n';
  var es = new EventSource(url);
  es.onmessage = function(e) {
    if (e.data === '__DONE__') { es.close(); if (onDone) onDone(); return; }
    term.textContent += e.data + '\\n';
    term.scrollTop = term.scrollHeight;
  };
  es.onerror = function() { es.close(); term.textContent += '\\n❌ Connection error.\\n'; };
}
function markTask(taskId, done) {
  fetch('/api/task/' + taskId + '/' + (done ? 'done' : 'undone'), {method:'POST'})
    .then(function() { location.reload(); });
}
function toggleSection(id) {
  var el = document.getElementById(id);
  el.style.display = (el.style.display === 'none' || el.style.display === '') ? 'block' : 'none';
}

/* ── Lightweight Markdown → HTML renderer (no external lib needed) ──── */
function mdToHtml(md) {
  if (!md) return '';
  var s = md;
  // Fenced code blocks
  s = s.replace(/```([\\s\\S]*?)```/g, function(_, c) {
    return '<pre><code>' + escHtml(c.trim()) + '</code></pre>';
  });
  // Inline code
  s = s.replace(/`([^`]+)`/g, function(_, c) { return '<code>' + escHtml(c) + '</code>'; });
  // Headers (## and ###)
  s = s.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  s = s.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  s = s.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Bold and italic
  s = s.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
  s = s.replace(/\\_(.+?)\\_/g, '<em>$1</em>');
  s = s.replace(/\\*([^*]+)\\*/g, '<em>$1</em>');
  // HR
  s = s.replace(/^---$/gm, '<hr>');
  // Tables (simple)
  s = s.replace(/\\|(.+)\\|/g, function(line) {
    var cells = line.split('|').slice(1,-1).map(function(c){ return c.trim(); });
    return '<tr>' + cells.map(function(c){
      return /^[-:]+$/.test(c) ? '' : '<td>' + c + '</td>';
    }).join('') + '</tr>';
  });
  s = s.replace(/(<tr>.*<\\/tr>\\n?)+/g, function(t) {
    return '<table>' + t + '</table>';
  });
  // Unordered lists
  s = s.replace(/(^[\\-\\*] .+\\n?)+/gm, function(block) {
    var items = block.trim().split('\\n').map(function(ln) {
      return '<li>' + ln.replace(/^[\\-\\*] /, '') + '</li>';
    }).join('');
    return '<ul>' + items + '</ul>';
  });
  // Ordered lists
  s = s.replace(/(^\\d+\\. .+\\n?)+/gm, function(block) {
    var items = block.trim().split('\\n').map(function(ln) {
      return '<li>' + ln.replace(/^\\d+\\. /, '') + '</li>';
    }).join('');
    return '<ol>' + items + '</ol>';
  });
  // Blockquote
  s = s.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  // Paragraphs (double newline)
  s = s.replace(/\\n\\n+/g, '</p><p>');
  // Single newlines (inside paragraph)
  s = s.replace(/\\n/g, '<br>');
  return '<p>' + s + '</p>';
}
function escHtml(t) {
  return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
</script>
"""


def nav_html(active: str) -> str:
    """Render the bottom navigation bar."""
    pages = [
        ("home", "/", "fa-home", "হোম"),
        ("research", "/research", "fa-search", "রিসার্চ"),
        ("ai", "/ai", "fa-robot", "AI"),
        ("leads", "/leads", "fa-users", "লিডস"),
        ("reports", "/reports", "fa-chart-bar", "রিপোর্ট"),
    ]
    items = "".join(
        f'<a href="{href}" class="nav-it {"on" if pid == active else ""}">'
        f'<i class="fas {icon}"></i><span>{label}</span></a>'
        for pid, href, icon, label in pages
    )
    return f'<nav class="nav-bot">{items}</nav>'


def header_html() -> str:
    """Render the top header bar."""
    now = datetime.now().strftime("%d %b, %I:%M %p")
    return (
        '<div class="app-header">'
        '<div style="display:flex;align-items:center;justify-content:space-between;">'
        '<div><h1>🚀 Agency App</h1>'
        '<small>Md Jamil Islam &nbsp;|&nbsp; Target: $1M/year</small></div>'
        f'<div style="text-align:right;font-size:.68rem;color:var(--muted)">{now}</div>'
        '</div></div>'
    )


def page(content: str, active_nav: str = "home", extra_scripts: str = "") -> str:
    """Wrap content in a complete HTML page."""
    return (
        f"<!DOCTYPE html><html lang='bn'><head>{COMMON_HEAD}</head><body>"
        f"{header_html()}"
        f"{content}"
        f"{nav_html(active_nav)}"
        f"{COMMON_SCRIPTS}"
        f"{extra_scripts}"
        f"</body></html>"
    )


# ═════════════════════════════════════════════════════════════════════════════
# Routes
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/")
def home() -> str:
    """Dashboard page."""
    leads = load_leads()
    stats = lead_stats(leads)
    pending = pending_today()

    total_tasks = sum(len(s["tasks"]) for s in SECTIONS)
    done_tasks = sum(1 for t in all_tasks() if is_done(t["id"], t["freq"]))
    overall_pct = round((done_tasks / max(total_tasks, 1)) * 100)

    sec_progress_map = {s["id"]: section_progress(s) for s in SECTIONS}
    task_done_map = {t["id"]: is_done(t["id"], t["freq"]) for t in all_tasks()}

    tpl = """
{% if pending_count > 0 %}
<div class="reminder-box">
  <i class="fas fa-bell" style="color:var(--warn)"></i>
  <strong> আজকের {{ pending_count }}টি কাজ বাকি!</strong>
  {% for t in pending_tasks[:3] %}
  <div style="font-size:.78rem;margin-top:4px;color:var(--muted)">
    ⬜ {{ t.title }}
    <span class="badge-c bg-once">{{ t.section_title }}</span>
  </div>
  {% endfor %}
  {% if pending_count > 3 %}
  <div style="font-size:.75rem;color:var(--muted);margin-top:4px">
    + আরও {{ pending_count - 3 }}টি...
  </div>
  {% endif %}
</div>
{% else %}
<div class="all-done-box">
  <i class="fas fa-check-circle" style="color:var(--success)"></i>
  <strong> আজকের সব কাজ শেষ! 🎉</strong>
</div>
{% endif %}

<div class="card">
  <div class="card-header">
    <span style="font-weight:700">📊 সামগ্রিক Progress</span>
    <span class="badge-c bg-done">{{ overall_done }}/{{ overall_total }}</span>
  </div>
  <div class="card-body">
    <div class="pb"><div class="pb-inner" style="width:{{ overall_pct }}%"></div></div>
    <div style="font-size:.72rem;color:var(--muted);margin-top:5px">{{ overall_pct }}% সম্পন্ন</div>
  </div>
</div>

<div class="stat-grid" style="margin-bottom:12px;">
  <div class="stat-box">
    <div class="stat-num">{{ stats.total }}</div>
    <div class="stat-lbl">মোট লিড</div>
  </div>
  <div class="stat-box">
    <div class="stat-num" style="color:var(--success)">{{ stats.converted }}</div>
    <div class="stat-lbl">Client হয়েছে 🎉</div>
  </div>
  <div class="stat-box">
    <div class="stat-num" style="color:#f39c12">{{ stats.replied }}</div>
    <div class="stat-lbl">Reply আসা</div>
  </div>
  <div class="stat-box">
    <div class="stat-num" style="color:var(--accent)">{{ stats.reply_rate }}%</div>
    <div class="stat-lbl">Reply Rate</div>
  </div>
</div>

<div class="card">
  <div class="card-header"><strong>⚡ Quick Actions</strong></div>
  <div class="card-body">
    <div class="grid2">
      <a href="/research" class="btn btn-primary">
        <i class="fas fa-search"></i> রিসার্চ
      </a>
      <a href="/outreach" class="btn btn-success">
        <i class="fas fa-paper-plane"></i> আউটরিচ
      </a>
      <a href="/leads" class="btn btn-outline">
        <i class="fas fa-users"></i> লিডস
      </a>
      <a href="/reports" class="btn btn-outline">
        <i class="fas fa-chart-bar"></i> রিপোর্ট
      </a>
    </div>
  </div>
</div>

<div class="page-title" style="margin-top:4px;">📋 সব Section</div>

{% for sec in sections %}
{% set prog = sec_progress[sec.id] %}
{% set pct = (prog.done / prog.total * 100)|int if prog.total > 0 else 0 %}
<div class="card">
  <div class="card-header"
       style="border-left:4px solid {{ sec.color }};cursor:pointer"
       onclick="toggleSection('s-{{ sec.id }}')">
    <div>
      <span style="font-size:1.15rem;margin-right:6px">{{ sec.icon }}</span>
      <strong>{{ sec.title }}</strong>
      <div style="font-size:.72rem;color:var(--muted)">{{ sec.desc }}</div>
    </div>
    <div style="text-align:right;min-width:60px">
      <div class="badge-c {% if prog.done == prog.total %}bg-done{% else %}bg-pend{% endif %}">
        {{ prog.done }}/{{ prog.total }}
      </div>
      <div class="pb" style="width:58px;margin-top:5px;">
        <div class="pb-inner" style="width:{{ pct }}%;background:{{ sec.color }}"></div>
      </div>
    </div>
  </div>
  <div id="s-{{ sec.id }}" style="display:none;">
    <div class="card-body" style="padding-top:8px;padding-bottom:8px;">
    {% for task in sec.tasks %}
    {% set done = task_done[task.id] %}
    <div class="task-row" onclick="location.href='/task/{{ task.id }}'">
      <div class="task-check {% if done %}done{% endif %}">
        {% if done %}<i class="fas fa-check" style="font-size:.62rem"></i>{% endif %}
      </div>
      <div style="flex:1">
        <div class="task-title">{{ task.title }}</div>
        <div class="task-meta">
          <span class="badge-c bg-{{ task.freq }}">{{ task.freq }}</span>
          {% if task.tool_link %}
          <a href="{{ task.tool_link }}" style="font-size:.72rem;margin-left:5px"
             onclick="event.stopPropagation()">
            <i class="fas fa-arrow-right"></i> Tool
          </a>
          {% endif %}
        </div>
      </div>
      <i class="fas fa-chevron-right"
         style="color:var(--muted);font-size:.72rem;margin-top:3px"></i>
    </div>
    {% endfor %}
    </div>
  </div>
</div>
{% endfor %}
"""
    content = render_template_string(
        f'<div class="page">{tpl}</div>',
        sections=SECTIONS,
        stats=stats,
        pending_count=len(pending),
        pending_tasks=pending,
        overall_done=done_tasks,
        overall_total=total_tasks,
        overall_pct=overall_pct,
        sec_progress=sec_progress_map,
        task_done=task_done_map,
    )
    return page(content, "home")


@app.route("/task/<task_id>")
def task_detail(task_id: str) -> str | Response:
    """Task detail page."""
    task = get_task(task_id)
    if not task:
        return redirect(url_for("home"))
    done = is_done(task_id, task["freq"])

    tpl = """
<a href="javascript:history.back()" style="font-size:.83rem;color:var(--muted)">
  <i class="fas fa-arrow-left"></i> পেছনে
</a>
<div style="margin-top:14px;margin-bottom:4px;">
  <div class="page-title" style="margin-bottom:4px;">{{ task.title }}</div>
  <span class="badge-c bg-{{ task.freq }}">{{ task.freq }}</span>
  <span class="badge-c bg-once" style="margin-left:5px;">{{ task.section_title }}</span>
  {% if done %}
  <span class="badge-c bg-done" style="margin-left:5px;">✅ সম্পন্ন</span>
  {% else %}
  <span class="badge-c bg-pend" style="margin-left:5px;">⬜ বাকি</span>
  {% endif %}
</div>

<div class="card" style="margin-top:14px;">
  <div class="card-header"><i class="fas fa-book-open"></i> <strong>গাইড</strong></div>
  <div class="card-body">
    <div class="guide-box">{{ task.guide }}</div>
  </div>
</div>

{% if task.tool_link %}
<a href="{{ task.tool_link }}" class="btn btn-primary w-100"
   style="display:block;margin-bottom:12px;">
  <i class="fas fa-tools"></i> এই Tool খোলো
</a>
{% endif %}

{% if task.script %}
<div class="card" style="margin-bottom:12px;" id="script-card">
  <div class="card-header"><i class="fas fa-terminal"></i> <strong>Command চালাও</strong></div>
  <div class="card-body">
    <div class="guide-box" style="margin-bottom:11px;">$ {{ task.script }}</div>
    <button class="btn btn-success w-100" onclick="runTaskScript()">
      <i class="fas fa-play"></i> Run করো
    </button>
    <div id="term" class="terminal" style="margin-top:11px;display:none;"></div>
  </div>
</div>
{% endif %}

<div class="card">
  <div class="card-body">
    {% if done %}
    <button class="btn btn-outline w-100" onclick="markTask('{{ task.id }}', false)">
      <i class="fas fa-undo"></i> Undo (চিহ্ন সরাও)
    </button>
    {% else %}
    <button class="btn btn-success w-100" onclick="markTask('{{ task.id }}', true)">
      <i class="fas fa-check"></i> সম্পন্ন হিসেবে Mark করো
    </button>
    {% endif %}
  </div>
</div>
"""
    content = render_template_string(
        f'<div class="page">{tpl}</div>',
        task=task,
        done=done,
    )
    extra = f"""<script>
function runTaskScript() {{
  document.getElementById('term').style.display = 'block';
  runStream('/api/run/task/{task_id}', 'term', function() {{
    markTask('{task_id}', true);
  }});
}}
</script>"""
    return page(content, "home", extra)


@app.route("/research")
def research() -> str:
    """Research tool page."""
    tpl = """
<div class="page-title"><i class="fas fa-search"></i> Research Tool</div>

<div class="card">
  <div class="card-header"><strong>🎯 নতুন লিড খোঁজো</strong></div>
  <div class="card-body">
    <label class="form-lbl">Niche (কোন ব্যবসা?)</label>
    <select class="form-sel" id="niche">
      <option value="restaurant">🍽️ Restaurant</option>
      <option value="dentist">🦷 Dentist</option>
      <option value="lawyer">⚖️ Lawyer</option>
      <option value="real estate">🏠 Real Estate</option>
      <option value="gym">💪 Gym/Fitness</option>
      <option value="salon">✂️ Salon/Beauty</option>
      <option value="hotel">🏨 Hotel</option>
      <option value="pharmacy">💊 Pharmacy</option>
      <option value="plumber">🔧 Plumber</option>
      <option value="electrician">⚡ Electrician</option>
    </select>

    <label class="form-lbl">Location (কোথায়? — US মার্কেট)</label>
    <select class="form-sel" id="location">
      <option value="New York, NY">New York, NY</option>
      <option value="Los Angeles, CA">Los Angeles, CA</option>
      <option value="Chicago, IL">Chicago, IL</option>
      <option value="Houston, TX">Houston, TX</option>
      <option value="Phoenix, AZ">Phoenix, AZ</option>
      <option value="Philadelphia, PA">Philadelphia, PA</option>
      <option value="San Antonio, TX">San Antonio, TX</option>
      <option value="San Diego, CA">San Diego, CA</option>
      <option value="Dallas, TX">Dallas, TX</option>
      <option value="Miami, FL">Miami, FL</option>
    </select>

    <label class="form-lbl">কতটি লিড খুঁজবে?</label>
    <input type="number" class="form-ctrl" id="count" value="50" min="5" max="500">

    <div class="toggle-row">
      <label class="switch">
        <input type="checkbox" id="skip_scrape">
        <span class="slider"></span>
      </label>
      <span style="font-size:.83rem;">Skip scraping <small style="color:var(--muted)">(দ্রুত)</small></span>
    </div>

    <button class="btn btn-primary w-100" onclick="startResearch()">
      <i class="fas fa-search"></i> রিসার্চ শুরু করো
    </button>
  </div>
</div>

<div class="card" id="term-card" style="display:none;">
  <div class="card-header">
    <strong><i class="fas fa-terminal"></i> Live Output</strong>
    <button class="btn btn-sm btn-outline" onclick="document.getElementById('term').textContent=''">
      Clear
    </button>
  </div>
  <div class="card-body">
    <div id="term" class="terminal"></div>
  </div>
</div>

<div class="card">
  <div class="card-header"><strong>📋 Tips</strong></div>
  <div class="card-body">
    <div class="guide-box">Google API Key না থাকলে "Skip scraping" চালু করো।

US মার্কেট — ভালো niche:
• Dentist (New York, LA) — high value, SEO ($2,500+/deal)
• Lawyer (Chicago, Dallas) — premium pricing ($3,500+/deal)
• Restaurant (Miami, Houston) — সহজে convert হয় ($1,500/deal)

প্রতিদিন ৫০+ লিড research করো।
Save হয়: tracking/leads.csv</div>
  </div>
</div>
"""
    extra = """<script>
function startResearch() {
  var niche = document.getElementById('niche').value;
  var loc = document.getElementById('location').value;
  var cnt = document.getElementById('count').value;
  var skip = document.getElementById('skip_scrape').checked ? '1' : '0';
  document.getElementById('term-card').style.display = 'block';
  var url = '/api/run/research?niche=' + encodeURIComponent(niche)
    + '&location=' + encodeURIComponent(loc)
    + '&count=' + cnt + '&skip=' + skip;
  runStream(url, 'term', function() {
    fetch('/api/task/morning_research/done', {method:'POST'});
  });
}
</script>"""
    return page(f'<div class="page">{tpl}</div>', "research", extra)


@app.route("/outreach")
def outreach() -> str:
    """Outreach tool page."""
    tpl = """
<div class="page-title"><i class="fas fa-envelope"></i> Outreach Tool</div>

<div class="card">
  <div class="card-header"><strong>📧 Email পাঠাও</strong></div>
  <div class="card-body">
    <label class="form-lbl">Campaign Type</label>
    <select class="form-sel" id="campaign">
      <option value="initial">Initial — প্রথম ইমেইল</option>
      <option value="follow_up">Follow-up — পরের ইমেইল</option>
    </select>

    <label class="form-lbl">Daily Limit</label>
    <input type="number" class="form-ctrl" id="limit" value="50" min="1" max="200">

    <div class="toggle-row">
      <label class="switch">
        <input type="checkbox" id="dry_run" checked>
        <span class="slider"></span>
      </label>
      <span style="font-size:.83rem;">
        <strong>Dry Run</strong>
        <small style="color:var(--muted)"> (preview — ইমেইল যাবে না)</small>
      </span>
    </div>

    <div class="warn-box">
      <i class="fas fa-exclamation-triangle"></i>
      <strong> প্রথমে Dry Run করো!</strong> ঠিক থাকলে OFF করে Send করো।
    </div>

    <button class="btn btn-primary w-100" onclick="startOutreach()">
      <i class="fas fa-paper-plane"></i> পাঠাও
    </button>
  </div>
</div>

<div class="card" id="term-card" style="display:none;">
  <div class="card-header"><strong><i class="fas fa-terminal"></i> Live Output</strong></div>
  <div class="card-body">
    <div id="term" class="terminal"></div>
  </div>
</div>

<div class="card">
  <div class="card-header"><strong>📋 Tips</strong></div>
  <div class="card-body">
    <div class="guide-box">SENDGRID_API_KEY লাগবে ইমেইল পাঠাতে।
→ sendgrid.com-এ free account (100 ইমেইল/দিন)

Follow-up sequence:
• 1st: 3 দিন পর
• 2nd: 7 দিন পর
• 3rd: 14 দিন পর

Good metrics:
• Open rate > 30% ✅
• Reply rate > 5% ✅</div>
  </div>
</div>
"""
    extra = """<script>
function startOutreach() {
  var campaign = document.getElementById('campaign').value;
  var limit = document.getElementById('limit').value;
  var dry = document.getElementById('dry_run').checked ? '1' : '0';
  document.getElementById('term-card').style.display = 'block';
  var url = '/api/run/outreach?campaign=' + campaign + '&limit=' + limit + '&dry=' + dry;
  var taskId = campaign === 'initial' ? 'outreach_initial' : 'outreach_followup';
  runStream(url, 'term', function() {
    fetch('/api/task/' + taskId + '/done', {method:'POST'});
  });
}
</script>"""
    return page(f'<div class="page">{tpl}</div>', "outreach", extra)


@app.route("/leads")
def leads_page() -> str:
    """Lead manager page."""
    leads = load_leads()
    stats = lead_stats(leads)

    tpl = """
<div class="page-title"><i class="fas fa-users"></i> Lead Manager</div>

<div class="stat-grid" style="margin-bottom:13px;">
  <div class="stat-box">
    <div class="stat-num">{{ stats.total }}</div>
    <div class="stat-lbl">মোট লিড</div>
  </div>
  <div class="stat-box">
    <div class="stat-num ga">{{ stats.grade_a }}</div>
    <div class="stat-lbl">Grade A</div>
  </div>
  <div class="stat-box">
    <div class="stat-num" style="color:#f39c12">{{ stats.replied }}</div>
    <div class="stat-lbl">Reply আসা</div>
  </div>
  <div class="stat-box">
    <div class="stat-num" style="color:var(--success)">{{ stats.converted }}</div>
    <div class="stat-lbl">Client 🎉</div>
  </div>
</div>

<div class="card" style="margin-bottom:12px;">
  <div class="card-body" style="padding:10px 13px;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
      <select class="form-sel" id="fs" onchange="filterLeads()" style="margin-bottom:0">
        <option value="">সব Status</option>
        <option value="new">New</option>
        <option value="contacted">Contacted</option>
        <option value="replied">Replied</option>
        <option value="converted">Converted</option>
      </select>
      <select class="form-sel" id="fg" onchange="filterLeads()" style="margin-bottom:0">
        <option value="">সব Grade</option>
        <option value="A">Grade A</option>
        <option value="B">Grade B</option>
        <option value="C">Grade C</option>
      </select>
    </div>
  </div>
</div>

{% if leads %}
<div class="card">
  <div class="card-header">
    <strong>📋 Leads ({{ leads|length }})</strong>
    <a href="/research" class="btn btn-sm btn-primary">+ নতুন</a>
  </div>
  <div class="table-wrap">
    <table id="ltable">
      <thead><tr>
        <th>নাম</th><th>Niche</th><th>Grade</th><th>Status</th>
      </tr></thead>
      <tbody>
        {% for l in leads %}
        <tr data-status="{{ l.get('status','new') }}" data-grade="{{ l.get('grade','') }}">
          <td>
            <div style="font-weight:600;font-size:.8rem">{{ l.get('name','—')[:18] }}</div>
            <div style="font-size:.68rem;color:var(--muted)">{{ l.get('location','') }}</div>
          </td>
          <td style="font-size:.78rem">{{ l.get('niche','') }}</td>
          <td><span class="g{{ l.get('grade','').lower() }}">{{ l.get('grade','—') }}</span></td>
          <td><span class="s-{{ l.get('status','new') }}">{{ l.get('status','new') }}</span></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% else %}
<div class="card">
  <div class="card-body" style="text-align:center;padding:35px 18px;color:var(--muted)">
    <i class="fas fa-users" style="font-size:2.2rem;margin-bottom:12px;display:block"></i>
    <div style="font-size:.95rem;margin-bottom:7px;">এখনো কোনো লিড নেই</div>
    <div style="font-size:.8rem;">Research tool দিয়ে প্রথম লিড খোঁজো!</div>
    <a href="/research" class="btn btn-primary" style="margin-top:14px;">
      <i class="fas fa-search"></i> Research শুরু করো
    </a>
  </div>
</div>
{% endif %}
"""
    extra = """<script>
function filterLeads() {
  var st = document.getElementById('fs').value;
  var gr = document.getElementById('fg').value;
  document.querySelectorAll('#ltable tbody tr').forEach(function(r) {
    var ok = (!st || r.dataset.status === st) && (!gr || r.dataset.grade === gr);
    r.style.display = ok ? '' : 'none';
  });
}
</script>"""
    content = render_template_string(
        f'<div class="page">{tpl}</div>',
        leads=leads,
        stats=stats,
    )
    return page(content, "leads", extra)


@app.route("/reports")
def reports() -> str:
    """Reports page."""
    leads = load_leads()
    stats = lead_stats(leads)
    est_revenue = f"{stats['converted'] * 2000:,}"
    report_files: list[str] = []
    if REPORTS_DIR.exists():
        report_files = sorted(
            [f.name for f in REPORTS_DIR.iterdir() if f.is_file()],
            reverse=True,
        )[:5]

    tpl = """
<div class="page-title"><i class="fas fa-chart-bar"></i> Report Generator</div>

<div class="card">
  <div class="card-header"><strong>📊 Report তৈরি করো</strong></div>
  <div class="card-body">
    <label class="form-lbl">Period</label>
    <select class="form-sel" id="period">
      <option value="weekly">সাপ্তাহিক (Weekly)</option>
      <option value="monthly">মাসিক (Monthly)</option>
    </select>
    <label class="form-lbl">Format</label>
    <select class="form-sel" id="fmt">
      <option value="html">HTML (browser-এ দেখা যাবে)</option>
      <option value="json">JSON</option>
    </select>
    <button class="btn btn-primary w-100" onclick="genReport()">
      <i class="fas fa-file-alt"></i> Report তৈরি করো
    </button>
  </div>
</div>

<div class="card" id="term-card" style="display:none;">
  <div class="card-header"><strong><i class="fas fa-terminal"></i> Output</strong></div>
  <div class="card-body">
    <div id="term" class="terminal"></div>
  </div>
</div>

<div class="card">
  <div class="card-header"><strong>📈 এখনকার Stats</strong></div>
  <div class="card-body">
    <div class="stat-grid">
      <div class="stat-box">
        <div class="stat-num">{{ stats.total }}</div>
        <div class="stat-lbl">মোট লিড</div>
      </div>
      <div class="stat-box">
        <div class="stat-num" style="color:#f39c12">{{ stats.reply_rate }}%</div>
        <div class="stat-lbl">Reply Rate</div>
      </div>
      <div class="stat-box">
        <div class="stat-num ga">{{ stats.grade_a }}</div>
        <div class="stat-lbl">Grade A</div>
      </div>
      <div class="stat-box">
        <div class="stat-num" style="color:var(--success)">${{ est_revenue }}</div>
        <div class="stat-lbl">Est. Revenue</div>
      </div>
    </div>
  </div>
</div>

{% if reports %}
<div class="card">
  <div class="card-header"><strong>📁 সাম্প্রতিক Reports</strong></div>
  <div class="card-body" style="padding-top:8px;padding-bottom:8px;">
    {% for rpt in reports %}
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:9px 0;border-bottom:1px solid var(--border);">
      <span style="font-size:.8rem;">{{ rpt }}</span>
      <a href="/download/{{ rpt }}" class="btn btn-sm btn-outline">
        <i class="fas fa-download"></i>
      </a>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}
"""
    extra = """<script>
function genReport() {
  var period = document.getElementById('period').value;
  var fmt = document.getElementById('fmt').value;
  document.getElementById('term-card').style.display = 'block';
  var url = '/api/run/report?period=' + period + '&format=' + fmt;
  runStream(url, 'term', function() {
    fetch('/api/task/weekly_report/done', {method:'POST'});
    setTimeout(function() { location.reload(); }, 800);
  });
}
</script>"""
    content = render_template_string(
        f'<div class="page">{tpl}</div>',
        stats=stats,
        est_revenue=est_revenue,
        reports=report_files,
    )
    return page(content, "reports", extra)


@app.route("/download/<filename>")
def download_report(filename: str) -> Response:
    """Download a report file (safe: verifies path is inside REPORTS_DIR)."""
    from flask import abort, send_from_directory

    # Strip any directory components and resolve the final path
    safe_name = Path(filename).name
    resolved = (REPORTS_DIR / safe_name).resolve()

    # Ensure the resolved path is strictly inside REPORTS_DIR
    try:
        resolved.relative_to(REPORTS_DIR.resolve())
    except ValueError:
        abort(403)

    if not resolved.exists():
        abort(404)

    return send_from_directory(str(REPORTS_DIR), safe_name)


# ═════════════════════════════════════════════════════════════════════════════
# API endpoints
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/task/<task_id>/done", methods=["POST"])
def api_mark_done(task_id: str) -> Response:
    """Mark a task as done."""
    mark_done(task_id)
    return jsonify({"status": "ok", "task_id": task_id, "done": True})


@app.route("/api/task/<task_id>/undone", methods=["POST"])
def api_mark_undone(task_id: str) -> Response:
    """Un-mark a task."""
    mark_undone(task_id)
    return jsonify({"status": "ok", "task_id": task_id, "done": False})


@app.route("/api/progress")
def api_progress() -> Response:
    """Return current progress as JSON."""
    return jsonify(load_progress())


@app.route("/api/leads")
def api_leads() -> Response:
    """Return leads as JSON."""
    return jsonify(load_leads())


@app.route("/api/run/research")
def api_run_research() -> Response:
    """SSE stream: run the research script."""
    niche = request.args.get("niche", "restaurant")
    location = request.args.get("location", "New York, NY")
    count = request.args.get("count", str(DEFAULT_LEAD_COUNT))
    skip = request.args.get("skip", "0")

    # Validate against allowlists to prevent injection
    if niche not in ALLOWED_NICHES:
        niche = "restaurant"
    if location not in ALLOWED_LOCATIONS:
        location = "New York, NY"

    try:
        count_int = max(MIN_LEAD_COUNT, min(MAX_LEAD_COUNT, int(count)))
    except ValueError:
        count_int = DEFAULT_LEAD_COUNT

    skip_flag = "--skip-scrape" if skip == "1" else ""
    cmd = (
        f'{sys.executable} scripts/run_research.py '
        f'--niche "{niche}" --location "{location}" '
        f'--count {count_int} {skip_flag}'
    ).strip()

    return Response(
        stream_job(cmd),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/run/outreach")
def api_run_outreach() -> Response:
    """SSE stream: run the outreach script."""
    campaign = request.args.get("campaign", "initial")
    if campaign not in ALLOWED_CAMPAIGNS:
        campaign = "initial"
    limit = request.args.get("limit", str(DEFAULT_EMAIL_LIMIT))
    dry = request.args.get("dry", "1")

    try:
        limit_int = max(MIN_EMAIL_LIMIT, min(MAX_EMAIL_LIMIT, int(limit)))
    except ValueError:
        limit_int = DEFAULT_EMAIL_LIMIT

    dry_flag = "--dry-run" if dry == "1" else ""
    cmd = (
        f'{sys.executable} scripts/send_outreach.py '
        f'--campaign {campaign} --limit {limit_int} {dry_flag}'
    ).strip()

    return Response(
        stream_job(cmd),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/run/report")
def api_run_report() -> Response:
    """SSE stream: run the report generator."""
    period = request.args.get("period", "weekly")
    if period not in ALLOWED_PERIODS:
        period = "weekly"
    fmt = request.args.get("format", "html")
    if fmt not in ALLOWED_FORMATS:
        fmt = "html"

    cmd = f'{sys.executable} scripts/generate_report.py --period {period} --format {fmt}'
    return Response(
        stream_job(cmd),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/run/task/<task_id>")
def api_run_task_script(task_id: str) -> Response:
    """SSE stream: run the script attached to a specific task."""
    task = get_task(task_id)

    def _no_script() -> Generator[str, None, None]:
        yield "data: এই task-এর কোনো runnable script নেই।\n\n"
        yield "data: __DONE__\n\n"

    if not task or not task.get("script"):
        return Response(
            _no_script(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )
    return Response(
        stream_job(str(task["script"])),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ═════════════════════════════════════════════════════════════════════════════
# AI Assistant routes
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/ai")
def ai_page() -> str:
    """AI Assistant chat page."""
    ai = get_ai()
    briefing: dict[str, Any] = {}
    if ai:
        briefing = ai.daily_briefing()

    tpl = """
<div style="padding:13px 13px 4px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
    <div style="width:38px;height:38px;background:linear-gradient(135deg,#4f8ef7,#6f42c1);
      border-radius:50%;display:flex;align-items:center;justify-content:center;
      font-size:1.15rem;flex-shrink:0;">🤖</div>
    <div>
      <div style="font-weight:700;font-size:.92rem;">Agency AI Assistant</div>
      <div style="font-size:.68rem;color:var(--muted);">
        API-free &bull; Bengali &bull; Context-aware
        <span style="color:var(--success);margin-left:5px;">● Online</span>
      </div>
    </div>
    <button onclick="clearChat()"
      style="margin-left:auto;background:none;border:none;color:var(--muted);
        font-size:.72rem;cursor:pointer;padding:4px 8px;border:1px solid var(--border);
        border-radius:6px;">🗑 Clear</button>
  </div>

  <!-- Tab bar -->
  <div style="display:flex;gap:4px;margin-top:6px;">
    <button id="tab-chat" onclick="showTab('chat')"
      style="flex:1;padding:7px 4px;border-radius:8px 8px 0 0;border:1px solid var(--border);
        border-bottom:none;background:var(--card);font-size:.78rem;font-weight:600;cursor:pointer;">
      💬 Chat</button>
    <button id="tab-strategy" onclick="showTab('strategy')"
      style="flex:1;padding:7px 4px;border-radius:8px 8px 0 0;border:1px solid var(--border);
        border-bottom:none;background:var(--surface);font-size:.78rem;cursor:pointer;">
      🧠 Strategy</button>
    <button id="tab-market" onclick="showTab('market')"
      style="flex:1;padding:7px 4px;border-radius:8px 8px 0 0;border:1px solid var(--border);
        border-bottom:none;background:var(--surface);font-size:.78rem;cursor:pointer;">
      🌍 Market</button>
  </div>
</div>

<!-- ── Strategy Panel ── -->
<div id="panel-strategy" style="display:none;padding:0 13px 13px;">
  <div style="border:1px solid var(--border);border-radius:0 0 12px 12px;
    background:var(--card);padding:13px;">
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
      <select id="mkt-select" onchange="loadStrategy()"
        style="flex:1;min-width:110px;padding:7px 10px;border-radius:8px;
          border:1px solid var(--border);background:var(--surface);
          color:var(--text);font-size:.82rem;">
        <option value="USA">🇺🇸 USA</option>
        <option value="Canada">🇨🇦 Canada</option>
        <option value="UK">🇬🇧 UK</option>
        <option value="Europe">🇪🇺 Europe</option>
        <option value="Australia">🇦🇺 Australia</option>
      </select>
      <button onclick="loadStrategy()"
        style="padding:7px 14px;border-radius:8px;border:none;
          background:var(--primary);color:#fff;font-size:.82rem;cursor:pointer;">
        🔄 Refresh</button>
    </div>
    <div id="strategy-loading" style="text-align:center;padding:20px;color:var(--muted);">
      <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
    </div>
    <div id="strategy-content" style="display:none;"></div>
  </div>
</div>

<!-- ── Market Intel Panel ── -->
<div id="panel-market" style="display:none;padding:0 13px 13px;">
  <div style="border:1px solid var(--border);border-radius:0 0 12px 12px;
    background:var(--card);padding:13px;">
    <div style="font-weight:700;margin-bottom:8px;font-size:.88rem;">
      🌍 Target Markets — USA, Canada, UK, Europe</div>
    <div id="market-content">
      <div style="text-align:center;padding:20px;color:var(--muted);">
        <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
      </div>
    </div>
  </div>
</div>

<!-- ── Chat Panel ── -->
<div id="panel-chat" style="padding:0 13px 13px;">
  <div class="chat-wrap" style="border-radius:0 0 12px 12px;">
    <div class="chat-msgs" id="chat-msgs">
      <!-- Initial briefing message -->
      <div class="msg msg-ai" id="briefing-msg">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>

    <!-- Quick action buttons -->
    <div class="quick-btns" id="quick-btns">
      <button class="quick-btn" onclick="sendQuick('আজ কী করব?')">📋 আজকের কাজ</button>
      <button class="quick-btn" onclick="sendQuick('আমার progress কেমন?')">📊 Progress</button>
      <button class="quick-btn" onclick="sendQuick('কিভাবে রিসার্চ করব?')">🔍 Research</button>
      <button class="quick-btn" onclick="sendQuick('কিভাবে email পাঠাব?')">📧 Email</button>
      <button class="quick-btn" onclick="sendQuick('কোন niche সেরা?')">🎯 Best Niche</button>
      <button class="quick-btn" onclick="sendQuick('আমার জন্য best strategy কী?')">🧠 Strategy</button>
      <button class="quick-btn" onclick="sendQuick('app সবসময় running রাখব কিভাবে?')">🔄 Always-On</button>
      <button class="quick-btn" onclick="sendQuick('$1M revenue কিভাবে?')">💰 Revenue</button>
    </div>

    <div class="chat-input-row">
      <textarea class="chat-input" id="chat-input"
        placeholder="যেকোনো প্রশ্ন করো... (Bengali বা English)"
        rows="1"
        onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMsg();}
                   this.style.height='auto';this.style.height=this.scrollHeight+'px';"
        oninput="this.style.height='auto';this.style.height=this.scrollHeight+'px';">
      </textarea>
      <button class="send-btn" onclick="sendMsg()">
        <i class="fas fa-paper-plane"></i>
      </button>
    </div>
  </div>
</div>
"""
    extra = f"""<script>
var BRIEFING = {json.dumps(briefing)};
var chatMsgs = document.getElementById('chat-msgs');

/* ── Tab switching ── */
function showTab(name) {{
  ['chat','strategy','market'].forEach(function(t) {{
    document.getElementById('panel-'+t).style.display = (t===name) ? '' : 'none';
    var btn = document.getElementById('tab-'+t);
    if (btn) {{
      btn.style.background = (t===name) ? 'var(--card)' : 'var(--surface)';
      btn.style.fontWeight = (t===name) ? '600' : '400';
    }}
  }});
  if (name==='strategy') loadStrategy();
  if (name==='market') loadMarket();
}}

/* ── Strategy Panel ── */
function loadStrategy() {{
  var market = document.getElementById('mkt-select').value;
  document.getElementById('strategy-loading').style.display = '';
  document.getElementById('strategy-content').style.display = 'none';
  fetch('/api/ai/recommend?market=' + encodeURIComponent(market))
  .then(function(r){{ return r.json(); }})
  .then(function(d) {{
    document.getElementById('strategy-loading').style.display = 'none';
    var sc = document.getElementById('strategy-content');
    sc.style.display = '';
    var rec = d.recommendation || {{}};
    var niches = d.top_niches || [];
    var pipe = d.pipeline || {{}};

    // Funnel bar
    var funnelHtml = '<div style="margin-bottom:12px;">' +
      '<div style="font-weight:700;font-size:.82rem;margin-bottom:6px;">📊 Pipeline</div>' +
      '<div style="display:flex;gap:6px;flex-wrap:wrap;">' +
      mkBadge('Leads','#4f8ef7',pipe.total||0) +
      mkBadge('Contacted','#6f42c1',pipe.contacted||0) +
      mkBadge('Replied','#20c997',pipe.replied||0) +
      mkBadge('Clients','#fd7e14',pipe.converted||0) +
      '</div>' +
      '<div style="margin-top:6px;font-size:.75rem;color:var(--muted);">' +
      'Est. Revenue: <strong>$' + (pipe.est_revenue||0).toLocaleString() + '</strong>' +
      ' &nbsp;|&nbsp; Goal: <strong>' + (pipe.goal_pct||0) + '%</strong> of $1M' +
      '</div></div>';

    // #1 Action card
    var actionHtml = '<div style="background:linear-gradient(135deg,var(--primary),#6f42c1);' +
      'color:#fff;border-radius:12px;padding:12px;margin-bottom:12px;">' +
      '<div style="font-size:.72rem;opacity:.85;margin-bottom:4px;">🎯 #1 Priority Action</div>' +
      '<div style="font-weight:700;font-size:.95rem;margin-bottom:6px;">' + escHtml(rec.action||'') + '</div>' +
      '<div style="font-size:.76rem;opacity:.9;margin-bottom:8px;">' + escHtml(rec.reason||'') + '</div>' +
      '<div style="font-size:.74rem;background:rgba(255,255,255,.15);border-radius:8px;padding:7px;">' +
      '⚡ ' + escHtml(rec.quick_win||'') + '</div></div>';

    // Run button
    var runBtn = '';
    if (rec.run_tool) {{
      runBtn = '<a href="' + rec.run_tool + '" style="display:block;text-align:center;' +
        'background:var(--primary);color:#fff;padding:10px;border-radius:10px;' +
        'text-decoration:none;font-weight:700;font-size:.86rem;margin-bottom:12px;">' +
        '▶️ এখনই করো → ' + rec.run_tool + '</a>';
    }}

    // Top niches
    var nichesHtml = '<div style="font-weight:700;font-size:.82rem;margin-bottom:8px;">' +
      d.market_flag + ' ' + d.market + ' — Top Niches</div>' +
      '<div style="display:flex;flex-direction:column;gap:7px;">';
    niches.forEach(function(n,i) {{
      var bar = Math.round(n.roi_score / 100 * 100);
      nichesHtml += '<div style="background:var(--surface);border-radius:10px;padding:10px;">' +
        '<div style="display:flex;justify-content:space-between;align-items:center;">' +
        '<span style="font-weight:600;font-size:.83rem;">' + ['🥇','🥈','🥉'][i] + ' ' + escHtml(n.label) + '</span>' +
        '<span style="font-size:.72rem;color:var(--muted);">ROI: <strong>' + n.roi_score + '</strong>/100</span>' +
        '</div>' +
        '<div style="height:4px;background:var(--border);border-radius:4px;margin:5px 0;">' +
        '<div style="height:100%;width:' + bar + '%;background:var(--primary);border-radius:4px;"></div></div>' +
        '<div style="font-size:.72rem;color:var(--muted);">$' + n.avg_deal.toLocaleString() + ' avg &bull; ' +
        n.close_days + ' days close</div>' +
        '<div style="font-size:.71rem;margin-top:4px;color:var(--text);">' + escHtml(n.why) + '</div>' +
        '</div>';
    }});
    nichesHtml += '</div>';

    // Best cities
    var citiesHtml = '<div style="margin-top:10px;font-size:.76rem;color:var(--muted);">' +
      '🏙️ Target cities: <strong>' + (d.best_cities||[]).join(', ') + '</strong></div>' +
      '<div style="font-size:.76rem;color:var(--muted);margin-top:3px;">' +
      '⏰ Best send time: <strong>' + escHtml(d.send_time||'') + '</strong></div>';

    sc.innerHTML = funnelHtml + actionHtml + runBtn + nichesHtml + citiesHtml;
  }})
  .catch(function(e) {{
    document.getElementById('strategy-loading').style.display = 'none';
    document.getElementById('strategy-content').style.display = '';
    document.getElementById('strategy-content').innerHTML =
      '<div style="color:var(--danger);font-size:.8rem;">❌ ' + escHtml(e.message) + '</div>';
  }});
}}

function mkBadge(label, color, val) {{
  return '<div style="background:' + color + '22;border:1px solid ' + color + '44;' +
    'border-radius:8px;padding:5px 10px;text-align:center;min-width:55px;">' +
    '<div style="font-size:.7rem;color:var(--muted);">' + label + '</div>' +
    '<div style="font-weight:700;font-size:.95rem;color:' + color + ';">' + val + '</div></div>';
}}

/* ── Market Intel Panel ── */
function loadMarket() {{
  var mc = document.getElementById('market-content');
  if (mc.dataset.loaded) return;
  mc.dataset.loaded = '1';

  var markets = [
    {{id:'USA', flag:'🇺🇸', niches:['🦷 Dentist','⚖️ Lawyer','🔧 Plumber','⚡ Electrician','🏠 Real Estate'],
      rate:'4-8%', time:'9-11 AM EST Tue-Thu', cities:['New York','Los Angeles','Chicago','Houston','Phoenix']}},
    {{id:'Canada', flag:'🇨🇦', niches:['🦷 Dentist','🔧 Plumber','🏠 Real Estate','⚖️ Lawyer','💪 Gym'],
      rate:'5-9%', time:'9-11 AM EST Tue-Thu', cities:['Toronto','Vancouver','Calgary','Ottawa','Montreal']}},
    {{id:'UK', flag:'🇬🇧', niches:['🦷 Dentist','⚖️ Lawyer','⚡ Electrician','💇 Salon','📊 Accountant'],
      rate:'4-7%', time:'9-11 AM GMT Tue-Thu', cities:['London','Manchester','Birmingham','Leeds','Glasgow']}},
    {{id:'Europe', flag:'🇪🇺', niches:['🍽️ Restaurant','💪 Gym','💇 Salon','🦷 Dentist','📊 Accountant'],
      rate:'3-6%', time:'9-11 AM CET Tue-Thu', cities:['Berlin','Paris','Amsterdam','Madrid','Dublin']}},
    {{id:'Australia', flag:'🇦🇺', niches:['🦷 Dentist','🧘 Chiro','🔧 Plumber','💪 Gym','🏠 Real Estate'],
      rate:'5-8%', time:'9-11 AM AEST Tue-Thu', cities:['Sydney','Melbourne','Brisbane','Perth','Adelaide']}}
  ];
  var html = '<div style="display:flex;flex-direction:column;gap:10px;">';
  markets.forEach(function(m) {{
    html += '<div style="background:var(--surface);border-radius:12px;padding:12px;">' +
      '<div style="font-weight:700;font-size:.88rem;margin-bottom:6px;">' +
      m.flag + ' ' + m.id +
      ' <span style="font-size:.7rem;color:var(--success);font-weight:400;">Reply: ' + m.rate + '</span></div>' +
      '<div style="font-size:.74rem;color:var(--muted);margin-bottom:5px;">⏰ ' + m.time + '</div>' +
      '<div style="font-size:.74rem;margin-bottom:5px;"><strong>Top Niches:</strong> ' + m.niches.join(' &bull; ') + '</div>' +
      '<div style="font-size:.73rem;color:var(--muted);">🏙️ ' + m.cities.join(', ') + '</div>' +
      '<button onclick="document.getElementById(\'mkt-select\').value=\'' + m.id +
      '\';showTab(\'strategy\')" style="margin-top:8px;width:100%;padding:7px;border-radius:8px;' +
      'border:none;background:var(--primary);color:#fff;font-size:.76rem;cursor:pointer;">' +
      '🎯 ' + m.id + ' Strategy দেখো</button></div>';
  }});
  html += '</div>';
  mc.innerHTML = html;
}}

/* ── Chat ── */

/* Show briefing after short delay (feels natural) */
setTimeout(function() {{
  var bEl = document.getElementById('briefing-msg');
  if (bEl && BRIEFING.reply) {{
    bEl.innerHTML = mdToHtml(BRIEFING.reply);
    if (BRIEFING.quick_actions && BRIEFING.quick_actions.length) {{
      var div = document.createElement('div');
      div.className = 'quick-btns';
      div.style.marginTop = '8px';
      BRIEFING.quick_actions.forEach(function(qa) {{
        var b = document.createElement('button');
        b.className = 'quick-btn';
        b.textContent = qa.label;
        b.onclick = function() {{ sendQuick(qa.msg); }};
        div.appendChild(b);
      }});
      bEl.appendChild(div);
    }}
  }}
  scrollChat();
}}, 500);

function scrollChat() {{
  chatMsgs.scrollTop = chatMsgs.scrollHeight;
}}

function appendMsg(html, isUser) {{
  var el = document.createElement('div');
  el.className = 'msg ' + (isUser ? 'msg-user' : 'msg-ai');
  el.innerHTML = html;
  chatMsgs.appendChild(el);
  scrollChat();
  return el;
}}

function appendTyping() {{
  return appendMsg(
    '<span class="typing-dot"></span><span class="typing-dot"></span>' +
    '<span class="typing-dot"></span>', false
  );
}}

function sendMsg() {{
  var inp = document.getElementById('chat-input');
  var msg = inp.value.trim();
  if (!msg) return;
  inp.value = '';
  inp.style.height = 'auto';
  _doSend(msg);
}}

function sendQuick(msg) {{
  if (msg.startsWith('__goto__')) {{
    window.location.href = msg.replace('__goto__', '');
    return;
  }}
  _doSend(msg);
}}

function _doSend(msg) {{
  appendMsg(escHtml(msg), true);
  var typing = appendTyping();
  fetch('/api/ai/chat', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{message: msg}})
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(data) {{
    typing.remove();
    var el = appendMsg(mdToHtml(data.reply || '(no response)'), false);
    // Tool link button
    if (data.tool_link) {{
      var div = document.createElement('div');
      div.style.marginTop = '8px';
      var a = document.createElement('a');
      a.href = data.tool_link;
      a.className = 'quick-btn goto';
      a.innerHTML = '<i class="fas fa-arrow-right"></i> Tool খোলো';
      div.appendChild(a);
      el.appendChild(div);
    }}
    // Quick action buttons
    if (data.quick_actions && data.quick_actions.length) {{
      var div2 = document.createElement('div');
      div2.className = 'quick-btns';
      div2.style.marginTop = '8px';
      data.quick_actions.forEach(function(qa) {{
        var b = document.createElement('button');
        b.className = qa.msg.startsWith('__goto__') ? 'quick-btn goto' : 'quick-btn';
        b.textContent = qa.label;
        b.onclick = function() {{ sendQuick(qa.msg); }};
        div2.appendChild(b);
      }});
      el.appendChild(div2);
    }}
    scrollChat();
  }})
  .catch(function(e) {{
    typing.remove();
    appendMsg('❌ Error: ' + e.message, false);
  }});
}}

function clearChat() {{
  fetch('/api/ai/clear', {{method:'POST'}}).then(function() {{
    chatMsgs.innerHTML = '';
    location.reload();
  }});
}}

function escHtml(t) {{
  return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}
</script>"""
    return page(f"{tpl}", "ai", extra)


@app.route("/api/ai/chat", methods=["POST"])
def api_ai_chat() -> Response:
    """Process a chat message through the AI assistant."""
    from flask import abort

    data = request.get_json(silent=True)
    if not data or "message" not in data:
        abort(400)

    raw_message: str = str(data["message"])
    # Limit input length to prevent abuse
    message = raw_message[:500].strip()
    if not message:
        abort(400)

    ai = get_ai()
    if ai is None:
        return jsonify({
            "reply": (
                "⚠️ AI Assistant লোড হয়নি।\n\n"
                "`scripts/ai_assistant.py` ফাইলটি আছে কিনা দেখো।"
            ),
            "intent": "error",
            "quick_actions": [],
            "tool_link": None,
            "run_cmd": None,
        })

    result = ai.chat(message)
    return jsonify(result)


@app.route("/api/ai/clear", methods=["POST"])
def api_ai_clear() -> Response:
    """Clear the AI conversation history for this session."""
    ai = get_ai()
    if ai:
        ai.clear_history()
    return jsonify({"status": "ok"})


@app.route("/api/ai/briefing")
def api_ai_briefing() -> Response:
    """Return the daily briefing as JSON."""
    ai = get_ai()
    if ai is None:
        return jsonify({"reply": "AI not available.", "quick_actions": []})
    return jsonify(ai.daily_briefing())


@app.route("/api/ai/recommend")
def api_ai_recommend() -> Response:
    """
    Return a full strategic recommendation: best niche, market, and #1 action.

    Query param: ?market=USA  (default USA; also Canada, UK, Europe, Australia)
    """
    ai = get_ai()
    if ai is None:
        return jsonify({"error": "AI not available."}), 503

    market = request.args.get("market", "USA").strip()
    allowed = {"USA", "Canada", "UK", "Europe", "Australia"}
    if market not in allowed:
        market = "USA"

    try:
        data = ai.get_strategy_recommendation(market=market)
        return jsonify(data)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("\n" + "=" * 60)
    print("  🚀 Agency Research Automation — Mobile Web App")
    print("  Owner: Md Jamil Islam  |  Target: $1M/year")
    print(f"  URL:   http://localhost:{port}")
    print("  " + "─" * 56)
    print("  📱 মোবাইলে খুলতে:")
    print("  Replit → Run, দেওয়া URL → mobile browser")
    print("  Termux → http://localhost:5000")
    print("  Same WiFi → http://<PC-IP>:5000")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=False, threaded=True)
