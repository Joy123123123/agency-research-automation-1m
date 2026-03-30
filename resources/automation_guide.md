# ⚙️ Automation Guide

Complete guide to automating your agency research business end-to-end.

---

## Overview

The goal is to spend as little manual time as possible on repetitive tasks
while maintaining high quality. Below is the full automation stack.

```
AUTOMATION STACK

Daily (automated):
├── Lead generation (Apollo.io API → client_tracker.csv)
├── Email sending (email_outreach.py → Gmail/lemlist)
└── Research data gathering (research_automation.py)

Weekly (semi-automated):
├── Report generation (research_automation.py + human review)
├── Metrics update (data_processor.py --report all)
└── Follow-up sequences (lemlist automations)

Monthly (manual with automation support):
├── Client delivery (report generation + formatting)
├── Revenue tracking (manual update to revenue_tracker.csv)
└── Business review (data_processor.py --report all)
```

---

## 1. Daily Automation

### Script: Automated Lead Generation

**What it does:** Finds 20 new marketing agency leads every weekday morning.

**Setup via GitHub Actions:**

Create `.github/workflows/daily_leads.yml`:
```yaml
name: Daily Lead Generation
on:
  schedule:
    - cron: '0 8 * * 1-5'  # 8 AM UTC weekdays
jobs:
  generate-leads:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r scripts/requirements.txt
      - name: Generate leads
        run: python scripts/lead_generation.py --count 20
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
          HUNTER_API_KEY: ${{ secrets.HUNTER_API_KEY }}
      - name: Commit updated tracker
        run: |
          git config user.name "Automation Bot"
          git config user.email "bot@github.com"
          git add tracking/client_tracker.csv
          git commit -m "Daily lead update $(date +%Y-%m-%d)" || exit 0
          git push
```

**Manual execution:**
```bash
python scripts/lead_generation.py --industry "marketing agency" --country US --count 20
```

---

### Script: Automated Email Outreach

**What it does:** Sends personalized cold emails to new leads.

**Manual execution:**
```bash
# Send cold outreach to 20 new leads
python scripts/email_outreach.py --template cold_outreach --leads 20

# Send follow-ups to contacted leads (change status filter in script)
python scripts/email_outreach.py --template follow_up --leads 15

# Dry run first to preview emails
python scripts/email_outreach.py --dry-run --template cold_outreach --leads 5
```

**Recommended daily schedule:**
- 9:00 AM: Run cold_outreach (20 emails)
- 12:00 PM: Run follow_up (10-15 emails)

**Using lemlist instead (recommended for 50+ emails/day):**
1. Export `client_tracker.csv` (status = "new") to lemlist
2. Create sequence: Email 1 → Wait 3 days → Email 2 → Wait 4 days → Email 3
3. Set sending time: 8 AM - 12 PM (prospect's timezone)
4. lemlist handles follow-ups automatically

---

## 2. Research Automation

### Script: Research Report Generation

**What it does:** Calls Perplexity AI and OpenAI to research topics and generates
a structured markdown report.

**Manual execution:**
```bash
# Generate a full research report
python scripts/research_automation.py \
    --client "Acme Marketing Agency" \
    --company "Their Target Company" \
    --industry "SaaS marketing" \
    --location "United States" \
    --topics "industry_overview,competitor_analysis,target_audience"

# Available topics:
# industry_overview, competitor_analysis, target_audience,
# keyword_opportunities, content_strategy
```

**Output:** Markdown file in `reports/` folder

**Post-generation steps:**
1. Open the generated report
2. Customize the "Recommendations" section with client-specific insights
3. Convert to PDF (VS Code → Export to PDF, or Pandoc)
4. Send to client via email or Google Drive

---

### Batch Research for Multiple Clients

Create a client config file `/tmp/clients.json`:
```json
[
  {
    "client": "Agency A",
    "company": "Their Client Company",
    "industry": "e-commerce marketing",
    "topics": "competitor_analysis,keyword_opportunities"
  },
  {
    "client": "Agency B",
    "company": "Their Client Company",
    "industry": "B2B SaaS",
    "topics": "industry_overview,content_strategy"
  }
]
```

Run for all clients:
```bash
python -c "
import json, subprocess
with open('/tmp/clients.json') as f:
    clients = json.load(f)
for c in clients:
    subprocess.run([
        'python', 'scripts/research_automation.py',
        '--client', c['client'],
        '--company', c['company'],
        '--industry', c['industry'],
        '--topics', c['topics']
    ])
"
```

---

## 3. Data Processing & Reporting

### Clean and Deduplicate Leads

Run weekly to maintain data quality:
```bash
# Remove duplicates
python scripts/data_processor.py --input tracking/client_tracker.csv --dedupe

# Clean and normalize data
python scripts/data_processor.py --input tracking/client_tracker.csv --clean

# Do both
python scripts/data_processor.py --input tracking/client_tracker.csv --clean --dedupe
```

---

### Generate Business Reports

```bash
# View email metrics
python scripts/data_processor.py --report metrics

# View revenue summary
python scripts/data_processor.py --report revenue

# View lead pipeline
python scripts/data_processor.py --report pipeline

# View everything
python scripts/data_processor.py --report all
```

**Sample output:**
```
============================================================
  Agency Research Automation - ALL REPORT
  Generated: 2024-03-15 09:00:00
============================================================

📧 EMAIL METRICS
   Total Sent:   142
   Total Failed: 3
   By Campaign:
     - cold_outreach: 100
     - follow_up: 42

💰 REVENUE SUMMARY
   Active Clients:    8
   MRR:               $10,000.00
   Total Collected:   $15,000.00
   Annual Run Rate:   $120,000.00
   Progress to $1M:   12.0%

🎯 LEAD PIPELINE
   contacted            : 45
   new                  : 78
   proposal_sent        : 12
   closed_won           : 8
   discovery_scheduled  : 7
```

---

## 4. End-to-End Workflow

### Automated Daily Flow

```
8:00 AM  → GitHub Actions runs lead_generation.py (20 new leads added)
9:00 AM  → You manually trigger email_outreach.py (or lemlist auto-sends)
12:00 PM → Follow-up emails sent
3:00 PM  → Research reports generated for active clients
5:00 PM  → Review replies, update CRM, schedule calls
```

### Weekly Flow (Monday)

```
1. Run: python scripts/data_processor.py --report all
2. Review metrics — adjust outreach volume if needed
3. Export any new "new" leads to lemlist for sequences
4. Generate research reports for clients due this week
5. Schedule check-in calls with active clients
```

### Monthly Flow (1st of month)

```
1. Generate all client research reports
2. Quality review each report (1 hour)
3. Deliver reports to clients via Google Drive
4. Update revenue_tracker.csv with new payments
5. Run: python scripts/data_processor.py --report all
6. Review: client retention, MRR growth, lead metrics
7. Plan next month's outreach strategy
```

---

## 5. Scaling the Automation

### Month 1-2: Solo (4 hours/day)

```
Manual tasks (2 hours):
- Email personalization
- Discovery calls
- Report quality review
- Client communication

Automated tasks (0 manual time):
- Lead generation
- Data cleaning
- Metrics reporting
- Basic research gathering
```

### Month 3+: With VA Support (2 hours/day for you)

Delegate to VA:
- Lead list review and scoring
- Email personalization
- Report formatting
- Client Slack channel responses
- Tracking file updates

You focus on:
- Discovery calls and closing
- Strategy and pricing decisions
- Client relationships
- Business development

### Month 4+: Full Scale (1 hour/day oversight)

```
VA 1 (Research): Runs scripts, reviews output, formats reports
VA 2 (Outreach): Manages lemlist, qualifies replies, books calls
You: Discovery calls, closing, client strategy
```

---

## 6. Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'requests'`
```bash
pip install -r scripts/requirements.txt
```

**Issue:** `APOLLO_API_KEY not set` warning
- Check your `.env` file exists and has the correct key
- Run: `cat .env` to verify (don't share the output publicly)

**Issue:** Email sending fails with `SMTPAuthenticationError`
- Gmail: Make sure you're using an App Password, not your regular password
- Check that 2-Step Verification is enabled on your Google account

**Issue:** No leads in client_tracker.csv after running lead_generation.py
- Check Apollo.io API key is valid
- Try running with `--count 5` first to test
- If no API key, mock data will be generated automatically

**Issue:** Perplexity API returns errors
- Verify API key is correct
- Check account has credits
- The script will fall back to OpenAI automatically

---

## 7. Environment Variables Reference

| Variable | Description | Where to Get |
|----------|-------------|-------------|
| `PERPLEXITY_API_KEY` | Perplexity AI API key | perplexity.ai/settings/api |
| `OPENAI_API_KEY` | OpenAI API key | platform.openai.com/api-keys |
| `APOLLO_API_KEY` | Apollo.io API key | app.apollo.io/settings/integrations/api |
| `HUNTER_API_KEY` | Hunter.io API key | hunter.io/api-keys |
| `SMTP_HOST` | Email SMTP server | Your email provider docs |
| `SMTP_PORT` | SMTP port (usually 587) | Your email provider docs |
| `SMTP_USER` | Your email address | Your email account |
| `SMTP_PASSWORD` | SMTP/App password | Google: App Passwords |
| `FROM_NAME` | Sender display name | Set to your name |
| `FROM_EMAIL` | Sender email address | Same as SMTP_USER |
| `EMAIL_DELAY` | Seconds between emails | 60 recommended |

---

*For tool account setup instructions, see `resources/tools_setup.md`*
