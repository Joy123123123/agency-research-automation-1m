# 🤖 Automation Guide

**Creator:** Md Jamil Islam  
**Purpose:** How to run and use the automation scripts effectively

---

## Overview

The scripts in `scripts/` automate the most time-consuming parts of the business:

| Script | What it does | Run it |
|--------|-------------|--------|
| `lead_generation.py` | Finds marketing agency leads | Daily |
| `research_automation.py` | Generates research reports | Per client |
| `email_outreach.py` | Creates email schedules | Daily |
| `data_processor.py` | Analyzes your metrics | Weekly |

---

## Running the Scripts

### Step 1: Setup
```bash
cd scripts/
pip install -r requirements.txt
```

### Step 2: Generate Leads
```bash
python lead_generation.py
```
Output: `tracking/client_tracker.csv` with 50 sample leads

### Step 3: Create Research Reports
```bash
python research_automation.py
```
Output: 3 sample reports in `templates/`

### Step 4: Plan Email Outreach
```bash
python email_outreach.py
```
Output: `tracking/outreach_schedule.csv` with email tasks

### Step 5: Analyze Metrics
```bash
python data_processor.py
```
Output: Summary report in `tracking/`

---

## Daily Automation Workflow

Run these every morning:
```bash
# 1. Check and update leads
python scripts/lead_generation.py

# 2. Generate reports for active clients
python scripts/research_automation.py

# 3. Get today's email tasks
python scripts/email_outreach.py

# 4. Check metrics
python scripts/data_processor.py
```

---

## Customizing the Scripts

### Change Number of Leads Generated
In `lead_generation.py`, line with `generate_sample_leads(count=50)`:
```python
leads = generate_sample_leads(count=100)  # change to 100
```

### Change Report Niche
In `research_automation.py`, update the `samples` list:
```python
samples = [
    {"company": "Your Client Name", "client": "Client A", "niche": "your niche"},
]
```

### Change Email Templates
In `email_outreach.py`, update the `EMAIL_TEMPLATES` dictionary with your custom templates.

---

## GitHub Actions (Optional Advanced Automation)

To run scripts automatically every day, create `.github/workflows/daily_automation.yml`:

```yaml
name: Daily Automation
on:
  schedule:
    - cron: '0 8 * * 1-5'  # 8am, Mon-Fri
jobs:
  run-scripts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/lead_generation.py
      - run: python scripts/data_processor.py
```

---

## Troubleshooting

### "Module not found" error
```bash
pip install -r scripts/requirements.txt
```

### "File not found" error
Make sure you're running scripts from the root directory:
```bash
cd /path/to/agency-research-automation-1m
python scripts/lead_generation.py
```

### CSV file is empty
Run `lead_generation.py` first before other scripts.

---

*For tool setup, see `resources/tools_setup.md`*  
*For premium support, see `PREMIUM_REQUEST.md`*
