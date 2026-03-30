"""
Follow-Up Automation Module
Manages automated follow-up email sequences
Owner: Md Jamil Islam
"""
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FollowUpManager:
    """
    Manages automated follow-up sequences for leads.
    Tracks which follow-up step each lead is on and when to send next.
    """

    # Follow-up sequence timing (days after previous email)
    SEQUENCE = [
        {"day": 0,  "template": "initial_outreach",   "subject": "Quick question about {name}'s online presence"},
        {"day": 3,  "template": "follow_up_1",         "subject": "Re: Quick question about {name}'s online presence"},
        {"day": 7,  "template": "follow_up_2",         "subject": "Last follow-up — free website audit for {name}"},
        {"day": 14, "template": "breakup_email",       "subject": "Closing your file, {name}"},
    ]

    def __init__(self, tracking_file: str = "tracking/follow_ups.json"):
        self.tracking_file = Path(tracking_file)
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load follow-up tracking data."""
        if self.tracking_file.exists():
            with open(self.tracking_file) as f:
                return json.load(f)
        return {}

    def _save_data(self):
        """Save follow-up tracking data."""
        with open(self.tracking_file, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def enqueue_lead(self, lead_email: str, lead_name: str, lead_info: Dict):
        """Add a lead to the follow-up sequence."""
        self.data[lead_email] = {
            "name": lead_name,
            "info": lead_info,
            "current_step": 0,
            "last_sent": None,
            "next_send": datetime.now().isoformat(),
            "status": "active",
            "replied": False,
            "unsubscribed": False,
        }
        self._save_data()
        logger.info(f"Enqueued {lead_email} for follow-up sequence")

    def get_due_emails(self) -> List[Dict]:
        """Get all leads that are due for their next follow-up email."""
        due = []
        now = datetime.now()

        for email, data in self.data.items():
            if data.get("status") != "active":
                continue
            if data.get("replied") or data.get("unsubscribed"):
                continue

            step = data.get("current_step", 0)
            if step >= len(self.SEQUENCE):
                continue

            next_send_str = data.get("next_send")
            if not next_send_str:
                continue

            next_send = datetime.fromisoformat(next_send_str)
            if now >= next_send:
                due.append({
                    "email": email,
                    "name": data["name"],
                    "info": data.get("info", {}),
                    "step": step,
                    "template": self.SEQUENCE[step]["template"],
                    "subject_template": self.SEQUENCE[step]["subject"],
                })

        logger.info(f"{len(due)} leads due for follow-up")
        return due

    def mark_sent(self, email: str):
        """Mark an email as sent and advance to next step."""
        if email not in self.data:
            return

        data = self.data[email]
        step = data["current_step"]
        data["last_sent"] = datetime.now().isoformat()
        data["current_step"] = step + 1

        # Calculate next send date
        if step + 1 < len(self.SEQUENCE):
            days_until_next = self.SEQUENCE[step + 1]["day"] - self.SEQUENCE[step]["day"]
            next_send = datetime.now() + timedelta(days=days_until_next)
            data["next_send"] = next_send.isoformat()
        else:
            data["status"] = "completed"

        self._save_data()

    def mark_replied(self, email: str):
        """Mark a lead as having replied (stop sequence)."""
        if email in self.data:
            self.data[email]["replied"] = True
            self.data[email]["status"] = "replied"
            self._save_data()
            logger.info(f"Marked {email} as replied — stopping sequence")

    def unsubscribe(self, email: str):
        """Remove a lead from follow-up sequence."""
        if email in self.data:
            self.data[email]["unsubscribed"] = True
            self.data[email]["status"] = "unsubscribed"
            self._save_data()
