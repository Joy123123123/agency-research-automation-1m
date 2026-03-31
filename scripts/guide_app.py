#!/usr/bin/env python3
"""
Agency Research Automation — Interactive Guide App (বাংলা)
Owner: Md Jamil Islam
Goal: ধাপে ধাপে গাইড করা, progress save করা, resume করার সুবিধা

Usage:
    python scripts/guide_app.py

Features:
    - সব কাজ Section আকারে সাজানো
    - প্রতিটি কাজ শেষ করলে ✅ মার্ক হয়
    - পরের দিন আবার ঢুকলে যেখানে ছেড়েছিলে সেখান থেকে শুরু
    - Reminder: কোন কাজ বাকি আছে দেখাবে
    - Termux / Replit / PC — সব জায়গায় কাজ করবে
"""

import sys
import json
import os
import subprocess
import traceback
from datetime import date
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────
# Constants
# ──────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
PROGRESS_FILE = BASE_DIR / "tracking" / "app_progress.json"
LEADS_FILE = BASE_DIR / "tracking" / "leads.csv"

# ANSI রঙ (Termux/Linux সাপোর্ট করে; Windows-এ ঠিকঠাক না হলেও কাজ চলবে)
C = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "cyan": "\033[96m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "dim": "\033[2m",
}


def clr(text: str, color: str) -> str:
    """রঙ লাগাও।"""
    return f"{C.get(color, '')}{text}{C['reset']}"


# ──────────────────────────────────────────
# Sections & Tasks Definition
# ──────────────────────────────────────────

# প্রতিটি section-এ tasks আছে।
# প্রতিটি task-এ:
#   id        — unique str
#   title     — ছোট শিরোনাম
#   guide     — বিস্তারিত বাংলা গাইড
#   command   — (optional) চালানোর কমান্ড
#   freq      — "daily" | "weekly" | "monthly" | "once"

SECTIONS: list[dict[str, Any]] = [
    {
        "id": "setup",
        "icon": "⚙️",
        "title": "প্রথম সেটআপ",
        "desc": "একবারই করতে হবে — API কী, ভার্চুয়াল এনভায়রনমেন্ট, ডিপেন্ডেন্সি",
        "tasks": [
            {
                "id": "setup_venv",
                "title": "Python Virtual Environment তৈরি করো",
                "freq": "once",
                "guide": (
                    "📌 Virtual Environment মানে একটা আলাদা Python ঘর যেখানে সব library থাকবে।\n"
                    "\n"
                    "কমান্ড:\n"
                    "  python -m venv venv\n"
                    "  source venv/bin/activate   ← Linux/Mac/Termux\n"
                    "  venv\\Scripts\\activate      ← Windows\n"
                    "\n"
                    "Termux-এ যদি সমস্যা হয়:\n"
                    "  pkg install python\n"
                    "  pip install virtualenv\n"
                    "  virtualenv venv\n"
                    "  source venv/bin/activate\n"
                ),
                "command": "python -m venv venv && echo 'venv তৈরি হয়েছে!'",
            },
            {
                "id": "setup_deps",
                "title": "Dependencies Install করো",
                "freq": "once",
                "guide": (
                    "📌 requirements.txt-এ সব library-র নাম লেখা আছে।\n"
                    "এই কমান্ড সব এক সাথে install করে দেবে।\n"
                    "\n"
                    "venv activate থাকলে:\n"
                    "  pip install -r requirements.txt\n"
                    "\n"
                    "Termux-এ সময় নিতে পারে — ধৈর্য ধরো 😊\n"
                ),
                "command": "pip install -r requirements.txt",
            },
            {
                "id": "setup_apikeys",
                "title": "API কী সেটআপ করো",
                "freq": "once",
                "guide": (
                    "📌 config/api_keys.env ফাইলে আপনার API কী দিতে হবে।\n"
                    "\n"
                    "প্রথমে উদাহরণ ফাইল কপি করো:\n"
                    "  cp config/api_keys.env.example config/api_keys.env\n"
                    "\n"
                    "এরপর ফাইলটি খুলে কী দিন:\n"
                    "  nano config/api_keys.env\n"
                    "\n"
                    "কোথায় পাবেন?\n"
                    "  OPENAI_API_KEY     → platform.openai.com\n"
                    "  GOOGLE_API_KEY     → console.cloud.google.com (Maps API)\n"
                    "  SENDGRID_API_KEY   → sendgrid.com (বিনামূল্যে 100 ইমেইল/দিন)\n"
                    "  AIRTABLE_API_KEY   → airtable.com/create/tokens\n"
                    "  NOTION_TOKEN       → notion.so/my-integrations\n"
                    "\n"
                    "⚠️  কী কখনো GitHub-এ push করবেন না!\n"
                ),
                "command": None,
            },
            {
                "id": "setup_logs",
                "title": "Logs ফোল্ডার তৈরি করো",
                "freq": "once",
                "guide": (
                    "📌 Script চালাতে গেলে logs/ ফোল্ডার লাগবে।\n"
                    "\n"
                    "  mkdir -p logs data/reports\n"
                ),
                "command": "mkdir -p logs data/reports && echo 'ফোল্ডার তৈরি হয়েছে!'",
            },
        ],
    },
    {
        "id": "morning",
        "icon": "🌅",
        "title": "সকালের কাজ (9:00–10:00 AM)",
        "desc": "প্রতিদিন সকালে নতুন লিড খোঁজো এবং inbox চেক করো",
        "tasks": [
            {
                "id": "morning_research",
                "title": "নতুন লিড রিসার্চ করো",
                "freq": "daily",
                "guide": (
                    "📌 Google Maps API ব্যবহার করে আপনার নির্বাচিত niche-এ লিড খোঁজে\n"
                    "AI দিয়ে score করবে এবং tracking/leads.csv-এ save করবে।\n"
                    "\n"
                    "কমান্ড:\n"
                    "  python scripts/run_research.py --niche restaurant --location \"New York, NY\" --count 50\n"
                    "\n"
                    "Niche পরিবর্তন করতে পারো:\n"
                    "  restaurant, dentist, lawyer, real estate, gym, salon, hotel, pharmacy\n"
                    "\n"
                    "US Location:\n"
                    "  \"New York, NY\", \"Los Angeles, CA\", \"Chicago, IL\", \"Houston, TX\", \"Miami, FL\"\n"
                    "\n"
                    "API Key না থাকলে --skip-scrape দিয়ে চালাও:\n"
                    "  python scripts/run_research.py --skip-scrape\n"
                ),
                "command": "python scripts/run_research.py --niche restaurant --location \"New York, NY\" --count 50",
            },
            {
                "id": "morning_review_leads",
                "title": "নতুন লিড review করো",
                "freq": "daily",
                "guide": (
                    "📌 tracking/leads.csv ফাইলে যা পাওয়া গেছে দেখো।\n"
                    "\n"
                    "CSV ফাইল দেখতে:\n"
                    "  cat tracking/leads.csv\n"
                    "  বা Excel/Google Sheets-এ open করো।\n"
                    "\n"
                    "Grade A/B লিড গুলো সবচেয়ে ভালো। তাদের ইমেইল আছে কিনা চেক করো।\n"
                    "\n"
                    "মোট কতটি লিড আছে দেখতে:\n"
                    "  python -c \"import csv; r=list(csv.DictReader(open('tracking/leads.csv'))); print(f'মোট লিড: {len(r)}')\"\n"
                ),
                "command": None,
            },
            {
                "id": "morning_inbox",
                "title": "Reply Inbox চেক করো",
                "freq": "daily",
                "guide": (
                    "📌 যে ইমেইল থেকে আউটরিচ পাঠিয়েছো সেটার inbox খোলো।\n"
                    "\n"
                    "কেউ reply করলে:\n"
                    "  ✅ আগ্রহী হলে — call schedule করো (Section 4 দেখো)\n"
                    "  ❌ Unsubscribe করলে — leads.csv-এ status='unsubscribed' দাও\n"
                    "\n"
                    "Gmail ব্যবহার করলে: gmail.com খোলো\n"
                    "SendGrid dashboard: app.sendgrid.com\n"
                ),
                "command": None,
            },
        ],
    },
    {
        "id": "outreach",
        "icon": "📧",
        "title": "আউটরিচ (10:00–11:00 AM)",
        "desc": "লিডদের ইমেইল পাঠাও এবং follow-up দাও",
        "tasks": [
            {
                "id": "outreach_initial",
                "title": "প্রথম আউটরিচ ইমেইল পাঠাও",
                "freq": "daily",
                "guide": (
                    "📌 tracking/leads.csv থেকে নতুন লিডদের AI-generated personalized ইমেইল পাঠাবে।\n"
                    "\n"
                    "আগে dry-run করে দেখো (ইমেইল যাবে না, preview দেখাবে):\n"
                    "  python scripts/send_outreach.py --campaign initial --dry-run\n"
                    "\n"
                    "ঠিক থাকলে actual send করো:\n"
                    "  python scripts/send_outreach.py --campaign initial\n"
                    "\n"
                    "প্রতিদিন limit: 200 ইমেইল (SendGrid free plan)\n"
                    "\n"
                    "⚠️  SENDGRID_API_KEY না থাকলে এটা কাজ করবে না।\n"
                    "   প্রথমে sendgrid.com-এ free account খোলো।\n"
                ),
                "command": "python scripts/send_outreach.py --campaign initial --dry-run",
            },
            {
                "id": "outreach_followup",
                "title": "Follow-up ইমেইল পাঠাও",
                "freq": "daily",
                "guide": (
                    "📌 আগে যাদের ইমেইল পাঠানো হয়েছে কিন্তু reply করেনি তাদের follow-up দাও।\n"
                    "\n"
                    "  python scripts/send_outreach.py --campaign follow_up\n"
                    "\n"
                    "Follow-up কতদিন পর পাঠাবে?\n"
                    "  - 1st follow-up: 3 দিন পর\n"
                    "  - 2nd follow-up: 7 দিন পর\n"
                    "  - 3rd follow-up: 14 দিন পর\n"
                    "\n"
                    "এই সিকোয়েন্স src/automation/follow_up.py-তে আছে।\n"
                ),
                "command": "python scripts/send_outreach.py --campaign follow_up",
            },
        ],
    },
    {
        "id": "analytics",
        "icon": "📊",
        "title": "Analytics দেখো (11:00–12:00 PM)",
        "desc": "ইমেইল open rate, lead status, campaign performance চেক করো",
        "tasks": [
            {
                "id": "analytics_sendgrid",
                "title": "SendGrid Dashboard চেক করো",
                "freq": "daily",
                "guide": (
                    "📌 SendGrid Dashboard-এ গেলে দেখবে:\n"
                    "  - কতটি ইমেইল open হয়েছে\n"
                    "  - কতটি click হয়েছে\n"
                    "  - কতটি bounce/spam হয়েছে\n"
                    "\n"
                    "URL: https://app.sendgrid.com/statistics\n"
                    "\n"
                    "ভালো metric:\n"
                    "  Open rate > 30%  ✅\n"
                    "  Reply rate > 5%  ✅\n"
                    "  Click rate > 10% ✅\n"
                ),
                "command": None,
            },
            {
                "id": "analytics_leads",
                "title": "Lead Status আপডেট করো",
                "freq": "daily",
                "guide": (
                    "📌 tracking/leads.csv খুলে lead-দের status আপডেট করো:\n"
                    "\n"
                    "  status field-এ লিখতে পারো:\n"
                    "  new           → এখনো contact করা হয়নি\n"
                    "  contacted     → ইমেইল পাঠানো হয়েছে\n"
                    "  replied       → reply এসেছে\n"
                    "  interested    → কল schedule হয়েছে\n"
                    "  converted     → client হয়েছে 🎉\n"
                    "  not_interested → interested না\n"
                    "  unsubscribed  → unsubscribe করেছে\n"
                    "\n"
                    "Excel বা Google Sheets-এ CSV import করলে সহজ হবে।\n"
                ),
                "command": None,
            },
            {
                "id": "analytics_report",
                "title": "Daily Summary দেখো",
                "freq": "daily",
                "guide": (
                    "📌 আজকের performance summary দেখতে:\n"
                    "\n"
                    "  python -c \"\n"
                    "import csv\n"
                    "rows = list(csv.DictReader(open('tracking/leads.csv')))\n"
                    "from collections import Counter\n"
                    "status = Counter(r.get('status','new') for r in rows)\n"
                    "print('📊 Lead Status:')\n"
                    "for k,v in status.items(): print(f'  {k}: {v}')\n"
                    "print(f'  মোট: {len(rows)}')\n"
                    "\"\n"
                ),
                "command": (
                    "python -c \""
                    "import csv,os; f='tracking/leads.csv';"
                    "rows=list(csv.DictReader(open(f))) if os.path.exists(f) else [];"
                    "from collections import Counter;"
                    "st=Counter(r.get('status','new') for r in rows);"
                    "print('📊 Lead Status সারাংশ:');"
                    "[print(f'  {k}: {v}টি') for k,v in st.items()];"
                    "print(f'  মোট: {len(rows)}টি লিড')\""
                ),
            },
        ],
    },
    {
        "id": "followup",
        "icon": "🔄",
        "title": "বিকেলের Follow-up (3:00–4:00 PM)",
        "desc": "Reply-দের সাথে যোগাযোগ করো, call schedule করো",
        "tasks": [
            {
                "id": "followup_replies",
                "title": "Reply-দের সাথে কথা বলো",
                "freq": "daily",
                "guide": (
                    "📌 যারা reply করেছে তাদের সাথে কীভাবে কথা বলবে:\n"
                    "\n"
                    "1️⃣  সকালে inbox চেক করে list করো কারা reply করেছে\n"
                    "2️⃣  প্রতিটি reply-এ ব্যক্তিগতভাবে সাড়া দাও\n"
                    "3️⃣  আগ্রহীকে বলো: 'আপনার সাথে 15 মিনিট কথা বলতে পারি?'\n"
                    "4️⃣  Calendly বা Google Calendar link দাও\n"
                    "\n"
                    "Sample response:\n"
                    "  'ধন্যবাদ reply করার জন্য! আপনার business-এর জন্য\n"
                    "   specific কিছু ideas আছে আমার। ১৫ মিনিট কথা বলবেন?'\n"
                ),
                "command": None,
            },
            {
                "id": "followup_calls",
                "title": "Call Schedule করো",
                "freq": "daily",
                "guide": (
                    "📌 আগ্রহী lead-দের সাথে discovery call schedule করো।\n"
                    "\n"
                    "বিনামূল্যে scheduling tool:\n"
                    "  Calendly: calendly.com (free plan আছে)\n"
                    "  Google Calendar: calendar.google.com\n"
                    "\n"
                    "Call-এ যা জিজ্ঞেস করবে:\n"
                    "  1. আপনার এখন সবচেয়ে বড় marketing চ্যালেঞ্জ কী?\n"
                    "  2. মাসে marketing-এ কতটাকা invest করতে পারবেন?\n"
                    "  3. Website/Social media আছে কিনা?\n"
                    "  4. আগে কোনো agency-র সাথে কাজ করেছেন কিনা?\n"
                ),
                "command": None,
            },
            {
                "id": "followup_crm",
                "title": "Airtable/CRM আপডেট করো",
                "freq": "daily",
                "guide": (
                    "📌 প্রতিটি lead-এর latest status CRM-এ রাখো।\n"
                    "\n"
                    "Airtable (বিনামূল্যে):\n"
                    "  airtable.com → New Base → Import CSV → tracking/leads.csv\n"
                    "\n"
                    "অথবা শুধু tracking/leads.csv আপডেট করো:\n"
                    "  status, replied_at, converted_at কলাম আপডেট করো\n"
                    "\n"
                    "কেন CRM গুরুত্বপূর্ণ?\n"
                    "  → কোন lead কোথায় আছে track রাখতে\n"
                    "  → Revenue forecast করতে\n"
                    "  → Follow-up কখন করতে হবে মনে রাখতে\n"
                ),
                "command": None,
            },
        ],
    },
    {
        "id": "weekly",
        "icon": "📅",
        "title": "সাপ্তাহিক কাজ (প্রতি সোমবার)",
        "desc": "Report তৈরি করো, A-grade lead review করো, নতুন niche যোগ করো",
        "tasks": [
            {
                "id": "weekly_report",
                "title": "সাপ্তাহিক Report তৈরি করো",
                "freq": "weekly",
                "guide": (
                    "📌 গত সপ্তাহের সব activity-র report generate করো।\n"
                    "\n"
                    "  python scripts/generate_report.py --period weekly\n"
                    "\n"
                    "Report-এ থাকবে:\n"
                    "  - কতটি নতুন লিড পাওয়া গেছে\n"
                    "  - কতটি ইমেইল পাঠানো হয়েছে\n"
                    "  - Open rate / Reply rate\n"
                    "  - Converted leads\n"
                    "  - Revenue achieved vs target\n"
                    "\n"
                    "HTML report: data/reports/ ফোল্ডারে save হবে\n"
                ),
                "command": "python scripts/generate_report.py --period weekly --format html",
            },
            {
                "id": "weekly_a_leads",
                "title": "A-Grade Leads যারা reply করেনি তাদের review করো",
                "freq": "weekly",
                "guide": (
                    "📌 Grade A lead মানে সবচেয়ে ভালো prospect।\n"
                    "তারা reply না করলে একটু ভিন্নভাবে approach করো।\n"
                    "\n"
                    "A-grade leads দেখতে:\n"
                    "  grep 'A,' tracking/leads.csv | head -20\n"
                    "\n"
                    "এদের জন্য:\n"
                    "  1. LinkedIn-এ connect করো\n"
                    "  2. তাদের business visit করো (যদি কাছে হয়)\n"
                    "  3. ভিন্ন subject line দিয়ে ইমেইল করো\n"
                    "  4. Social media-তে তাদের post-এ comment করো\n"
                ),
                "command": None,
            },
            {
                "id": "weekly_new_niche",
                "title": "নতুন Niche/Location যোগ করো",
                "freq": "weekly",
                "guide": (
                    "📌 একটা niche saturate হয়ে গেলে নতুন niche try করো।\n"
                    "\n"
                    "Available niches: restaurant, dentist, lawyer, real estate,\n"
                    "                  gym, salon, plumber, electrician, hotel, pharmacy\n"
                    "\n"
                    "নতুন নিশ research করো:\n"
                    "  python scripts/run_research.py --niche dentist --location \"Chicago, IL\" --count 30\n"
                    "\n"
                    "কোন niche সবচেয়ে ভালো response দিচ্ছে সেটাতে বেশি focus করো।\n"
                ),
                "command": None,
            },
            {
                "id": "weekly_backup",
                "title": "Data Backup করো",
                "freq": "weekly",
                "guide": (
                    "📌 tracking/ ফোল্ডারের সব data backup করো।\n"
                    "\n"
                    "  cp -r tracking/ tracking_backup_$(date +%Y%m%d)/\n"
                    "\n"
                    "অথবা Google Drive-এ upload করো:\n"
                    "  tracking/leads.csv → Google Sheets-এ import\n"
                    "\n"
                    "GitHub-এ push করো (api_keys.env ছাড়া):\n"
                    "  git add tracking/leads.csv\n"
                    "  git commit -m 'weekly backup'\n"
                    "  git push\n"
                ),
                "command": None,
            },
        ],
    },
    {
        "id": "monthly",
        "icon": "📆",
        "title": "মাসিক কাজ",
        "desc": "Revenue review, template optimize, scoring update, next month plan",
        "tasks": [
            {
                "id": "monthly_revenue",
                "title": "Revenue vs Target Review করো",
                "freq": "monthly",
                "guide": (
                    "📌 এই মাসে কতটাকা আয় হয়েছে এবং target কতটা ছিল।\n"
                    "\n"
                    "Monthly report:\n"
                    "  python scripts/generate_report.py --period monthly\n"
                    "\n"
                    "Revenue targets (Year 1):\n"
                    "  মাস ১-৩:  $10,000–$20,000/মাস  (৫–১০ জন client)\n"
                    "  মাস ৪-৬:  $30,000–$50,000/মাস  (১৫–২৫ জন client)\n"
                    "  মাস ৭-৯:  $60,000–$80,000/মাস  (৩০–৪০ জন client)\n"
                    "  মাস ১০-১২: $90,000–$100,000/মাস (৪৫–৫০ জন client)\n"
                    "\n"
                    "Target miss করলে:\n"
                    "  → Lead volume বাড়াও\n"
                    "  → Closing rate উন্নত করো\n"
                    "  → Pricing strategy review করো\n"
                ),
                "command": "python scripts/generate_report.py --period monthly --format html",
            },
            {
                "id": "monthly_templates",
                "title": "Email Template Optimize করো",
                "freq": "monthly",
                "guide": (
                    "📌 কোন email template সবচেয়ে বেশি open/reply পাচ্ছে সেটা দেখো।\n"
                    "\n"
                    "Templates: templates/ ফোল্ডারে আছে\n"
                    "\n"
                    "A/B testing করো:\n"
                    "  - Subject line পরিবর্তন করো\n"
                    "  - Email length কম/বেশি করো\n"
                    "  - Call-to-action পরিবর্তন করো\n"
                    "\n"
                    "Best performing template-এর pattern দিয়ে নতুন template লেখো।\n"
                    "\n"
                    "Template files:\n"
                    "  templates/initial_outreach.html\n"
                    "  templates/follow_up_1.html\n"
                    "  templates/follow_up_2.html\n"
                ),
                "command": None,
            },
            {
                "id": "monthly_scoring",
                "title": "Lead Scoring Criteria আপডেট করো",
                "freq": "monthly",
                "guide": (
                    "📌 কোন ধরনের lead বেশি convert হচ্ছে সেটা বুঝে scoring আপডেট করো।\n"
                    "\n"
                    "Scoring file: src/ai/lead_scorer.py\n"
                    "\n"
                    "বর্তমান scoring criteria:\n"
                    "  - Google Rating (0–5 star)\n"
                    "  - Review count\n"
                    "  - Website আছে কিনা\n"
                    "  - Social media presence\n"
                    "  - Business age\n"
                    "\n"
                    "যদি দেখো restaurant বেশি convert হচ্ছে, restaurant-এর weight বাড়াও।\n"
                ),
                "command": None,
            },
            {
                "id": "monthly_plan",
                "title": "পরের মাসের Plan করো",
                "freq": "monthly",
                "guide": (
                    "📌 পরের মাসের জন্য target set করো।\n"
                    "\n"
                    "চেকলিস্ট:\n"
                    "  □ কতটি lead target করব? (প্রতি সপ্তাহে ৫০–৫০০)\n"
                    "  □ কোন niche-এ focus করব?\n"
                    "  □ কোন location expand করব?\n"
                    "  □ Budget কত?\n"
                    "  □ নতুন কোনো service add করব?\n"
                    "\n"
                    "এই app-এর progress reset করতে চাইলে:\n"
                    "  tracking/app_progress.json ফাইল delete করো।\n"
                ),
                "command": None,
            },
        ],
    },
]


# ──────────────────────────────────────────
# Progress Manager
# ──────────────────────────────────────────

class ProgressManager:
    """Progress JSON ফাইলে save/load করে।"""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.data: dict = self._load()

    def _load(self) -> dict:
        if self.filepath.exists():
            try:
                with open(self.filepath, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save(self) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def is_done(self, task_id: str, today_only: bool = False) -> bool:
        """কোনো task done কিনা।"""
        if task_id not in self.data:
            return False
        record = self.data[task_id]
        if today_only:
            return record.get("last_done", "") == date.today().isoformat()
        return record.get("done", False)

    def mark_done(self, task_id: str) -> None:
        today = date.today().isoformat()
        self.data[task_id] = {
            "done": True,
            "last_done": today,
            "done_count": self.data.get(task_id, {}).get("done_count", 0) + 1,
        }
        self.save()

    def mark_undone(self, task_id: str) -> None:
        if task_id in self.data:
            self.data[task_id]["done"] = False
        self.save()

    def pending_tasks(self) -> list[dict]:
        """আজকের জন্য বাকি daily tasks।"""
        pending = []
        today = date.today().isoformat()
        for section in SECTIONS:
            for task in section["tasks"]:
                tid = task["id"]
                freq = task["freq"]
                if freq == "once":
                    if not self.is_done(tid):
                        pending.append({"section": section["title"], **task})
                elif freq == "daily":
                    last = self.data.get(tid, {}).get("last_done", "")
                    if last != today:
                        pending.append({"section": section["title"], **task})
        return pending


# ──────────────────────────────────────────
# Display Helpers
# ──────────────────────────────────────────

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header() -> None:
    print(clr("═" * 60, "cyan"))
    print(clr("  🚀 Agency Research Automation — গাইড অ্যাপ", "bold"))
    print(clr("  Owner: Md Jamil Islam  |  Target: $1,000,000/year", "dim"))
    print(clr("═" * 60, "cyan"))
    print()


def print_task_status(task: dict, progress: ProgressManager) -> str:
    """Task line দেখাও।"""
    freq = task["freq"]
    done = False
    if freq == "once":
        done = progress.is_done(task["id"])
    elif freq == "daily":
        done = progress.is_done(task["id"], today_only=True)
    elif freq in ("weekly", "monthly"):
        done = progress.is_done(task["id"])

    tick = clr("✅", "green") if done else clr("⬜", "dim")
    count = progress.data.get(task["id"], {}).get("done_count", 0)
    count_str = clr(f" (×{count})", "dim") if count > 0 else ""
    return f"  {tick}  {task['title']}{count_str}"


# ──────────────────────────────────────────
# Screens
# ──────────────────────────────────────────

def show_main_menu(progress: ProgressManager) -> None:
    """Main menu দেখাও।"""
    clear_screen()
    print_header()

    # Reminder
    pending = progress.pending_tasks()
    if pending:
        print(clr(f"  ⏰ Reminder: আজকের {len(pending)}টি কাজ বাকি আছে!", "yellow"))
        print()

    print(clr("  📋 SECTIONS:", "bold"))
    print()
    for i, section in enumerate(SECTIONS, 1):
        total = len(section["tasks"])
        done_count = sum(
            1 for t in section["tasks"]
            if (t["freq"] == "once" and progress.is_done(t["id"]))
            or (t["freq"] == "daily" and progress.is_done(t["id"], today_only=True))
            or (t["freq"] in ("weekly", "monthly") and progress.is_done(t["id"]))
        )
        bar = clr(f"[{done_count}/{total}]", "green" if done_count == total else "yellow")
        print(f"  {clr(str(i), 'cyan')}.  {section['icon']}  {section['title']}  {bar}")
        print(clr(f"       {section['desc']}", "dim"))
        print()

    print(clr("  R.  ⏰ আজকের Reminder দেখো", "yellow"))
    print(clr("  Q.  ❌ বের হও", "red"))
    print()
    print(clr("═" * 60, "cyan"))


def show_section(section: dict, progress: ProgressManager) -> None:
    """একটা section দেখাও।"""
    while True:
        clear_screen()
        print_header()
        print(clr(f"  {section['icon']}  {section['title']}", "bold"))
        print(clr(f"  {section['desc']}", "dim"))
        print(clr("  " + "─" * 56, "cyan"))
        print()

        for i, task in enumerate(section["tasks"], 1):
            print(f"  {clr(str(i), 'cyan')}.  {print_task_status(task, progress)}")
            freq_label = {
                "once": clr("[একবার]", "blue"),
                "daily": clr("[প্রতিদিন]", "green"),
                "weekly": clr("[সাপ্তাহিক]", "yellow"),
                "monthly": clr("[মাসিক]", "magenta"),
            }.get(task["freq"], "")
            print(f"       {freq_label}")
            print()

        print(clr("  B.  ← পেছনে যাও", "dim"))
        print()
        print(clr("═" * 60, "cyan"))
        choice = input(clr("  কোন task দেখবে? (নম্বর দাও): ", "cyan")).strip().upper()

        if choice == "B" or choice == "":
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(section["tasks"]):
                show_task(section["tasks"][idx], progress)
        except ValueError:
            pass


def show_task(task: dict, progress: ProgressManager) -> None:
    """একটা task-এর detail guide দেখাও।"""
    while True:
        clear_screen()
        print_header()

        freq_label = {
            "once": clr("একবার করলেই হবে", "blue"),
            "daily": clr("প্রতিদিন", "green"),
            "weekly": clr("প্রতি সোমবার", "yellow"),
            "monthly": clr("প্রতি মাসে", "magenta"),
        }.get(task["freq"], task["freq"])

        print(clr(f"  📌 {task['title']}", "bold"))
        print(clr(f"  Frequency: {freq_label}", "dim"))
        print(clr("  " + "─" * 56, "cyan"))
        print()

        # Guide
        for line in task["guide"].splitlines():
            if line.startswith("  ") or line.startswith("    "):
                print(clr(line, "dim"))
            elif line.startswith("📌") or line.startswith("⚠️"):
                print(clr(f"  {line}", "yellow"))
            elif line.strip() == "":
                print()
            else:
                print(f"  {line}")
        print()

        # Status
        done = progress.is_done(
            task["id"],
            today_only=(task["freq"] == "daily"),
        )
        status_str = clr("✅ সম্পন্ন!", "green") if done else clr("⬜ বাকি আছে", "yellow")
        print(clr("  " + "─" * 56, "cyan"))
        print(f"  Status: {status_str}")
        print()

        # Options
        if task["command"]:
            print(clr("  1.  ▶️  Command চালাও", "green"))
        print(clr("  2.  ✅ সম্পন্ন হিসেবে Mark করো", "green") if not done else
              clr("  2.  ↩️  Undo (সম্পন্ন চিহ্ন সরাও)", "yellow"))
        print(clr("  B.  ← পেছনে যাও", "dim"))
        print()
        print(clr("═" * 60, "cyan"))
        choice = input(clr("  কী করবে?: ", "cyan")).strip().upper()

        if choice == "B" or choice == "":
            break
        elif choice == "1" and task["command"]:
            run_command(task["command"])
        elif choice == "2":
            if done:
                progress.mark_undone(task["id"])
                print(clr("\n  ↩️  Undo করা হয়েছে।", "yellow"))
            else:
                progress.mark_done(task["id"])
                print(clr("\n  ✅ দারুণ! কাজটা সম্পন্ন হিসেবে Mark হয়েছে।", "green"))
            input(clr("  [Enter চাপো] ", "dim"))


def run_command(cmd: str) -> None:
    """Command চালাও এবং output দেখাও।"""
    print()
    print(clr(f"  ▶️  চালাচ্ছি: {cmd}", "cyan"))
    print(clr("  " + "─" * 56, "dim"))
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(BASE_DIR),
            capture_output=False,
            text=True,
        )
        print()
        if result.returncode == 0:
            print(clr("  ✅ Command সফলভাবে চলেছে!", "green"))
        else:
            print(clr(f"  ⚠️  Exit code: {result.returncode}", "yellow"))
    except Exception as exc:  # noqa: BLE001
        print(clr(f"  ❌ Command চালাতে সমস্যা হয়েছে: {exc}", "red"))
        print(clr("  বিস্তারিত:", "dim"))
        for line in traceback.format_exc().splitlines():
            print(clr(f"    {line}", "dim"))
    print()
    input(clr("  [Enter চাপো] ", "dim"))


def show_reminders(progress: ProgressManager) -> None:
    """আজকের বাকি কাজ দেখাও।"""
    clear_screen()
    print_header()
    print(clr("  ⏰ আজকের Reminder", "bold"))
    print(clr("  " + "─" * 56, "cyan"))
    print()

    pending = progress.pending_tasks()
    if not pending:
        print(clr("  🎉 আজকের সব কাজ শেষ! দারুণ!", "green"))
    else:
        print(clr(f"  {len(pending)}টি কাজ এখনো বাকি:\n", "yellow"))
        for task in pending:
            section_name = task.get("section", "")
            print(f"  ⬜  {clr(task['title'], 'bold')}")
            print(clr(f"       Section: {section_name}", "dim"))
            print()

    print()
    print(clr("═" * 60, "cyan"))
    input(clr("  [Enter চাপো] ", "dim"))


# ──────────────────────────────────────────
# Main App Loop
# ──────────────────────────────────────────

def main() -> None:
    """Main app loop।"""
    progress = ProgressManager(PROGRESS_FILE)

    while True:
        show_main_menu(progress)
        choice = input(clr("  কোন section-এ যাবে? (নম্বর/R/Q): ", "cyan")).strip().upper()

        if choice == "Q":
            clear_screen()
            print(clr("\n  👋 আবার দেখা হবে! ভালো থেকো।\n", "cyan"))
            sys.exit(0)
        elif choice == "R":
            show_reminders(progress)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(SECTIONS):
                    show_section(SECTIONS[idx], progress)
            except ValueError:
                pass


if __name__ == "__main__":
    main()
