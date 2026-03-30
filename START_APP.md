# 📱 Mobile Web App — চালু করার গাইড
**Owner:** Md Jamil Islam

এই guide পড়লে তুমি নিজেই mobile-এ app চালু করতে পারবে।

---

## 🟢 Option 1: Replit (সবচেয়ে সহজ — মোবাইল থেকেই করা যাবে)

### ধাপ ১: Replit-এ project খোলো
1. **replit.com** এ যাও
2. GitHub repo import করো:
   - `+ Create Repl` → `Import from GitHub`
   - URL দাও: `https://github.com/Joy123123123/agency-research-automation-1m`
3. Language: **Python** বেছে নাও

### ধাপ ২: Flask install করো
Replit Shell-এ লেখো:
```bash
pip install flask
```

### ধাপ ৩: App চালু করো
```bash
python scripts/web_app.py
```

### ধাপ ৪: মোবাইলে খোলো
- Replit উপরে একটা **URL দেখাবে** (যেমন: `https://your-project.username.repl.co`)
- সেই URL মোবাইল browser-এ paste করো
- **Done! 🎉**

---

## 🔵 Option 2: Termux (Android — সরাসরি মোবাইলে)

### ধাপ ১: Termux install করো
- F-Droid থেকে Termux download করো (Play Store version পুরনো)
- URL: https://f-droid.org/packages/com.termux/

### ধাপ ২: Setup করো
```bash
pkg update && pkg upgrade
pkg install python git
pip install flask
```

### ধাপ ৩: Repo clone করো
```bash
git clone https://github.com/Joy123123123/agency-research-automation-1m.git
cd agency-research-automation-1m
pip install flask
```

### ধাপ ৪: App চালু করো
```bash
python scripts/web_app.py
```

### ধাপ ৫: Browser-এ খোলো
- Mobile browser-এ যাও
- URL: `http://localhost:5000`
- **Done! 🎉**

---

## 💻 Option 3: PC/Laptop

```bash
# Clone করো
git clone https://github.com/Joy123123123/agency-research-automation-1m.git
cd agency-research-automation-1m

# Virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install
pip install flask

# Run
python scripts/web_app.py
```

Browser-এ যাও: `http://localhost:5000`

মোবাইলে একই WiFi-এ থাকলে:
- PC-এর IP বের করো: `ipconfig` (Windows) বা `ifconfig` (Linux/Mac)
- মোবাইলে: `http://192.168.1.X:5000`

---

## 🌐 Internet-এ সবসময় চালু রাখতে (Free Hosting)

### Railway.app (সম্পূর্ণ বিনামূল্যে)
1. **railway.app** এ GitHub দিয়ে login করো
2. `New Project` → `Deploy from GitHub repo`
3. Repo বেছে নাও
4. Environment Variable যোগ করো:
   ```
   PORT=5000
   ```
5. Start Command: `python scripts/web_app.py`
6. Deploy হলে URL পাবে → মোবাইলে সেই URL দিয়ে access করো

### Render.com (বিকল্প)
1. **render.com** → `New Web Service`
2. GitHub repo connect করো
3. Build Command: `pip install flask`
4. Start Command: `python scripts/web_app.py`
5. Free plan-এ deploy হবে

---

## ⚙️ API Keys সেটআপ (Tools কাজ করতে)

App চালু হবে API key ছাড়াও। কিন্তু Research/Outreach কাজ করতে লাগবে।

`config/api_keys.env` ফাইলে:
```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
SENDGRID_API_KEY=SG....
```

Replit-এ Secrets-এ দাও (বেশি secure):
- Left panel → 🔒 Secrets
- Key ও Value দাও

---

## 📱 App-এ কী কী আছে

| Page | কাজ |
|------|-----|
| 🏠 হোম | Dashboard, progress, reminder |
| 🔍 রিসার্চ | Niche/location বেছে লিড খোঁজো |
| 📧 আউটরিচ | ইমেইল পাঠাও (dry-run + live) |
| 👥 লিডস | সব লিড দেখো, filter করো |
| 📊 রিপোর্ট | Weekly/monthly report তৈরি করো |

---

## 🆘 সমস্যা হলে

**"Flask not found":**
```bash
pip install flask
```

**"Port already in use":**
```bash
python scripts/web_app.py  # নিজেই আলাদা port নেবে
# অথবা:
PORT=8080 python scripts/web_app.py
```

**Termux-এ "pip not found":**
```bash
pkg install python
python -m pip install flask
```
