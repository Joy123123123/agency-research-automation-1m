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
    from flask import Flask, Response, jsonify, redirect, render_template_string, request, url_for
except ImportError:
    print("\n❌  Flask পাওয়া যায়নি। ইনস্টল করুন:\n    pip install flask\n")
    sys.exit(1)

# ── Allowed values (input validation) ────────────────────────────────────────
ALLOWED_NICHES = {
    "restaurant", "dentist", "lawyer", "real estate", "gym",
    "salon", "hotel", "pharmacy", "plumber", "electrician",
}
ALLOWED_LOCATIONS = {
    "Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna",
    "Comilla", "Mymensingh",
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
app.secret_key = os.urandom(24)

# ── Global job output queue ───────────────────────────────────────────────────
_job_output: queue.Queue[str] = queue.Queue()
_job_running = threading.Event()


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
@media(max-width:380px){.stat-num{font-size:1.35rem;}body{font-size:14px;}}
</style>
"""

COMMON_SCRIPTS = """
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
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
</script>
"""


def nav_html(active: str) -> str:
    """Render the bottom navigation bar."""
    pages = [
        ("home", "/", "fa-home", "হোম"),
        ("research", "/research", "fa-search", "রিসার্চ"),
        ("outreach", "/outreach", "fa-envelope", "আউটরিচ"),
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

    <label class="form-lbl">Location (কোথায়?)</label>
    <select class="form-sel" id="location">
      <option value="Dhaka">Dhaka</option>
      <option value="Chittagong">Chittagong</option>
      <option value="Sylhet">Sylhet</option>
      <option value="Rajshahi">Rajshahi</option>
      <option value="Khulna">Khulna</option>
      <option value="Comilla">Comilla</option>
      <option value="Mymensingh">Mymensingh</option>
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

ভালো niche:
• Restaurant — সহজে convert হয়
• Dentist — high value, SEO
• Lawyer — premium pricing

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
    location = request.args.get("location", "Dhaka")
    count = request.args.get("count", str(DEFAULT_LEAD_COUNT))
    skip = request.args.get("skip", "0")

    # Validate against allowlists to prevent injection
    if niche not in ALLOWED_NICHES:
        niche = "restaurant"
    if location not in ALLOWED_LOCATIONS:
        location = "Dhaka"

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
