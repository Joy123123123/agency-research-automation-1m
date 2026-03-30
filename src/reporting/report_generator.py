"""
Report Generator Module
Generates weekly/monthly performance reports
Owner: Md Jamil Islam
"""
import logging
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates HTML, PDF, and CSV reports for the agency research automation system.
    """

    def __init__(self, tracking_dir: str = "tracking", reports_dir: str = "data/reports"):
        self.tracking_dir = Path(tracking_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_weekly_summary(self) -> Dict:
        """Generate a weekly performance summary."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        leads_data = self._load_leads()
        campaigns_data = self._load_campaigns()

        total_leads = len(leads_data)
        new_this_week = sum(
            1 for lead in leads_data
            if self._is_in_range(lead.get("created_at", ""), start_date, end_date)
        )
        emails_sent = sum(
            1 for lead in leads_data
            if lead.get("status") in ("contacted", "replied")
            and self._is_in_range(lead.get("contacted_at", ""), start_date, end_date)
        )
        replies = sum(1 for lead in leads_data if lead.get("status") == "replied")
        reply_rate = (replies / max(emails_sent, 1)) * 100

        summary = {
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "total_leads_in_db": total_leads,
            "new_leads_this_week": new_this_week,
            "emails_sent_this_week": emails_sent,
            "replies_this_week": replies,
            "reply_rate_pct": round(reply_rate, 1),
            "active_campaigns": len([c for c in campaigns_data if c.get("status") == "active"]),
            "revenue_this_week": self._estimate_revenue(leads_data, start_date, end_date),
            "generated_at": datetime.now().isoformat(),
        }

        logger.info(f"Weekly summary: {emails_sent} emails sent, {reply_rate:.1f}% reply rate")
        return summary

    def export_to_csv(self, leads: List[Dict], filename: Optional[str] = None) -> str:
        """Export leads to CSV file."""
        if not filename:
            filename = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = self.reports_dir / filename
        if not leads:
            logger.warning("No leads to export")
            return str(filepath)

        fieldnames = list(leads[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(leads)

        logger.info(f"Exported {len(leads)} leads to {filepath}")
        return str(filepath)

    def generate_html_report(self, summary: Dict) -> str:
        """Generate an HTML report from summary data."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Agency Research Report — {summary.get('period', '')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; }} h2 {{ color: #3498db; }}
        .metric {{ font-size: 2em; font-weight: bold; color: #27ae60; }}
        .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
    </style>
</head>
<body>
    <h1>🚀 Agency Research Automation — Weekly Report</h1>
    <p><strong>Period:</strong> {summary.get('period', 'N/A')}</p>
    <p><strong>Generated:</strong> {summary.get('generated_at', 'N/A')}</p>

    <div class="grid">
        <div class="card">
            <h2>New Leads</h2>
            <div class="metric">{summary.get('new_leads_this_week', 0)}</div>
        </div>
        <div class="card">
            <h2>Emails Sent</h2>
            <div class="metric">{summary.get('emails_sent_this_week', 0)}</div>
        </div>
        <div class="card">
            <h2>Reply Rate</h2>
            <div class="metric">{summary.get('reply_rate_pct', 0)}%</div>
        </div>
        <div class="card">
            <h2>Total Leads</h2>
            <div class="metric">{summary.get('total_leads_in_db', 0)}</div>
        </div>
        <div class="card">
            <h2>Active Campaigns</h2>
            <div class="metric">{summary.get('active_campaigns', 0)}</div>
        </div>
        <div class="card">
            <h2>Est. Revenue</h2>
            <div class="metric">${summary.get('revenue_this_week', 0):,.0f}</div>
        </div>
    </div>
</body>
</html>"""
        report_file = self.reports_dir / f"report_{datetime.now().strftime('%Y%m%d')}.html"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"HTML report saved: {report_file}")
        return str(report_file)

    def _load_leads(self) -> List[Dict]:
        """Load leads from tracking CSV."""
        leads_file = self.tracking_dir / "leads.csv"
        if not leads_file.exists():
            return []
        with open(leads_file, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _load_campaigns(self) -> List[Dict]:
        """Load campaign data."""
        campaigns_file = self.tracking_dir / "campaigns.json"
        if not campaigns_file.exists():
            return []
        with open(campaigns_file) as f:
            return json.load(f)

    def _is_in_range(self, date_str: str, start: datetime, end: datetime) -> bool:
        """Check if a date string falls within a range."""
        if not date_str:
            return False
        try:
            date = datetime.fromisoformat(date_str)
            return start <= date <= end
        except (ValueError, TypeError):
            return False

    def _estimate_revenue(
        self, leads: List[Dict], start: datetime, end: datetime
    ) -> float:
        """Estimate revenue from converted leads."""
        avg_deal_size = 2000  # USD
        converted = sum(
            1 for lead in leads
            if lead.get("status") == "converted"
            and self._is_in_range(lead.get("converted_at", ""), start, end)
        )
        return converted * avg_deal_size
