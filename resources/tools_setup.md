# 🛠️ Tools Setup Guide

Complete setup instructions for all tools used in the Agency Research Automation system.

---

## 1. Python Environment

### Install Python 3.10+
Download from [python.org](https://www.python.org/downloads/)

Verify installation:
```bash
python --version
# Should output: Python 3.10.x or higher
```

### Install Dependencies
```bash
cd scripts/
pip install -r requirements.txt
```

### Create `.env` File
Create a file called `.env` in the project root:
```bash
# Copy the template
cp .env.example .env
# Edit with your actual values
nano .env  # or open in any text editor
```

**`.env` Template:**
```env
# Research APIs
PERPLEXITY_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Lead Generation
APOLLO_API_KEY=your_key_here
HUNTER_API_KEY=your_key_here

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
FROM_NAME=Your Name
FROM_EMAIL=your_email@gmail.com

# Settings
EMAIL_DELAY=60
```

> **Security:** Never commit `.env` to git. It's already in `.gitignore`.

---

## 2. Research APIs

### Perplexity AI (Recommended — Real-time data)

**Setup:**
1. Go to [perplexity.ai](https://www.perplexity.ai)
2. Click "API" in the sidebar
3. Create an account (free tier available)
4. Generate an API key
5. Add to `.env`: `PERPLEXITY_API_KEY=pplx-xxxxx`

**Cost:** $5 for ~500 searches (more than enough to start)

**Used by:** `scripts/research_automation.py`

---

### OpenAI (Fallback research)

**Setup:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account → API keys → Create new key
3. Add to `.env`: `OPENAI_API_KEY=sk-xxxxx`
4. Add billing ($5 minimum to start)

**Cost:** ~$0.002 per request (GPT-4o-mini)

**Used by:** `scripts/research_automation.py` (fallback)

---

## 3. Lead Generation Tools

### Apollo.io (Primary lead source)

**Free Tier:** 50 email exports/month

**Setup:**
1. Go to [apollo.io](https://www.apollo.io)
2. Create free account
3. Go to Settings → API → Create API Key
4. Add to `.env`: `APOLLO_API_KEY=your_key`

**Upgrade:** $49/month for 1,000 exports (recommended for scale)

**Manual Use (no API):**
1. Login to Apollo.io
2. Filter: Job Title = "CEO, Owner, Founder" + Industry = "Marketing Agency" + Location = "United States"
3. Export to CSV
4. Import to `tracking/client_tracker.csv`

---

### Hunter.io (Email verification)

**Free Tier:** 25 requests/month

**Setup:**
1. Go to [hunter.io](https://hunter.io)
2. Create free account
3. Go to API → Copy your API key
4. Add to `.env`: `HUNTER_API_KEY=your_key`

**Upgrade:** $49/month for 500 requests

---

### LinkedIn Sales Navigator (Manual use)
- No API available on free plan
- Use manually: Search "Marketing Agency Owner" filtered by location
- Free account works — but limited
- Premium Navigator: $79/month (recommended at Month 2+)

---

## 4. Email Setup

### Gmail SMTP (Recommended for starting)

**Setup:**
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Go to Security → App passwords
4. Create app password for "Mail" → "Windows Computer"
5. Copy the 16-character password
6. Add to `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=youremail@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop  (your app password)
   ```

> **Note:** Gmail has a sending limit of 500 emails/day. For higher volume, use a dedicated email tool.

---

### lemlist (Recommended for scale — 30+ emails/day)

**Why use lemlist:** Built-in sending limits, warm-up, tracking, and sequence automation.

**Setup:**
1. Go to [lemlist.com](https://www.lemlist.com)
2. Create account (free trial, then $59/month)
3. Connect your Gmail/Outlook
4. Import leads from `tracking/client_tracker.csv`
5. Create sequences using `templates/email_templates.md`

**Key Features:**
- Auto follow-up sequences
- Email open/click tracking
- Reply detection (auto-pauses sequence)
- Team collaboration

---

### Instantly.ai (Alternative, cheaper)

- $37/month for unlimited emails
- Better for high-volume cold outreach
- [instantly.ai](https://instantly.ai)

---

## 5. CRM & Tracking

### HubSpot Free CRM

**Setup:**
1. Go to [hubspot.com/crm](https://www.hubspot.com/crm)
2. Create free account
3. Import `tracking/client_tracker.csv`
4. Setup pipeline stages matching CSV status field

**Pipeline Stages:**
- New Lead
- Email Sent
- Replied
- Discovery Call Scheduled
- Proposal Sent
- Negotiating
- Closed Won
- Closed Lost

---

### Google Sheets (Simple alternative)

Upload all CSV files to Google Drive:
1. Go to [drive.google.com](https://drive.google.com)
2. New → File Upload → select all CSV files from `tracking/`
3. Open each file → File → Save as Google Sheets
4. Share with collaborators

**Benefit:** Easy to view on mobile, auto-save, collaboration

---

## 6. Automation

### Make.com (Zapier alternative — cheaper)

**Free Tier:** 1,000 operations/month

**Setup:**
1. Go to [make.com](https://www.make.com)
2. Create free account
3. Start with these automations:

**Automation 1: New lead → Add to Google Sheets**
- Trigger: New CSV row added
- Action: Add to Google Sheets row

**Automation 2: Email reply → Update lead status**
- Trigger: Gmail new reply (filtered by label)
- Action: Update status in Google Sheets to "replied"

**Automation 3: New client → Trigger onboarding**
- Trigger: Revenue tracker updated with "active" status
- Action: Send welcome email (template from `email_templates.md`)

---

### GitHub Actions (Free automation)

Automate Python scripts on a schedule:

Create `.github/workflows/daily_research.yml`:
```yaml
name: Daily Lead Generation
on:
  schedule:
    - cron: '0 9 * * 1-5'  # 9 AM weekdays
jobs:
  generate-leads:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/lead_generation.py --count 20
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
```

Add secrets in: GitHub repo → Settings → Secrets → Actions

---

## 7. Calendar & Scheduling

### Calendly (Free)

**Setup:**
1. Go to [calendly.com](https://calendly.com)
2. Create free account
3. Create event: "15-Minute Discovery Call"
4. Set availability: Monday-Friday, 9 AM - 5 PM (your timezone)
5. Copy link and use in all outreach emails

**Why:** Eliminates back-and-forth scheduling

---

## 8. Payment Processing

### Stripe

**Setup:**
1. Go to [stripe.com](https://www.stripe.com)
2. Create account (no monthly fee, 2.9% + $0.30 per transaction)
3. Create a payment link or subscription product
4. Use in proposals and onboarding emails

**Monthly Subscription Setup:**
1. Stripe Dashboard → Products → Add Product
2. Name: "Growth Plan" | Price: $1,250/month | Recurring
3. Create payment link
4. Share with clients in proposal email

---

## 9. Quick Setup Checklist

### Day 1 (Must Have)
- [ ] Python installed and dependencies installed
- [ ] `.env` file created
- [ ] Apollo.io account created (free)
- [ ] Hunter.io account created (free)
- [ ] Gmail app password configured
- [ ] Calendly link created

### Week 1 (Recommended)
- [ ] Perplexity AI account + API key
- [ ] HubSpot CRM setup
- [ ] lemlist or Instantly.ai account
- [ ] Stripe account for payments

### Month 1 (As You Grow)
- [ ] Make.com automations
- [ ] GitHub Actions for daily scripts
- [ ] LinkedIn Sales Navigator
- [ ] Apollo.io paid plan (if volume justifies)

---

*For automation workflow details, see `resources/automation_guide.md`*
