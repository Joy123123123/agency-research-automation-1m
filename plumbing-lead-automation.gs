// ============================================================
//  Plumbing Lead Automation — Google Apps Script
//  Paste this into the Script Editor bound to your Google
//  Sheet (the one that collects Form responses).
//
//  Setup:
//    1. Open Sheet → Extensions → Apps Script
//    2. Paste this entire file (replace any existing code)
//    3. Edit the CONFIG section below
//    4. Save, then add a "From spreadsheet > On form submit"
//       trigger pointing to onFormSubmit
// ============================================================

// ============================================================
//  CONFIG — edit these values before deploying
// ============================================================
var CONFIG = {
  // Display name shown in email subjects and bodies
  BUSINESS_NAME: "ABC Plumbing",

  // Where owner notifications are sent.
  // Leave empty ("") to send to whoever owns this script.
  OWNER_EMAIL: "",

  // Set true to also send an auto-reply email to the lead
  SEND_LEAD_AUTOREPLY: true
};

// ============================================================
//  HELPER
// ============================================================

/**
 * Safely extracts the first value from a namedValues array.
 * Returns "" if the key is missing or the array is empty.
 *
 * @param {Object} nv   - e.namedValues from the form submit event
 * @param {string} key  - The exact form question title
 * @returns {string}
 */
function get1(nv, key) {
  var arr = nv[key];
  if (!arr || arr.length === 0) return "";
  return String(arr[0]).trim();
}

// ============================================================
//  MAIN TRIGGER — wire this to "On form submit"
// ============================================================

/**
 * Runs automatically when a new Google Form response is submitted.
 * Sends an owner notification email and (optionally) a lead auto-reply.
 *
 * @param {GoogleAppsScript.Events.SheetsOnFormSubmit} e
 */
function onFormSubmit(e) {
  var nv = e.namedValues;

  // --- Pull form fields (must match form-question-titles.txt exactly) ---
  var leadName      = get1(nv, "Full Name");
  var leadEmail     = get1(nv, "Email Address");
  var leadPhone     = get1(nv, "Phone Number");
  var serviceType   = get1(nv, "Type of Plumbing Issue");
  var urgency       = get1(nv, "How Urgent Is This?");
  var address       = get1(nv, "Service Address (City, State)");
  var bestTime      = get1(nv, "Best Time to Call");
  var extraNotes    = get1(nv, "Additional Notes (optional)");
  var timestamp     = get1(nv, "Timestamp");

  // --- Resolve owner email ---
  // If OWNER_EMAIL is left blank, falls back to the Google account that
  // owns this Apps Script project (i.e., whoever authorized the trigger).
  // Set OWNER_EMAIL explicitly if the notification should go to a different
  // address than the account running the script.
  var ownerEmail = CONFIG.OWNER_EMAIL || Session.getActiveUser().getEmail();

  // ---- 1. Owner Notification Email --------------------------------
  var ownerSubject =
    "🚨 New Plumbing Lead: " + leadName + " (" + urgency + ")";

  var ownerBody =
    "You have a new plumbing lead from your Google Form!\n\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "  LEAD DETAILS\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "Name:          " + leadName    + "\n" +
    "Phone:         " + leadPhone   + "\n" +
    "Email:         " + leadEmail   + "\n" +
    "Issue:         " + serviceType + "\n" +
    "Urgency:       " + urgency     + "\n" +
    "Location:      " + address     + "\n" +
    "Best Time:     " + bestTime    + "\n" +
    "Notes:         " + extraNotes  + "\n" +
    "Submitted at:  " + timestamp   + "\n\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "ACTION: Call or text " + leadName + " at " + leadPhone +
    " as soon as possible.\n" +
    "Emergency leads expect a response within 15–30 minutes!\n\n" +
    "— " + CONFIG.BUSINESS_NAME + " Automation";

  GmailApp.sendEmail(ownerEmail, ownerSubject, ownerBody);

  // ---- 2. Lead Auto-Reply (optional) --------------------------------
  if (CONFIG.SEND_LEAD_AUTOREPLY && leadEmail) {
    var replySubject =
      "We Received Your Request — " + CONFIG.BUSINESS_NAME;

    var replyBody =
      "Hi " + leadName + ",\n\n" +
      "Thank you for reaching out to " + CONFIG.BUSINESS_NAME + "!\n\n" +
      "We've received your request regarding: " + serviceType + "\n\n" +
      "Our team will be in touch with you shortly" +
      (urgency.toLowerCase().indexOf("emergency") !== -1
        ? " — typically within 15–30 minutes for emergency calls"
        : " within a few hours") +
      ".\n\n" +
      "If your situation is a plumbing emergency (burst pipe, flooding, " +
      "no hot water), please also call us directly so we can dispatch " +
      "someone immediately.\n\n" +
      "What happens next:\n" +
      "  1. One of our plumbers will review your request.\n" +
      "  2. We'll call or text you at " + leadPhone + ".\n" +
      "  3. We'll schedule a time that works for you" +
      (bestTime ? " (you mentioned: " + bestTime + ")" : "") + ".\n\n" +
      "Thank you for choosing " + CONFIG.BUSINESS_NAME + ". " +
      "We look forward to helping you!\n\n" +
      "Best regards,\n" +
      CONFIG.BUSINESS_NAME + " Team\n\n" +
      "─────────────────────────────\n" +
      "This is an automated confirmation. Please do not reply to this " +
      "email. For urgent issues, call us directly.";

    GmailApp.sendEmail(leadEmail, replySubject, replyBody);
  }
}
