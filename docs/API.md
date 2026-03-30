# API Documentation — Agency Research Automation

## Overview

এই API ডকুমেন্টেশন agency-research-automation-1m প্রজেক্টের সকল মডিউলের ব্যবহার বর্ণনা করে।

---

## Research Module (`src/research/`)

### AgencyFinder

```python
from src.research.agency_finder import AgencyFinder

finder = AgencyFinder(api_key="YOUR_GOOGLE_KEY", delay=2.0)

# Google Maps থেকে ব্যবসা খুঁজুন
agencies = finder.find_by_google_maps(
    niche="restaurant",
    location="Dhaka",
    max_results=50
)

# কোয়ালিটি ফিল্টার করুন
quality_leads = finder.filter_by_criteria(
    agencies,
    min_rating=3.5,
    max_reviews=100,
    needs_website=True  # True = শুধু website-বিহীন ব্যবসা
)
```

### ContactScraper

```python
from src.research.contact_scraper import ContactScraper

scraper = ContactScraper(delay=1.5)

# একটি ওয়েবসাইট থেকে কন্টাক্ট স্ক্র্যাপ করুন
contact = scraper.scrape_website("https://example.com")
# Returns: {"emails": [...], "phones": [...], "facebook": "...", ...}

# একাধিক ওয়েবসাইট স্ক্র্যাপ
results = scraper.scrape_bulk(["https://site1.com", "https://site2.com"])
```

### MarketAnalyzer

```python
from src.research.market_analyzer import MarketAnalyzer

analyzer = MarketAnalyzer()

insight = analyzer.analyze_niche("restaurant", "Dhaka", agencies)
print(insight.opportunity_score)      # 0-100
print(insight.recommended_service)   # "website", "seo", etc.
print(insight.estimated_revenue)      # মাসিক আয়ের অনুমান

lead_score = analyzer.calculate_lead_score(agency)
```

---

## AI Module (`src/ai/`)

### ContentGenerator

```python
from src.ai.content_generator import ContentGenerator

gen = ContentGenerator(openai_key="...", gemini_key="...")

email = gen.generate_outreach_email(
    business_name="ABC Restaurant",
    niche="restaurant",
    location="Dhaka",
    sender_name="Md Jamil Islam"
)
# Returns: {"subject": "...", "body": "..."}

follow_up = gen.generate_follow_up(step=1, business_name="ABC", sender_name="Jamil")
```

### LeadScorer

```python
from src.ai.lead_scorer import LeadScorer

scorer = LeadScorer()

# একটি লিড স্কোর করুন
scored = scorer.score_lead({
    "name": "ABC Restaurant",
    "has_website": False,
    "email": "abc@abc.com",
    "google_rating": 3.8,
    "review_count": 25
})
print(scored.score)     # 0-100
print(scored.grade)     # A, B, C, D
print(scored.priority)  # high, medium, low, skip

# বাল্ক স্কোর ও সর্ট
scored_leads = scorer.score_bulk(leads_list)
high_priority = scorer.filter_high_priority(scored_leads)
```

---

## Automation Module (`src/automation/`)

### EmailSender

```python
from src.automation.email_sender import EmailSender

sender = EmailSender(
    api_key="SENDGRID_KEY",
    from_email="you@domain.com",
    from_name="Md Jamil Islam"
)

result = sender.send_single(
    to_email="lead@business.com",
    to_name="Business Name",
    subject="Your subject",
    html_content="<p>Email body</p>"
)
# result.status: "sent" | "failed" | "bounced"

results = sender.send_bulk(leads_list, subject_template, html_template, daily_limit=200)
```

### FollowUpManager

```python
from src.automation.follow_up import FollowUpManager

fm = FollowUpManager()

fm.enqueue_lead("email@business.com", "Business Name", lead_dict)

due = fm.get_due_emails()  # আজকের follow-up list

fm.mark_sent("email@business.com")
fm.mark_replied("email@business.com")
fm.unsubscribe("email@business.com")
```

---

## Reporting Module (`src/reporting/`)

### ReportGenerator

```python
from src.reporting.report_generator import ReportGenerator

gen = ReportGenerator()

summary = gen.generate_weekly_summary()
html_file = gen.generate_html_report(summary)
csv_file = gen.export_to_csv(leads_list)
```
