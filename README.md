# 🔧 Plumbing Lead Automation — Free Google-Only Demo

**For:** USA Plumbing SMBs  
**Cost to run:** $0/month (100% Google free tier)  
**Built for:** Android users — no laptop required  
**Goal:** Capture leads via Google Forms → log to Sheets → instant Gmail alert → optional auto-reply

---

## Table of Contents

1. [What You're Building](#what-youre-building)  
2. [Step 1 — Create the Google Form (Android)](#step-1--create-the-google-form-android)  
3. [Step 2 — Connect Form to Google Sheets](#step-2--connect-form-to-google-sheets)  
4. [Step 3 — Add the Apps Script Code](#step-3--add-the-apps-script-code)  
5. [Step 4 — Configure the Script](#step-4--configure-the-script)  
6. [Step 5 — Set Up the Trigger](#step-5--set-up-the-trigger)  
7. [Step 6 — Test Everything](#step-6--test-everything)  
8. [Troubleshooting on Mobile](#troubleshooting-on-mobile)  
9. [Pipeline Sheet Setup](#pipeline-sheet-setup)  
10. [Sales SOP — Daily Routine](#sales-sop--daily-routine)  
11. [Copy-Paste Outreach Templates](#copy-paste-outreach-templates)  
12. [FAQ / Notes](#faq--notes)

---

## What You're Building

```
Lead fills out Google Form
        ↓
Google Sheets logs the response automatically
        ↓
Apps Script triggers onFormSubmit()
        ↓
  ┌─────────────────────────────────┐
  │  Gmail → Business Owner Alert  │  (always)
  └─────────────────────────────────┘
        ↓
  ┌─────────────────────────────────┐
  │  Gmail → Lead Auto-Reply       │  (optional, toggle in config)
  └─────────────────────────────────┘
```

**Tools used:** Google Forms · Google Sheets · Google Apps Script · Gmail  
**Cost:** $0 — everything runs on Google's free tier  
**SMS:** Optional add-on (client-paid via Twilio) — not required for this demo

---

## Step 1 — Create the Google Form (Android)

> **Time:** ~15 minutes  
> **Mobile tip:** Use **Chrome** on Android. If a button is missing, tap the
> three-dot menu → **Desktop site** to switch to desktop mode.

### 1.1 Open Google Forms

1. Open **Chrome** on your Android phone.
2. Go to [forms.google.com](https://forms.google.com).
3. Sign in with your Google account.
4. Tap the **+** (plus) button to create a new blank form.

### 1.2 Set the Form Title and Description

- **Title:** `Plumbing Service Request`
- **Description:**  
  `Need a plumber? Fill out this quick form and we'll be in touch within 30 minutes!`

### 1.3 Add Questions (exact titles — copy from `templates/form-question-titles.txt`)

Add each question **in this order**. The script depends on these exact titles.

| # | Question Title | Type | Required |
|---|---------------|------|----------|
| 1 | `Full Name` | Short answer | ✅ Yes |
| 2 | `Email Address` | Short answer | ✅ Yes |
| 3 | `Phone Number` | Short answer | ✅ Yes |
| 4 | `Type of Plumbing Issue` | Multiple choice | ✅ Yes |
| 5 | `How Urgent Is This?` | Multiple choice | ✅ Yes |
| 6 | `Service Address (City, State)` | Short answer | ✅ Yes |
| 7 | `Best Time to Call` | Multiple choice | ✅ Yes |
| 8 | `Additional Notes (optional)` | Paragraph | ❌ No |

#### Question 4 — Type of Plumbing Issue (options)
- Burst or leaking pipe
- Drain clogged or backing up
- Water heater issue
- Toilet not flushing / overflowing
- Low water pressure
- Sewage smell / backup
- Faucet or fixture leak
- Other

#### Question 5 — How Urgent Is This? (options)
- 🚨 Emergency — right now
- Today (within a few hours)
- This week is fine
- Just getting a quote

#### Question 7 — Best Time to Call (options)
- Morning (8am–12pm)
- Afternoon (12pm–5pm)
- Evening (5pm–8pm)
- Anytime

### 1.4 (Optional) Set Up Form Confirmation Message

1. Click the **Settings** gear icon (top right).
2. Scroll to **Presentation**.
3. Set Confirmation message:  
   `Thanks! We received your request and will be in touch shortly. For emergencies, please call us directly.`

---

## Step 2 — Connect Form to Google Sheets

1. In the Form editor, tap the **Responses** tab.
2. Tap the **green Sheets icon** (Create Spreadsheet).
3. Choose **Create a new spreadsheet**.
4. Name it: `Plumbing Leads` → tap **Create**.

Google Sheets will now automatically log every new form submission.

---

## Step 3 — Add the Apps Script Code

> **Mobile tip:** Apps Script requires desktop mode in Chrome.

1. Open your **Plumbing Leads** Google Sheet.
2. Tap the three-dot menu (⋮) → **Desktop site**.
3. In the top menu, tap **Extensions → Apps Script**.
4. You'll see a new tab open with a default `myFunction()` — **delete all of it**.
5. Open the file `plumbing-lead-automation.gs` from this repository.  
   Copy its raw contents from GitHub:  
   go to the repository page → open `plumbing-lead-automation.gs` → tap **Raw** → select all → copy.
6. Copy the entire contents of the file.
7. Paste it into the Apps Script editor (replacing the deleted code).
8. Tap **Save** (the floppy disk icon or Ctrl+S).

---

## Step 4 — Configure the Script

At the top of the script, find the `CONFIG` block and update it:

```javascript
var CONFIG = {
  // Your business name — appears in email subject and body
  BUSINESS_NAME: "ABC Plumbing",   // ← Change this

  // Email address to receive lead notifications.
  // Leave "" to send to whoever owns this Google account.
  OWNER_EMAIL: "",                 // ← Add the owner's Gmail here (e.g. "owner@gmail.com")

  // Set to true to auto-reply to the lead's email
  SEND_LEAD_AUTOREPLY: true        // ← true = send auto-reply | false = don't
};
```

**Example (filled in):**
```javascript
var CONFIG = {
  BUSINESS_NAME: "Johnson Plumbing Co.",
  OWNER_EMAIL: "mike@johnsonplumbing.com",
  SEND_LEAD_AUTOREPLY: true
};
```

After editing, tap **Save** again.

---

## Step 5 — Set Up the Trigger

This tells Apps Script to run `onFormSubmit` every time a form response comes in.

1. In the Apps Script editor, tap the **clock icon** (Triggers) in the left sidebar.  
   *(If you don't see it, look for the icon that looks like an alarm clock.)*
2. Tap **+ Add Trigger** (bottom right).
3. Set the following options:

   | Setting | Value |
   |---------|-------|
   | Function to run | `onFormSubmit` |
   | Deployment | `Head` |
   | Event source | `From spreadsheet` |
   | Event type | `On form submit` |
   | Failure notification | `Notify me immediately` |

4. Tap **Save**.
5. Google will ask you to **authorize** the script — tap your account, then **Allow**.

> **Why authorize?** The script needs permission to read the form responses and send emails via Gmail.

---

## Step 6 — Test Everything

### 6.1 Submit a Test Form Response

1. Open your Google Form.
2. Tap the **eye icon** (Preview) to open the live form.
3. Fill it out with test data (use your own email in the Email field).
4. Submit it.

### 6.2 Check the Sheet

Open your **Plumbing Leads** Google Sheet — you should see a new row with the test data.

### 6.3 Check Gmail

Within 1–2 minutes you should receive:
- ✅ An email with subject: `🚨 New Plumbing Lead: [Name] ([Urgency])`
- ✅ (If `SEND_LEAD_AUTOREPLY: true`) An auto-reply email to the test address

### 6.4 Check the Trigger Execution Log

If emails didn't arrive:
1. In Apps Script → **Executions** (left sidebar).
2. You should see a recent execution of `onFormSubmit`.
3. If it shows an error, see [Troubleshooting](#troubleshooting-on-mobile).

---

## Troubleshooting on Mobile

| Problem | Fix |
|---------|-----|
| Can't see "Extensions" menu | Enable Desktop site in Chrome (three-dot menu → Desktop site) |
| Apps Script tab won't open | Make sure you're in the Sheet, not the Form; try Chrome not Samsung browser |
| "Authorization required" error | Run `onFormSubmit` manually once from the editor — it will prompt auth |
| Emails not arriving | Check Gmail Spam folder; check Executions log for errors |
| "Exception: Cannot call GmailApp" | Re-authorize the script (Triggers → edit → save → re-allow) |
| Form questions not matching | Confirm titles match exactly (including spaces and punctuation) from `templates/form-question-titles.txt` |
| Sheet not receiving responses | Go to Form → Responses tab → verify the green Sheets icon is linked |
| Script changes not saving | Make sure you saved (Ctrl+S or floppy disk icon) before testing |

---

## Pipeline Sheet Setup

Use the headers from `templates/pipeline-sheet-headers.csv` to create a second
sheet tab for tracking lead status.

### How to add the Pipeline tab:

1. In your **Plumbing Leads** Sheet, tap **+** at the bottom to add a new tab.
2. Name it `Pipeline`.
3. In cell A1, paste the first header; each subsequent header goes in the next
   column (B1, C1, …). The headers match the CSV in `templates/pipeline-sheet-headers.csv`:

```
Timestamp
Full Name
Email Address
Phone Number
Type of Plumbing Issue
How Urgent Is This?
Service Address (City, State)
Best Time to Call
Additional Notes
Status
Follow-Up Date
Assigned To
Job Value ($)
Notes
```

4. **Status column values to use:**
   - `New Lead`
   - `Contacted`
   - `Demo Sent`
   - `Closed - Won`
   - `Closed - Lost`
   - `Follow Up Later`

5. As leads come in, manually copy them from the **Form Responses** tab to **Pipeline** and update the Status column.

---

## Sales SOP — Daily Routine

This is how you sell this automation to plumbing businesses as a service.

### Your Offer (one sentence)
> "I'll set up a system that emails you the moment a new lead comes in and
> auto-replies to the lead — all free tools, no monthly software cost.
> Setup takes less than 24 hours."

### Daily Schedule (2–4 hours/day)

| Time | Task | Goal |
|------|------|------|
| 8:00 AM | Send 20–30 cold emails | New contacts daily |
| 9:00 AM | Send 20–30 DMs (Facebook, Nextdoor, Yelp) | Warm local leads |
| 11:00 AM | Reply to all responses from yesterday | Never leave a lead cold |
| 2:00 PM | Follow up with demo-watched prospects | Move to proposal |
| 4:00 PM | Log all activity in Pipeline sheet | Track progress |
| 5:00 PM | Review Pipeline — update statuses | 10-minute review |

### Weekly Goal
- **5 demos per week** → **2 closes per week**
- Setup fee: $500–$1,000 per client (one-time)
- Optional retainer: $99–$199/month (for support + updates)

### How to Demo (2 minutes)
1. Open your live Google Form on phone — fill it out live on the call.
2. Show the Sheet updating in real time.
3. Show the Gmail notification arriving within 1 minute.
4. Say: *"Your client sees this exact experience. They fill the form, you get
>    an instant alert, and the customer gets an auto-reply. Zero missed leads."*

---

## Copy-Paste Outreach Templates

See the full set in [`templates/outreach-email-templates.md`](templates/outreach-email-templates.md).

### Quick Cold Email (30 seconds to read)

**Subject:** Quick question about your missed plumbing leads, [First Name]

> Hi [First Name],
>
> I help plumbing companies in [City] automatically follow up with every new
> lead within 30 seconds — before they call your competitor.
>
> Most plumbers lose 40–60% of web leads just because they reply too slow.
> I fix that with a free Google-based system (no apps to buy).
>
> Can I send you a 2-minute demo video?
>
> — [Your Name]

### Quick DM (Facebook / Nextdoor)

> Hi [First Name]! Love what [Business Name] is doing. Quick question — do you
> have a way to auto-reply to new leads within 30 seconds? I help local plumbers
> set that up for free. Would love to show you a quick demo if interested!

---

## FAQ / Notes

**Q: Is this really free?**  
A: Yes. Google Forms, Google Sheets, Apps Script, and Gmail are all free for
personal and small business use. The only cost would be if you add SMS
(via Twilio, which is client-paid) — that's completely optional.

**Q: Can I add SMS notifications?**  
A: Yes, but SMS requires a Twilio account (client-paid, ~$1–5/month for
typical volume). The current setup covers email only, which works great for
most USA SMBs.

**Q: What if the business uses a different email provider?**  
A: The script uses Gmail (Google's free email). If the owner uses a non-Gmail
business email, set `OWNER_EMAIL` to their address — Gmail will still send
to any address. The auto-reply to the lead also works with any email address.

**Q: Can I use this for other home service niches?**  
A: Yes. Change `BUSINESS_NAME`, update the form question options (e.g., "Type
of HVAC Issue" instead of plumbing), and update the email copy in the script.

**Q: How many clients can I run this for?**  
A: Each client needs their own Google account, Sheet, and Apps Script project.
Gmail sends up to 100 emails/day on free accounts — more than enough for most
SMBs. Google Workspace accounts allow 1,500/day.

**Q: Is the lead's data secure?**  
A: Data stays in the client's own Google account. No third-party servers are
involved. This is a key selling point over paid SaaS tools.

---

*Built for the Android-first, USA SMB sales demo. No laptop required. 🚀*
