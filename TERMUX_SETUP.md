# 📱 Termux Setup Guide — Agency Research Automation (Free Mode)

**Platform:** Android phone with Termux  
**Goal:** Run fully automated lead research + Telegram notifications — no paid APIs needed.  
**Owner:** Md Jamil Islam

---

## পূর্বশর্ত (Prerequisites)

- Android 7+ phone
- Internet connection (Wi-Fi or mobile data)
- Telegram account (for notifications)

---

## ধাপ ১ — Termux ইনস্টল করুন (Install Termux)

> ⚠️ **Google Play Store-এর Termux outdated। F-Droid থেকে install করুন।**

1. F-Droid app install করুন: https://f-droid.org  
2. F-Droid খুলুন → "Termux" search করুন → Install করুন।

---

## ধাপ ২ — Termux basic setup (Base packages)

Termux খুলুন এবং নিচের commands একটা একটা করে run করুন:

```bash
# Package list update
pkg update -y && pkg upgrade -y

# Required packages
pkg install -y python git openssl libffi

# Python pip upgrade
pip install --upgrade pip
```

---

## ধাপ ৩ — Repository clone করুন

```bash
# Home directory-তে যান
cd ~

# Repository clone করুন
git clone https://github.com/Joy123123123/agency-research-automation-1m.git

# Folder-এ ঢুকুন
cd agency-research-automation-1m
```

---

## ধাপ ৪ — Python dependencies install করুন

```bash
# Minimal requirements install (recommended for phone)
pip install -r requirements-minimal.txt
```

requirements-minimal.txt এ আছে: `flask`, `requests`, `schedule` — এটুকুই Free Mode-এর জন্য যথেষ্ট।

যদি full dependencies লাগে:
```bash
pip install -r requirements.txt
```

---

## ধাপ ৫ — Telegram Bot তৈরি করুন

### ৫.১ — @BotFather দিয়ে bot তৈরি

1. Telegram খুলুন → Search করুন `@BotFather`
2. `/start` পাঠান
3. `/newbot` পাঠান
4. Bot-এর **name** দিন (যেমন: `My Agency Bot`)
5. Bot-এর **username** দিন (যেমন: `myagency_notify_bot`) — username-এ `bot` দিয়ে শেষ করতে হবে
6. BotFather আপনাকে একটা **token** দেবে:
   ```
   Use this token to access the HTTP API:
   1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ-abcdefgh
   ```
   এই পুরো token string টি সেভ করুন (`:` সহ) — এটাই `TELEGRAM_BOT_TOKEN`।

### ৫.২ — Chat ID বের করুন

**Method 1 (সহজ):**
1. আপনার নতুন bot-কে Telegram-এ খুজে `/start` পাঠান।
2. Browser-এ এই URL খুলুন (token replace করুন):
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. JSON response-এ `"chat":{"id":XXXXXXXXX}` দেখবেন — এই number-টাই আপনার `TELEGRAM_CHAT_ID`।

**Method 2 (Group-এর জন্য):**
1. একটা Telegram group তৈরি করুন।
2. Bot কে group-এ add করুন।
3. Group-এ যেকোনো message পাঠান।
4. উপরের URL-এ গেলে group-এর chat id দেখাবে (সাধারণত negative number, যেমন: `-1001234567890`)।

---

## ধাপ ৬ — API keys config করুন

```bash
# Example file থেকে copy করুন
cp config/api_keys.env.example config/api_keys.env

# Nano editor দিয়ে edit করুন
nano config/api_keys.env
```

নিচের lines খুঁজে বের করুন এবং আপনার values দিন (পুরো token string দিন, quotes ছাড়া):

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ-abcdefgh
TELEGRAM_CHAT_ID=123456789
```

`Ctrl+O` → Enter (save), তারপর `Ctrl+X` (exit)।

---

## ধাপ ৭ — Test run করুন (একবার)

```bash
cd ~/agency-research-automation-1m

python scripts/free_mode.py --niche dentist --location "New York, NY" --count 10 --skip-scrape
```

সফল হলে আউটপুট দেখাবে:
```
🚀 Free Mode Pipeline Starting — 2026-04-02 09:00
   Niche: dentist | Location: New York, NY | Count: 10
   Telegram: ✅ configured

📡 Step 1/3: Running lead research...
   ✅ Leads saved to: tracking/leads.csv
📊 Step 2/3: Generating report...
📬 Step 3/3: Sending Telegram notification...
   ✅ Telegram message sent
   ✅ Leads CSV sent to Telegram

==================================================
✅ Pipeline complete!
   Total leads: 10
   Grade A: 3 | Grade B: 5
   Leads file: tracking/leads.csv
   Logs: logs/free_mode.log
==================================================
```

আপনার Telegram-এও message আসবে।

---

## ধাপ ৮ — Daily automation চালু করুন

### Option A: Simple loop (সহজ, কিন্তু Termux background-এ kill হতে পারে)

```bash
python scripts/free_mode.py --loop --time 09:00
```

এটা প্রতিদিন সকাল ৯টায় automatically চলবে।

### Option B: Termux:Boot দিয়ে auto-start (Recommended)

Phone reboot হলেও automation চলবে:

1. F-Droid থেকে **Termux:Boot** install করুন।
2. Termux:Boot একবার open করুন (permission নেবে)।
3. Boot script তৈরি করুন:

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start_agency.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/agency-research-automation-1m
python scripts/free_mode.py --loop --time 09:00 >> logs/boot.log 2>&1 &
EOF
chmod +x ~/.termux/boot/start_agency.sh
```

এখন phone restart করলেও automation চালু থাকবে।

### Option C: Tasker (Advanced, battery efficient)

Tasker app install করুন → Profile → Time → প্রতিদিন 9:00 AM → Task → Run Shell:
```
bash -c "cd ~/agency-research-automation-1m && python scripts/free_mode.py --skip-scrape >> logs/tasker.log 2>&1"
```

---

## ধাপ ৯ — Output files কোথায় আছে

| File | বিবরণ |
|------|-------|
| `tracking/leads.csv` | সব leads (name, phone, website, grade, score) |
| `data/reports/summary_weekly.json` | Weekly report |
| `logs/free_mode.log` | Pipeline log (error check করুন) |
| `logs/research.log` | Research module log |

```bash
# Leads দেখুন (top 10)
head -11 tracking/leads.csv

# Log দেখুন (last 20 lines)
tail -20 logs/free_mode.log
```

---

## ধাপ ১০ — CLI flags (সব options)

```bash
python scripts/free_mode.py --help
```

| Flag | Default | বিবরণ |
|------|---------|-------|
| `--niche` | `dentist` | Business niche (dentist, lawyer, restaurant…) |
| `--location` | `New York, NY` | Search location |
| `--count` | `50` | Max leads per run |
| `--skip-scrape` | off | Website scraping skip করুন (phone-friendly) |
| `--loop` | off | Daily scheduler চালু করুন |
| `--time` | `09:00` | Daily run time (HH:MM) |

---

## সমস্যা সমাধান (Troubleshooting)

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests schedule
```

### "TELEGRAM_BOT_TOKEN not set"
```bash
nano config/api_keys.env
# TELEGRAM_BOT_TOKEN= এর পরে token দিন
```

### Termux background-এ kill হয়ে যাচ্ছে
- Phone Settings → Battery → Termux → "Don't optimize" বা "No restrictions" set করুন।
- Termux:Boot use করুন (Option B)।

### "No leads found"
```bash
# Internet connection check করুন
curl -I https://www.yellowpages.com

# Verbose run করুন
python scripts/run_research.py --niche dentist --location "New York, NY" --count 5
```

---

## Telegram Bot API — শুধু HTTPS, কোনো paid service নেই

এই system শুধু Telegram Bot API ব্যবহার করে:
- `https://api.telegram.org/bot{TOKEN}/sendMessage`
- `https://api.telegram.org/bot{TOKEN}/sendDocument`

কোনো paid service, subscription বা extra API key লাগবে না।

---

## Quick Reference Commands

```bash
# একবার run (test)
python scripts/free_mode.py --skip-scrape

# Daily loop
python scripts/free_mode.py --loop --time 09:00

# Custom niche/location
python scripts/free_mode.py --niche lawyer --location "Los Angeles, CA" --count 30

# Leads দেখুন
cat tracking/leads.csv

# Log দেখুন
tail -f logs/free_mode.log
```

---

*Termux setup guide — Agency Research Automation Free Mode*  
*Owner: Md Jamil Islam*
