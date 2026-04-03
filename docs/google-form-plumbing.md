# Google Form — Plumbing (USA) Lead Capture

Copy/paste-ready question list to recreate the Plumbing lead-capture form in
Google Drive (works from desktop or Android).

---

## How to create the form (Android / Desktop)

1. Open **Google Drive** → tap **+** → **Google Forms**.
2. Give the form the title: **Plumbing Service Request**.
3. Add each question below **in order** using the question types shown.
4. Mark every question as **Required** (toggle in the bottom-right of each
   question card).
5. When finished, tap **Send** → copy the link to share with prospects.

---

## Google Form — copy/paste question titles and options

Add questions in this exact order so the Apps Script processes column headers
correctly.

---

### Q1 — Full Name
- **Type:** Short answer
- **Title (copy exactly):** `Full Name`
- No options needed.

---

### Q2 — Phone Number
- **Type:** Short answer
- **Title (copy exactly):** `Phone Number`
- No options needed.

---

### Q3 — Email Address
- **Type:** Short answer
- **Title (copy exactly):** `Email Address`
- No options needed.

---

### Q4 — Service Address (ZIP)
- **Type:** Short answer
- **Title (copy exactly):** `Service Address (ZIP)`
- No options needed (respondent enters their 5-digit ZIP code).

---

### Q5 — Preferred Contact Method
- **Type:** Dropdown
- **Title (copy exactly):** `Preferred Contact Method`
- **Options (copy in this order):**
  1. `Phone Call`
  2. `Text / SMS`
  3. `Email`
  4. `WhatsApp`

---

### Q6 — Issue Type
- **Type:** Dropdown
- **Title (copy exactly):** `Issue Type`
- **Options (copy in this order):**
  1. `Leaking Pipe`
  2. `Clogged Drain`
  3. `Water Heater Repair / Replacement`
  4. `Toilet Repair / Replacement`
  5. `Faucet / Fixture Repair`
  6. `Sewer Line Issue`
  7. `Low Water Pressure`
  8. `Gas Line Issue`
  9. `New Installation`
  10. `Other`

---

### Q7 — Emergency Level
- **Type:** Dropdown
- **Title (copy exactly):** `Emergency Level`
- **Options (copy in this order):**
  1. `Emergency — Need Help Now (same day)`
  2. `Urgent — Within 24 Hours`
  3. `Scheduled — Within This Week`
  4. `Planning Ahead — No Rush`

---

### Q8 — Best Time to Contact
- **Type:** Dropdown
- **Title (copy exactly):** `Best Time to Contact`
- **Options (copy in this order):**
  1. `Morning (8 AM – 12 PM)`
  2. `Afternoon (12 PM – 5 PM)`
  3. `Evening (5 PM – 8 PM)`
  4. `Anytime`

---

### Q9 — Short Description
- **Type:** Paragraph
- **Title (copy exactly):** `Short Description`
- No options needed (respondent writes a brief description of the problem).

---

## Full question block (quick reference)

```
Q1  Full Name                    — Short answer
Q2  Phone Number                 — Short answer
Q3  Email Address                — Short answer
Q4  Service Address (ZIP)        — Short answer
Q5  Preferred Contact Method     — Dropdown
      Phone Call | Text / SMS | Email | WhatsApp
Q6  Issue Type                   — Dropdown
      Leaking Pipe | Clogged Drain | Water Heater Repair / Replacement |
      Toilet Repair / Replacement | Faucet / Fixture Repair |
      Sewer Line Issue | Low Water Pressure | Gas Line Issue |
      New Installation | Other
Q7  Emergency Level              — Dropdown
      Emergency — Need Help Now (same day) |
      Urgent — Within 24 Hours |
      Scheduled — Within This Week |
      Planning Ahead — No Rush
Q8  Best Time to Contact         — Dropdown
      Morning (8 AM – 12 PM) | Afternoon (12 PM – 5 PM) |
      Evening (5 PM – 8 PM) | Anytime
Q9  Short Description            — Paragraph
```

---

## Apps Script compatibility

The Apps Script (`onFormSubmit` trigger) reads column headers by exact title.
Make sure the titles in your Google Form match these names character-for-character:

| Apps Script field key | Google Form question title   |
|-----------------------|------------------------------|
| `Full Name`           | Full Name                    |
| `Phone Number`        | Phone Number                 |
| `Email Address`       | Email Address                |
| `Service Address`     | Service Address (ZIP)        |
| `Preferred Contact`   | Preferred Contact Method     |
| `Issue Type`          | Issue Type                   |
| `Emergency Level`     | Emergency Level              |
| `Best Time`           | Best Time to Contact         |
| `Short Description`   | Short Description            |

> **Tip:** After creating the form, open the linked Google Sheet
> (**Responses** tab → spreadsheet icon) and confirm the header row matches
> the titles above before connecting the Apps Script.
