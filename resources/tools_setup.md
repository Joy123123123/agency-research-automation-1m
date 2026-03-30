# 🛠️ Tools Setup Guide — Agency Research Automation

**Owner:** Md Jamil Islam  
**Time to complete:** 1–2 hours  
**Cost:** $0–$50/month (mostly free tiers to start)

---

## 1. Python Environment Setup

### Install Python
1. Download Python 3.9+ from [python.org](https://python.org)
2. Verify installation: `python --version`

### Set Up Project Dependencies
```bash
# Navigate to the scripts folder
cd scripts/

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import requests, pandas, bs4; print('All dependencies installed!')"
```

### Configure Environment Variables
1. Create a `.env` file in the root directory (it's in `.gitignore` — never commit it!)
2. Add your credentials:

```bash
# .env file — DO NOT commit to GitHub
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_NAME=Md Jamil Islam
FROM_EMAIL=your-email@gmail.com

# API Keys (add as you subscribe)
APOLLO_API_KEY=your-apollo-key
HUNTER_API_KEY=your-hunter-key
CLEARBIT_API_KEY=your-clearbit-key
```

---

## 2. Email Setup (Gmail)

### Create a Professional Email
- Use Gmail with a custom domain (e.g., `jamil@youragency.com`)
- Or use a free Gmail: `mdjaamilislam.research@gmail.com`

### Set Up Gmail App Password (for SMTP)
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Go to "App Passwords" → Generate password for "Mail"
4. Copy the 16-character password into your `.env` as `SMTP_PASSWORD`

### Email Warm-Up (Important!)
Before sending campaigns, warm up your email:
- Day 1–3: Send 5 emails/day manually
- Day 4–7: Send 10 emails/day
- Day 8–14: Send 20 emails/day
- Day 15+: Full campaign (30–50/day)

---

## 3. Lead Generation Tools

### Apollo.io (Free — 50 leads/month)
1. Sign up at [apollo.io](https://app.apollo.io)
2. Use for: Company search, contact finding, email verification
3. Free plan: 50 email credits/month
4. Paid plan ($39/mo): 1,000 email credits/month
5. Get API key: Settings → API Keys → Create new key

### Hunter.io (Free — 25 searches/month)
1. Sign up at [hunter.io](https://hunter.io)
2. Use for: Email finding by domain, email verification
3. Free plan: 25 searches + 50 verifications/month
4. Get API key: Settings → API → Copy key

### LinkedIn (Free)
1. Optimize your profile fully before outreach
2. Use free LinkedIn search for prospecting
3. Send 20 connection requests/day (stay within limits)
4. Consider LinkedIn Premium ($39/mo) for InMail

### Snov.io (Alternative — 50 credits free)
1. Sign up at [snov.io](https://snov.io)
2. Use for: Email finding, verification, drip campaigns

---

## 4. Research Tools

### SimilarWeb (Free tier)
1. Go to [similarweb.com](https://www.similarweb.com)
2. Use for: Website traffic data for competitor analysis
3. Free: 5 results per metric, 3-month data

### SEMrush (Free 7-day trial)
1. Sign up at [semrush.com](https://www.semrush.com)
2. Use for: SEO data, competitor keywords, backlinks
3. Start free trial for deeper research projects

### BuiltWith (Free)
1. Go to [builtwith.com](https://builtwith.com)
2. Install Chrome extension
3. Use for: Company technology stack detection

### Crunchbase (Free tier)
1. Sign up at [crunchbase.com](https://www.crunchbase.com)
2. Use for: Company funding, founding date, key personnel

### Google Search (Free — always)
```
# Powerful Google searches for research:
site:linkedin.com/company "[company name]"
"[company name]" competitor
"[company name]" pricing
"[company name]" review
"[company name]" "head of" OR "director of" OR "VP"
```

---

## 5. Outreach & CRM Tools

### Gmail (Free)
- Use labels to organize outreach (Prospects, Followed Up, Proposals, Clients)
- Use canned responses for email templates
- Enable read receipts (or use Mailtrack)

### Mailtrack (Free)
1. Install Chrome extension from [mailtrack.io](https://mailtrack.io)
2. Use for: Email open tracking in Gmail
3. Free: Unlimited tracking, small footer added

### Notion (Free)
1. Sign up at [notion.so](https://notion.so)
2. Use as your CRM and project management hub
3. Better alternative to tracking/ CSVs as you scale

### Calendly (Free)
1. Sign up at [calendly.com](https://calendly.com)
2. Use for: Discovery call booking (link in emails)
3. Free: 1 event type, unlimited bookings

---

## 6. Report Delivery Tools

### Google Docs (Free)
- Write and deliver research reports
- Share via link — professional and easy

### Canva (Free)
- Design professional report covers
- Create simple pitch decks
- [canva.com](https://www.canva.com)

### Notion (Free)
- Share research reports as Notion pages
- More interactive than PDFs

---

## 7. Payment Tools

### Stripe (Free to set up — 2.9% + $0.30/transaction)
1. Sign up at [stripe.com](https://stripe.com)
2. Use for: Invoicing and online payments
3. Send payment links via email

### PayPal (Free to set up)
1. Set up business account at [paypal.com](https://paypal.com)
2. Use for: International clients or clients who prefer PayPal

### Wave (Free invoicing)
1. Sign up at [waveapps.com](https://www.waveapps.com)
2. Free invoicing with professional templates
3. Tracks payments and sends reminders

---

## 8. Productivity Stack (Optional but Recommended)

| Tool | Purpose | Cost |
|------|---------|------|
| Notion | CRM + project mgmt | Free |
| Loom | Screen recording for demos | Free |
| Grammarly | Email proofreading | Free |
| LastPass | Password manager | Free |
| VS Code | Code editing | Free |
| Zoom | Discovery calls | Free (40-min limit) |
| Google Meet | Discovery calls | Free |

---

## 🚀 Minimum Viable Setup (Start Today)

To start making money THIS WEEK, you only need:
1. ✅ Gmail (you already have this)
2. ✅ Python + scripts (30 min setup)
3. ✅ Apollo.io free account (5 min)
4. ✅ Mailtrack (5 min)
5. ✅ Calendly (5 min)
6. ✅ Wave for invoicing (5 min)

**Total cost: $0. Total time: ~1 hour.**

---

*Set up tools once, use them forever. Don't over-tool — start simple and add as needed.*
