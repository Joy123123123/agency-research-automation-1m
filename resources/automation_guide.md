# ⚙️ Automation Guide

**Author:** Md Jamil Islam
**Purpose:** How to automate research, outreach, and reporting end-to-end

---

## Overview

This guide explains how to automate the key workflows in the Agency Research Automation system. Each script handles a specific part of the process.

---

## 1. Lead Generation Automation

**Script:** `scripts/lead_generation.py`

### What It Does
- Searches for marketing agencies by niche and location
- Filters by company size
- Exports to CSV for tracking

### How to Run
```bash
cd scripts
python lead_generation.py
```

### Output
- `tracking/client_tracker.csv` — Populated with new agency leads

### Configuration (in script)
```python
niches = ["SEO", "PPC", "social media", "content marketing"]
locations = ["New York", "London", "Toronto", "Sydney"]
daily_limit = 50  # Leads per run
```

---

## 2. Research Automation

**Script:** `scripts/research_automation.py`

### What It Does
- Generates competitor analysis reports for active clients
- Produces industry trend summaries
- Exports reports as JSON (convertible to PDF)

### How to Run
```bash
# Single client
python research_automation.py

# Batch (all active clients)
# Edit batch_research() call at bottom of script
python research_automation.py
```

### Output
- `reports/[client_name]_[date].json` — Research report files

---

## 3. Email Outreach Automation

**Script:** `scripts/email_outreach.py`

### What It Does
- Loads email templates
- Personalizes emails per contact
- Sends cold outreach campaigns
- Respects daily send limits (default: 20/day)

### Setup Required
Add SMTP credentials to `.env`:
```
EMAIL_USERNAME=your@email.com
EMAIL_PASSWORD=your_password
```

### How to Run
```bash
python email_outreach.py
```

### Safety Guidelines
- Never send more than 50 emails/day from one account
- Warm up new email accounts (start at 10/day, increase gradually)
- Use personalization to avoid spam filters
- Always include unsubscribe option

---

## 4. Data Processing & Reporting

**Script:** `scripts/data_processor.py`

### What It Does
- Calculates business metrics (reply rates, close rates, revenue)
- Generates weekly performance summaries
- Merges CSV files from multiple sources

### How to Run
```bash
python data_processor.py
```

### Output
```
=== WEEKLY PERFORMANCE SUMMARY ===
Total emails sent:   150
Total replies:       18
Reply rate:          12.0%
Discovery calls:     6
Proposals sent:      4
New clients:         2
Close rate:          33.3%
Total revenue:       $3,000.00
===================================
```

---

## 5. GitHub Actions Automation (Advanced)

You can automate weekly research runs using GitHub Actions.

### Create `.github/workflows/weekly_research.yml`:
```yaml
name: Weekly Research Automation

on:
  schedule:
    - cron: '0 8 * * 1'  # Every Monday at 8 AM UTC

jobs:
  research:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r scripts/requirements.txt
      - name: Run research automation
        run: python scripts/research_automation.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Add GitHub Secrets:
1. Repository → Settings → Secrets and variables → Actions
2. Add: `OPENAI_API_KEY`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`

---

## 6. Full Workflow (End-to-End)

```
Week 1:
  Monday    → Run lead_generation.py (get 50 new leads)
  Tue–Thu   → Run email_outreach.py (send 20/day)
  Friday    → Run data_processor.py (weekly metrics)

Every day:
  Morning   → Check replies, schedule calls
  Afternoon → Run research_automation.py for active clients
  Evening   → Update tracking CSVs
```

---

## 7. Zapier Automation (No-Code Alternative)

If you prefer no-code automation:

### Workflow 1: New Lead → Auto-Email
- Trigger: New row in Google Sheets (client_tracker)
- Action: Send email via Gmail

### Workflow 2: New Client → Onboarding
- Trigger: Status changed to "active" in Sheets
- Action: Send welcome email + create task in Trello/Notion

### Workflow 3: Weekly Report Reminder
- Trigger: Every Friday at 9 AM
- Action: Send reminder email to yourself

---

*Created by Md Jamil Islam | Agency Research Automation*
