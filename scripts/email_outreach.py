# Email Outreach Automation
# Author: Md Jamil Islam

import smtplib
import csv
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional


def load_email_template(template_name: str) -> str:
    """
    Load an email template from the templates directory.
    
    Args:
        template_name: Name of the template (e.g., 'cold_outreach', 'follow_up')
    
    Returns:
        Template string with placeholders
    """
    templates = {
        "cold_outreach": """Hi {first_name},

I noticed {agency_name} is doing great work in {niche}. 

I help agencies like yours save 10-20 hours/week on research and competitor analysis — completely automated.

Would you be open to seeing a free sample report I created for a {niche} agency similar to yours?

Takes 5 minutes to review, and it's yours to keep either way.

Best,
Md Jamil Islam
Agency Research Automation
mdjamilislam.work@gmail.com
""",
        "follow_up_1": """Hi {first_name},

Just following up on my previous email about automated research reports for {agency_name}.

I know your inbox is busy, so I'll keep this short: I've helped agencies cut their research time by 80% while delivering better reports to clients.

Happy to send over a free sample — just say the word.

Best,
Md Jamil Islam
""",
        "follow_up_2": """Hi {first_name},

Last follow-up — I promise!

Quick question: is research and competitive analysis currently a challenge for {agency_name}?

If yes, I have a solution that's working really well for similar agencies right now.

If it's not a priority, completely understand — just let me know and I won't bother you again.

Best,
Md Jamil Islam
mdjamilislam.work@gmail.com
""",
    }
    
    return templates.get(template_name, "")


def personalize_email(template: str, contact: dict) -> str:
    """
    Replace template placeholders with contact-specific data.
    
    Args:
        template: Email template with {placeholder} variables
        contact: Dictionary with contact data
    
    Returns:
        Personalized email string
    """
    try:
        return template.format(
            first_name=contact.get("first_name", "there"),
            agency_name=contact.get("name", "your agency"),
            niche=contact.get("niche", "digital marketing"),
            location=contact.get("location", ""),
        )
    except KeyError as e:
        print(f"Warning: Missing template variable {e}")
        return template


def send_email(
    to_email: str,
    subject: str,
    body: str,
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    from_name: str = "Md Jamil Islam",
) -> bool:
    """
    Send a single email via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body text
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        username: SMTP username
        password: SMTP password
        from_name: Display name for sender
    
    Returns:
        True if sent successfully, False otherwise
    """
    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{username}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(username, password)
            server.send_message(msg)
        print(f"Email sent to: {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send to {to_email}: {e}")
        return False


def run_outreach_campaign(
    contacts_csv: str,
    template_name: str,
    subject: str,
    smtp_config: dict,
    daily_limit: int = 20,
):
    """
    Run an email outreach campaign from a contact list.
    
    Args:
        contacts_csv: Path to CSV file with contact data
        template_name: Name of template to use
        subject: Email subject line
        smtp_config: Dict with smtp_host, smtp_port, username, password
        daily_limit: Max emails to send per day
    """
    template = load_email_template(template_name)
    if not template:
        print(f"Template '{template_name}' not found")
        return
    
    try:
        with open(contacts_csv, "r", encoding="utf-8") as f:
            contacts = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"Contacts file not found: {contacts_csv}")
        return
    
    new_contacts = [c for c in contacts if c.get("status") == "new"][:daily_limit]
    print(f"Sending to {len(new_contacts)} contacts today...")
    
    sent = 0
    for contact in new_contacts:
        email = contact.get("email", "")
        if not email:
            continue
        
        body = personalize_email(template, contact)
        success = send_email(email, subject, body, **smtp_config)
        
        if success:
            sent += 1
            contact["status"] = "outreach_sent"
            contact["outreach_date"] = datetime.now().strftime("%Y-%m-%d")
        
        time.sleep(2)  # Avoid sending too fast
    
    print(f"\nCampaign complete: {sent}/{len(new_contacts)} emails sent")


if __name__ == "__main__":
    # Example usage (configure with real SMTP settings)
    template = load_email_template("cold_outreach")
    sample_contact = {
        "first_name": "John",
        "name": "Growth Agency NYC",
        "niche": "SEO",
        "location": "New York",
    }
    print(personalize_email(template, sample_contact))
