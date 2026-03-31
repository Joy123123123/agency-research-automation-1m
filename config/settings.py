"""
Agency Research Automation — Main Settings
Owner: Md Jamil Islam
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / "config" / "api_keys.env")


# ========================
# AI Configuration
# ========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")


# ========================
# Email Configuration
# ========================
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "agency@example.com")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Md Jamil Islam")
EMAIL_DAILY_LIMIT = int(os.getenv("EMAIL_DAILY_LIMIT", "200"))


# ========================
# CRM Configuration
# ========================
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE_LEADS = os.getenv("AIRTABLE_TABLE_LEADS", "Leads")
AIRTABLE_TABLE_CAMPAIGNS = os.getenv("AIRTABLE_TABLE_CAMPAIGNS", "Campaigns")

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")


# ========================
# Scraping Configuration
# ========================
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "")
RESEARCH_DELAY_SECONDS = float(os.getenv("RESEARCH_DELAY_SECONDS", "2"))
MAX_LEADS_PER_DAY = int(os.getenv("MAX_LEADS_PER_DAY", "500"))

# User agents for scraping rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]


# ========================
# App Settings
# ========================
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATA_DIR = BASE_DIR / "data"
TRACKING_DIR = BASE_DIR / "tracking"
TEMPLATES_DIR = BASE_DIR / "templates"
REPORTS_DIR = BASE_DIR / "data" / "reports"


# ========================
# Target Niches
# ========================
DEFAULT_NICHES = [
    "restaurant",
    "dentist",
    "lawyer",
    "real estate",
    "gym",
    "salon",
    "plumber",
    "electrician",
    "hotel",
    "pharmacy",
]

DEFAULT_LOCATIONS = [
    "New York, NY",
    "Los Angeles, CA",
    "Chicago, IL",
    "Houston, TX",
    "Miami, FL",
]


# ========================
# Revenue Targets
# ========================
MONTHLY_REVENUE_TARGETS = {
    1: 10000,
    2: 15000,
    3: 20000,
    4: 30000,
    5: 40000,
    6: 50000,
    7: 60000,
    8: 70000,
    9: 80000,
    10: 90000,
    11: 95000,
    12: 100000,
}
ANNUAL_REVENUE_TARGET = 1_000_000
