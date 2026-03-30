# 🛠️ Tools Setup Guide

**Author:** Md Jamil Islam
**Purpose:** Configure all tools needed to run Agency Research Automation

---

## 1. Python Environment Setup

### Install Python
```bash
# Check if Python is installed
python --version   # Should be 3.9+

# If not installed, download from python.org
```

### Install Dependencies
```bash
# Navigate to the scripts directory
cd scripts/

# Install required packages
pip install -r requirements.txt
```

---

## 2. Google Sheets Setup

### Create Your Workspace
1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet named "Agency Research Automation"
3. Create these sheets (tabs):
   - `Client Tracker`
   - `Metrics Dashboard`
   - `Revenue Tracker`

### Import CSV Files
1. Open each sheet tab
2. File → Import → Upload
3. Upload the corresponding CSV from the `tracking/` folder
4. Select "Replace current sheet"

### Auto-update Formula (Optional)
```
=IMPORTDATA("URL_TO_YOUR_CSV")
```

---

## 3. Email Configuration

### Gmail Setup (Recommended for outreach)
1. Go to Gmail → Settings → See all settings
2. Enable "Less secure app access" OR set up App Password
3. Go to `scripts/email_outreach.py`
4. Update SMTP config:
```python
smtp_config = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 465,
    "username": "your.email@gmail.com",
    "password": "your_app_password",
}
```

### Create `.env` File for Security
```bash
# Create .env file (never commit this to GitHub!)
touch .env
```

Add to `.env`:
```
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
```

---

## 4. AI Research Tools

### Perplexity AI (Free)
1. Sign up at [perplexity.ai](https://perplexity.ai)
2. Use Pro Search for in-depth competitor research
3. Key prompts:
   - "Who are the top 5 competitors of [Agency Name]?"
   - "What are the latest trends in [niche] marketing in [year]?"

### ChatGPT (Free or Plus)
1. Sign up at [chat.openai.com](https://chat.openai.com)
2. Use for report drafting and email personalization
3. Key prompts for reports:
   - "Summarize this competitor analysis in 3 bullet points: [data]"
   - "Write an executive summary for this research: [data]"

### OpenAI API (For Automation)
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Get API key from API Keys section
3. Add to `.env`:
```
OPENAI_API_KEY=your_api_key_here
```

---

## 5. Lead Generation

### LinkedIn (Free)
1. Search: "marketing agency owner" + location
2. Filter by: 2nd connections, specific industries
3. Save 50 profiles per day as leads

### Clutch.co (Free)
1. Go to [clutch.co](https://clutch.co)
2. Filter by: Service type, location, company size
3. Extract agency names, websites, emails

### Hunter.io (Free tier)
1. Sign up at [hunter.io](https://hunter.io)
2. Find email addresses for agency contacts
3. Free: 25 searches/month

---

## 6. Scheduling & CRM

### Calendly (Free)
1. Sign up at [calendly.com](https://calendly.com)
2. Create a 30-minute "Discovery Call" event type
3. Connect your Google Calendar
4. Use your Calendly link in all outreach emails

### Google Calendar
- Block 9–11 AM for outreach tasks
- Block 11 AM–1 PM for research delivery
- Block 2–4 PM for discovery calls
- Block 4–5 PM for admin/tracking

---

## 7. Payment Setup

### Stripe (Recommended)
1. Sign up at [stripe.com](https://stripe.com)
2. Complete identity verification
3. Create payment links for each pricing tier
4. Add payment links to proposals

### PayPal Business
1. Sign up at [paypal.com/business](https://paypal.com/business)
2. Set up invoice templates
3. Use for international clients

### Wise (For International)
1. Sign up at [wise.com](https://wise.com)
2. Multi-currency support
3. Lower fees for international transfers

---

## 8. Environment Variables Reference

Create a `.env` file in the root directory:
```
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
OPENAI_API_KEY=your_openai_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
STRIPE_API_KEY=your_stripe_key
```

> ⚠️ **IMPORTANT:** Never commit `.env` to GitHub. It's already in `.gitignore`.

---

*Created by Md Jamil Islam | Agency Research Automation*
