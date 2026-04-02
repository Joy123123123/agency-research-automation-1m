# ⚡ Quick Start Guide — Agency Research Automation

**Owner:** Md Jamil Islam | **Version:** 1.0.0

---

## ১. সেটআপ (Setup)

```bash
git clone https://github.com/Joy123123123/agency-research-automation-1m.git
cd agency-research-automation-1m
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config/api_keys.env.example config/api_keys.env
```

## ২. API কী সেটআপ করুন (Configure API Keys)

`config/api_keys.env` ফাইল খুলুন এবং আপনার কীগুলি দিন:

```env
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here
SENDGRID_API_KEY=your_sendgrid_key_here
AIRTABLE_API_KEY=your_airtable_key_here
NOTION_TOKEN=your_notion_token_here
```

## ৩. প্রথম রিসার্চ রান করুন (Run First Research)

```bash
# টার্গেট নিশ রিসার্চ করুন (US মার্কেট)
python scripts/run_research.py --niche "restaurant" --location "New York, NY" --count 50

# ইমেইল আউটরিচ পাঠান
python scripts/send_outreach.py --campaign "initial" --leads tracking/leads.csv

# রিপোর্ট তৈরি করুন
python scripts/generate_report.py --period weekly
```

## ৪. ড্যাশবোর্ড (Dashboard)

```bash
# লিড ট্র্যাকার দেখুন
python scripts/dashboard.py

# ক্যাম্পেইন স্ট্যাটাস চেক করুন
python scripts/check_campaigns.py
```

## ৫. স্বয়ংক্রিয় শিডিউল (Automated Schedule)

```bash
# প্রতিদিন সকাল ৯টায় রিসার্চ চালু রাখুন
python scripts/scheduler.py --start
```

---

## 📱 Free Mode — Android Phone (Termux) — No API Keys Needed!

শুধু **Telegram Bot Token** লাগবে — বাকি সব free!

> Full guide: **[TERMUX_SETUP.md](TERMUX_SETUP.md)**

### Quick steps (Termux):

```bash
# 1. Termux setup
pkg update -y && pkg install -y python git
pip install -r requirements-minimal.txt

# 2. Telegram credentials দিন (config/api_keys.env):
#    TELEGRAM_BOT_TOKEN=your_token
#    TELEGRAM_CHAT_ID=your_chat_id

# 3. একবার test run করুন
python scripts/free_mode.py --niche dentist --location "New York, NY" --count 10 --skip-scrape

# 4. Daily automation চালু করুন (সকাল ৯টায়)
python scripts/free_mode.py --loop --time 09:00
```

**What Free Mode does:**
- 🔍 Runs US lead research (YellowPages, no API key)
- 📊 Generates daily summary + manual outreach guide (Bangla + English)
- 📬 Sends results + CSV to your Telegram automatically
- ⏰ Runs daily on schedule (phone stays as server)

**Outputs:**
| File | বিবরণ |
|------|-------|
| `tracking/leads.csv` | All leads with scores |
| `logs/free_mode.log` | Pipeline log |

---

## সাহায্য প্রয়োজন? (Need Help?)

- 📖 [পূর্ণ ডকুমেন্টেশন](docs/API.md)
- 🐛 [ইস্যু রিপোর্ট করুন](https://github.com/Joy123123123/agency-research-automation-1m/issues)
- 💬 [GitHub Discussion](https://github.com/Joy123123123/agency-research-automation-1m/discussions)
