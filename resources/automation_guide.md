# 🤖 Automation Guide — Agency Research Automation

**Owner:** Md Jamil Islam  
**Goal:** Automate 70–80% of repetitive research and outreach tasks

---

## Overview: The Automation Stack

```
Lead Generation  →  Data Processing  →  Email Outreach  →  Tracking
     ↓                    ↓                   ↓               ↓
lead_generation.py  data_processor.py  email_outreach.py  CSV tracking
```

**Manual work remaining:** Personalizing emails, conducting discovery calls, writing reports, closing clients.

---

## Step 1: Generate Leads Automatically

### Basic Usage
```bash
# Generate 100 leads (default settings)
python scripts/lead_generation.py

# Generate leads for a specific niche
python scripts/lead_generation.py --niche "SaaS company" --max-leads 50

# Save to a custom location
python scripts/lead_generation.py --output output/my_leads.csv
```

### Output
- `output/leads.csv` — Formatted lead list
- `output/leads.json` — Same data in JSON format
- `logs/lead_generation.log` — Execution log

### Customizing Lead Sources
Open `scripts/lead_generation.py` and modify `DEFAULT_CONFIG`:
```python
DEFAULT_CONFIG = {
    "niches": ["your target niche"],
    "target_employee_range": (10, 100),  # Company size
    "target_regions": ["United States"],  # Geography
    "max_leads": 100,
}
```

---

## Step 2: Clean and Validate Your Lead List

```bash
# Clean a leads CSV file (removes invalid emails, duplicates)
python scripts/data_processor.py output/leads.csv

# With minimum quality score filter
python scripts/data_processor.py output/leads.csv --min-score 60

# Custom output location
python scripts/data_processor.py output/leads.csv --output output/leads_clean.csv
```

### What It Does
1. ✅ Validates all email addresses
2. ✅ Normalizes phone numbers
3. ✅ Fixes URL formatting
4. ✅ Removes duplicates
5. ✅ Filters by quality score
6. ✅ Sorts by score (highest first)

---

## Step 3: Research a Specific Company

```bash
# Research a company
python scripts/research_automation.py "Bright Digital Agency"

# With additional details
python scripts/research_automation.py "CloudFlow SaaS" \
  --website "https://cloudflow.io" \
  --industry "SaaS" \
  --location "San Francisco, USA" \
  --output "output/cloudflow_research"
```

### Output
- `output/research_[company]_[date].md` — Formatted report
- `output/profile_[company].json` — Raw data file

### Extending the Research Script
In production, replace placeholder functions with real API calls:

```python
# In research_automation.py, replace generate_sample_leads() with:
import requests

def research_company_basics(profile):
    # Apollo.io API
    response = requests.get(
        "https://api.apollo.io/v1/organizations/search",
        headers={"X-Api-Key": os.getenv("APOLLO_API_KEY")},
        params={"q_organization_name": profile["company_name"]}
    )
    data = response.json()
    # Parse and fill profile...
    return profile
```

---

## Step 4: Run an Email Campaign

### Dry Run First (Always Test)
```bash
# Preview emails without sending (default mode)
python scripts/email_outreach.py --leads output/leads_clean.csv --template cold_intro --dry-run

# Preview follow-up emails
python scripts/email_outreach.py --leads output/leads_clean.csv --template follow_up_1
```

### Send Real Emails (After Setup)
```bash
# Ensure SMTP credentials are in .env file, then:
python scripts/email_outreach.py \
  --leads output/leads_clean.csv \
  --template cold_intro \
  --send \
  --max 30 \
  --delay 60
```

### Available Templates
| Template | When to Use |
|---------|-------------|
| `cold_intro` | First contact |
| `follow_up_1` | 3 days after no reply |
| `follow_up_2` | 7 days after no reply |
| `proposal_follow_up` | After sending proposal |

---

## Step 5: Full Pipeline (End-to-End)

Create a `run_pipeline.sh` script to automate everything:

```bash
#!/bin/bash
# Full automation pipeline — run daily

echo "🚀 Starting daily pipeline..."

# Step 1: Generate fresh leads
python scripts/lead_generation.py --max-leads 50 --output output/daily_leads.csv

# Step 2: Clean and validate
python scripts/data_processor.py output/daily_leads.csv \
  --output output/daily_leads_clean.csv \
  --min-score 50

# Step 3: Send outreach (cold intro to new leads)
python scripts/email_outreach.py \
  --leads output/daily_leads_clean.csv \
  --template cold_intro \
  --send \
  --max 20 \
  --delay 90

echo "✅ Pipeline complete!"
```

Run with:
```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

---

## Scheduling with Cron (Linux/Mac)

Run the pipeline automatically every morning at 9 AM:

```bash
# Open cron editor
crontab -e

# Add this line:
0 9 * * 1-5 /usr/bin/python3 /path/to/scripts/lead_generation.py >> /path/to/logs/cron.log 2>&1
```

---

## Connecting Real APIs

### Apollo.io API (Lead Enrichment)
```python
import requests
import os

def get_apollo_leads(keyword, per_page=10):
    url = "https://api.apollo.io/v1/mixed_people/search"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": os.getenv("APOLLO_API_KEY"),
    }
    payload = {
        "q_keywords": keyword,
        "per_page": per_page,
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get("people", [])
```

### Hunter.io API (Email Finding)
```python
def find_email_hunter(first_name, last_name, domain):
    url = "https://api.hunter.io/v2/email-finder"
    params = {
        "first_name": first_name,
        "last_name": last_name,
        "domain": domain,
        "api_key": os.getenv("HUNTER_API_KEY"),
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("data", {}).get("email", "")
```

### Clearbit API (Company Enrichment)
```python
def enrich_company(domain):
    url = f"https://company.clearbit.com/v2/companies/find"
    response = requests.get(
        url,
        params={"domain": domain},
        auth=(os.getenv("CLEARBIT_API_KEY"), ""),
    )
    return response.json() if response.status_code == 200 else {}
```

---

## Error Handling & Monitoring

### Check Logs
```bash
# View lead generation log
cat logs/lead_generation.log

# View email outreach log
cat logs/email_outreach.log

# Watch logs in real-time
tail -f logs/lead_generation.log
```

### Common Issues & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `SMTP authentication failed` | Wrong credentials | Check `.env` SMTP settings |
| `Rate limit exceeded` | Too many API calls | Add `time.sleep()` between requests |
| `File not found` | Missing output dir | Run `mkdir -p output logs` |
| `ModuleNotFoundError` | Missing package | Run `pip install -r requirements.txt` |

---

## Security Checklist

- [ ] `.env` file is in `.gitignore` (never commit API keys!)
- [ ] No credentials hardcoded in any script
- [ ] API keys have minimum required permissions
- [ ] Output files with personal data are in `output/` (gitignored)
- [ ] Log files don't contain sensitive data

---

*The goal is 80% automation, 20% high-value human touch. Automate the repetitive; personalize the important.*
