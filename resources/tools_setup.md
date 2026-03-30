# 🛠️ Tools Setup Guide

**Creator:** Md Jamil Islam  
**Purpose:** Step-by-step setup for all tools needed

---

## 1. Python Setup

### Install Python
1. Go to [python.org/downloads](https://python.org/downloads)
2. Download Python 3.11+
3. Run installer (check "Add to PATH")
4. Verify: open terminal, type `python --version`

### Install Dependencies
```bash
cd scripts/
pip install -r requirements.txt
```

---

## 2. Google Sheets Setup

### Create Your Tracking Sheets
1. Go to [sheets.google.com](https://sheets.google.com)
2. Create new sheet: "Client Tracker"
3. Columns: Company | Email | Status | Date | Revenue | Notes
4. Create sheet: "Revenue Tracker"
5. Columns: Month | Clients | Revenue | Target | Notes

### Import CSV Data
1. File → Import → Upload
2. Select `tracking/client_tracker.csv`
3. Replace current sheet

---

## 3. Perplexity AI Setup

1. Go to [perplexity.ai](https://perplexity.ai)
2. Create free account
3. Use for research queries like:
   - "Top 10 digital marketing agencies in New York 2024"
   - "Latest trends in content marketing 2024"
   - "Competitor analysis for [niche] agencies"

---

## 4. Apollo.io Setup (Lead Generation)

1. Go to [apollo.io](https://apollo.io)
2. Create free account (50 leads/month free)
3. Search filters to use:
   - Job title: "CEO" OR "Founder" OR "Owner"
   - Industry: "Marketing and Advertising"
   - Company size: 1-50 employees
   - Location: United States / United Kingdom

---

## 5. Hunter.io Setup (Email Finder)

1. Go to [hunter.io](https://hunter.io)
2. Create free account (25 searches/month free)
3. Use to find emails for agencies where you only have the domain

---

## 6. Zapier Setup (Automation)

1. Go to [zapier.com](https://zapier.com)
2. Create free account
3. Useful automations:
   - New email reply → Update Google Sheet status
   - New form submission → Add to client tracker
   - Calendar event → Send follow-up reminder

---

## 7. Calendly Setup (Scheduling)

1. Go to [calendly.com](https://calendly.com)
2. Create free account
3. Set availability: Mon-Fri, 9am-5pm your timezone
4. Create event: "15-Minute Discovery Call"
5. Share link in email signatures

---

## Quick Reference

| Tool | Use | Cost |
|------|-----|------|
| Python | Automation scripts | Free |
| Google Sheets | Tracking | Free |
| Perplexity AI | Research | Free |
| Apollo.io | Lead generation | Free (50/mo) |
| Hunter.io | Email finding | Free (25/mo) |
| Zapier | Workflow automation | Free (5 zaps) |
| Calendly | Call scheduling | Free |

---

*For automation help, see `resources/automation_guide.md`*
