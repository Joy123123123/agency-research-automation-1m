#!/usr/bin/env python3
"""
Agency AI Assistant — Pure Python, No External API Required
Owner: Md Jamil Islam
Goal: $1,000,000 revenue

Advanced AI features:
- MarketIntelligence: US/Europe/Canada niche data with ROI scores
- NicheAdvisor: recommends best niche+location based on market value & close speed
- BusinessStrategist: CEO-level thinking — prioritises highest-ROI actions
- IntentMatcher: 20 intents, Bengali + English
- ContextLoader: reads live leads.csv + app_progress.json
- AgencyAI: full chat engine with per-session history
- Requires ZERO external API calls
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

# ── Revenue goal ──────────────────────────────────────────────────────────────
REVENUE_GOAL = 1_000_000  # USD
AVG_DEAL_SIZE = 2_000     # USD per client
MONTHLY_TARGETS = [
    (1, 3, 10_000, 20_000),    # months 1-3
    (4, 6, 30_000, 50_000),    # months 4-6
    (7, 9, 60_000, 80_000),    # months 7-9
    (10, 12, 90_000, 100_000), # months 10-12
]


# ═════════════════════════════════════════════════════════════════════════════
# Market Intelligence — US/Europe/Canada niche data (built-in, no API)
# ═════════════════════════════════════════════════════════════════════════════

class MarketIntelligence:
    """
    Built-in market data for agency target markets.
    All data is research-backed averages; no external API needed.
    """

    # Each entry: (niche, avg_deal_usd, close_speed_days, competition, demand, markets)
    # close_speed: lower = faster money; competition: 1-5 (5=hardest)
    NICHES: list[dict[str, Any]] = [
        {
            "name": "dentist",
            "label": "🦷 Dentist",
            "avg_deal": 2500,
            "close_days": 7,
            "competition": 2,
            "demand": 5,
            "roi_score": 95,
            "markets": ["USA", "Canada", "UK", "Australia"],
            "why": "High value, always needs patients, weak online presence, easy to show ROI",
            "email_angle": "Show them lost revenue from missing Google reviews/SEO",
        },
        {
            "name": "lawyer",
            "label": "⚖️ Lawyer / Law Firm",
            "avg_deal": 3500,
            "close_days": 10,
            "competition": 3,
            "demand": 5,
            "roi_score": 92,
            "markets": ["USA", "Canada", "UK"],
            "why": "Each new client = $5K-$50K for them; easy ROI math; low online presence",
            "email_angle": "One new client from Google pays for your service 10x over",
        },
        {
            "name": "restaurant",
            "label": "🍽️ Restaurant",
            "avg_deal": 1500,
            "close_days": 5,
            "competition": 3,
            "demand": 5,
            "roi_score": 88,
            "markets": ["USA", "Canada", "UK", "Europe"],
            "why": "Huge volume, fast close, easy to find via Google Maps, emotional owners",
            "email_angle": "Show competitor restaurant ranking higher on Google",
        },
        {
            "name": "real_estate",
            "label": "🏠 Real Estate Agent",
            "avg_deal": 3000,
            "close_days": 12,
            "competition": 4,
            "demand": 4,
            "roi_score": 85,
            "markets": ["USA", "Canada"],
            "why": "One listing = $5K-$20K commission; they understand marketing ROI",
            "email_angle": "Agents with strong Google presence get 3x more listings",
        },
        {
            "name": "gym",
            "label": "💪 Gym / Fitness",
            "avg_deal": 1800,
            "close_days": 8,
            "competition": 3,
            "demand": 4,
            "roi_score": 82,
            "markets": ["USA", "Canada", "UK", "Europe"],
            "why": "January/summer rush, membership model = recurring client value",
            "email_angle": "Competitors gyms getting 50+ new members/month from Instagram",
        },
        {
            "name": "plumber",
            "label": "🔧 Plumber / HVAC",
            "avg_deal": 2000,
            "close_days": 6,
            "competition": 2,
            "demand": 5,
            "roi_score": 90,
            "markets": ["USA", "Canada"],
            "why": "Urgent service, terrible online presence, high ticket jobs, easy wins",
            "email_angle": "Emergency calls go to whoever ranks #1 on Google — is that you?",
        },
        {
            "name": "electrician",
            "label": "⚡ Electrician",
            "avg_deal": 2000,
            "close_days": 6,
            "competition": 2,
            "demand": 5,
            "roi_score": 89,
            "markets": ["USA", "Canada", "UK"],
            "why": "Same as plumber — high demand, terrible online presence, fast close",
            "email_angle": "Your competitor electricians are booked weeks out from Google calls",
        },
        {
            "name": "chiro",
            "label": "🧘 Chiropractor / Physio",
            "avg_deal": 2200,
            "close_days": 8,
            "competition": 2,
            "demand": 4,
            "roi_score": 87,
            "markets": ["USA", "Canada", "Australia"],
            "why": "Recurring appointments, weak online presence, affluent clients",
            "email_angle": "Patients choose chiropractors based on Google reviews — how are yours?",
        },
        {
            "name": "salon",
            "label": "💇 Salon / Spa",
            "avg_deal": 1200,
            "close_days": 5,
            "competition": 3,
            "demand": 4,
            "roi_score": 78,
            "markets": ["USA", "Canada", "UK", "Europe"],
            "why": "Repeat customers, visual business perfect for Instagram/Google",
            "email_angle": "Top salons in your area are fully booked — here's how",
        },
        {
            "name": "accounting",
            "label": "📊 Accountant / CPA",
            "avg_deal": 3000,
            "close_days": 14,
            "competition": 3,
            "demand": 4,
            "roi_score": 83,
            "markets": ["USA", "Canada", "UK"],
            "why": "Tax season urgency, professional services, long-term retainer potential",
            "email_angle": "Business owners Googling CPAs choose who appears on page 1",
        },
    ]

    # Target market data
    MARKETS: dict[str, dict[str, Any]] = {
        "USA": {
            "flag": "🇺🇸",
            "avg_deal_multiplier": 1.0,
            "best_niches": ["dentist", "lawyer", "plumber", "electrician", "real_estate"],
            "best_cities": [
                "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin",
                "Miami", "Atlanta", "Seattle", "Denver", "Boston",
            ],
            "timezone": "EST/PST",
            "send_time": "9-11 AM EST (Tuesday-Thursday)",
            "avg_response_rate": "4-8%",
        },
        "Canada": {
            "flag": "🇨🇦",
            "avg_deal_multiplier": 0.9,
            "best_niches": ["dentist", "plumber", "real_estate", "lawyer", "gym"],
            "best_cities": [
                "Toronto", "Vancouver", "Montreal", "Calgary", "Edmonton",
                "Ottawa", "Winnipeg", "Quebec City", "Hamilton", "Kitchener",
            ],
            "timezone": "EST/PST",
            "send_time": "9-11 AM EST (Tuesday-Thursday)",
            "avg_response_rate": "5-9%",
        },
        "UK": {
            "flag": "🇬🇧",
            "avg_deal_multiplier": 0.85,
            "best_niches": ["dentist", "lawyer", "electrician", "salon", "accounting"],
            "best_cities": [
                "London", "Manchester", "Birmingham", "Leeds", "Glasgow",
                "Liverpool", "Bristol", "Sheffield", "Edinburgh", "Leicester",
            ],
            "timezone": "GMT",
            "send_time": "9-11 AM GMT (Tuesday-Thursday)",
            "avg_response_rate": "4-7%",
        },
        "Europe": {
            "flag": "🇪🇺",
            "avg_deal_multiplier": 0.8,
            "best_niches": ["restaurant", "gym", "salon", "dental", "accounting"],
            "best_cities": [
                "Berlin", "Paris", "Amsterdam", "Madrid", "Rome",
                "Vienna", "Zurich", "Brussels", "Stockholm", "Dublin",
            ],
            "timezone": "CET",
            "send_time": "9-11 AM CET (Tuesday-Thursday)",
            "avg_response_rate": "3-6%",
        },
        "Australia": {
            "flag": "🇦🇺",
            "avg_deal_multiplier": 0.95,
            "best_niches": ["dentist", "chiro", "plumber", "gym", "real_estate"],
            "best_cities": [
                "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
            ],
            "timezone": "AEST",
            "send_time": "9-11 AM AEST (Tuesday-Thursday)",
            "avg_response_rate": "5-8%",
        },
    }

    @classmethod
    def get_top_niches(cls, market: str = "USA", top_n: int = 5) -> list[dict[str, Any]]:
        """Return top N niches for a market, sorted by ROI score."""
        market_data = cls.MARKETS.get(market, cls.MARKETS["USA"])
        best = market_data["best_niches"]
        niches = [n for n in cls.NICHES if n["name"] in best]
        # Sort by roi_score descending
        niches.sort(key=lambda x: x["roi_score"], reverse=True)
        return niches[:top_n]

    @classmethod
    def get_niche(cls, name: str) -> dict[str, Any] | None:
        """Return niche data by name."""
        for n in cls.NICHES:
            if n["name"] == name:
                return n
        return None

    @classmethod
    def score_opportunity(
        cls,
        niche: str,
        market: str = "USA",
    ) -> dict[str, Any]:
        """Calculate opportunity score for niche+market combo."""
        nd = cls.get_niche(niche)
        md = cls.MARKETS.get(market, cls.MARKETS["USA"])
        if not nd:
            return {}
        adj_deal = int(nd["avg_deal"] * md["avg_deal_multiplier"])
        return {
            "niche": nd["label"],
            "market": f"{md['flag']} {market}",
            "adj_deal_usd": adj_deal,
            "roi_score": nd["roi_score"],
            "close_days": nd["close_days"],
            "why": nd["why"],
            "email_angle": nd["email_angle"],
            "send_time": md["send_time"],
        }


# ═════════════════════════════════════════════════════════════════════════════
# Business Strategist — CEO-level thinking, no API
# ═════════════════════════════════════════════════════════════════════════════

class BusinessStrategist:
    """
    Thinks like a business advisor.
    Analyses current pipeline data + market intel to recommend the single
    highest-ROI action the user should take right now.
    """

    @staticmethod
    def recommend(
        leads_stats: dict[str, Any],
        revenue_progress: dict[str, Any],
        market: str = "USA",
    ) -> dict[str, Any]:
        """
        Return a strategic recommendation based on current state.

        Returns:
            {
                "action": str,          # What to do NOW
                "reason": str,          # Why this is the best move
                "expected_result": str, # What happens if you do it
                "niche": str,           # Best niche to focus on
                "market": str,          # Best market to focus on
                "quick_win": str,       # Fastest path to next revenue
                "run_tool": str|None,   # Tool to run immediately
            }
        """
        total = leads_stats.get("total", 0)
        contacted = leads_stats.get("contacted", 0)
        replied = leads_stats.get("replied", 0)
        converted = leads_stats.get("converted", 0)
        est_revenue = revenue_progress.get("est_revenue", 0)

        top = MarketIntelligence.get_top_niches(market, top_n=1)
        best_niche = top[0] if top else MarketIntelligence.NICHES[0]
        mkt_data = MarketIntelligence.MARKETS.get(market, MarketIntelligence.MARKETS["USA"])

        if total == 0:
            return {
                "action": "🔍 Research করো — এখনই!",
                "reason": (
                    f"{mkt_data['flag']} {market}-এ {best_niche['label']} "
                    f"niche-এ ROI Score {best_niche['roi_score']}/100। "
                    "কিন্তু লিড ছাড়া কিছুই হবে না।"
                ),
                "expected_result": (
                    f"50+ লিড research করলে "
                    f"→ 5% reply rate → 2-3 জন interested "
                    f"→ 1 client → ${best_niche['avg_deal']:,}"
                ),
                "niche": best_niche["name"],
                "market": market,
                "quick_win": (
                    f"Research → Outreach → {best_niche['close_days']} দিনে first client"
                ),
                "run_tool": "/research",
            }

        if contacted == 0:
            reply_potential = int(total * 0.06)
            client_potential = max(1, int(reply_potential * 0.15))
            return {
                "action": "📧 Email পাঠাও — এখনই!",
                "reason": (
                    f"{total}টি লিড আছে কিন্তু কেউ email পায়নি। "
                    "প্রতিটি দিন delay = হারানো revenue।"
                ),
                "expected_result": (
                    f"{total} email → ~{reply_potential} reply "
                    f"→ ~{client_potential} client "
                    f"→ ~${client_potential * best_niche['avg_deal']:,}"
                ),
                "niche": best_niche["name"],
                "market": market,
                "quick_win": f"আজই {min(total, 100)} email পাঠাও → {best_niche['close_days']} দিনে client",
                "run_tool": "/outreach",
            }

        reply_rate = (replied / max(contacted, 1)) * 100
        if reply_rate < 2 and contacted >= 20:
            return {
                "action": "✍️ Email subject line পরিবর্তন করো",
                "reason": (
                    f"Reply rate মাত্র {reply_rate:.1f}% — "
                    "industry average 4-8%। Subject line সমস্যা।"
                ),
                "expected_result": (
                    "Better subject line → reply rate 5%+ "
                    f"→ {int(contacted * 0.05)} নতুন reply সম্ভব"
                ),
                "niche": best_niche["name"],
                "market": market,
                "quick_win": (
                    "Subject: 'Quick question about [Business Name]' "
                    "or '[City] competitor update'"
                ),
                "run_tool": "/outreach",
            }

        if replied > 0 and converted == 0:
            return {
                "action": "📞 Reply-দের Call করো — আজই!",
                "reason": (
                    f"{replied} জন reply করেছে কিন্তু কেউ client হয়নি! "
                    "এরা interested — শুধু follow-up দরকার।"
                ),
                "expected_result": (
                    f"{replied} reply-কে call করো "
                    f"→ 30% close rate → "
                    f"${int(replied * 0.3 * best_niche['avg_deal']):,} potential revenue"
                ),
                "niche": best_niche["name"],
                "market": market,
                "quick_win": (
                    "Reply-দের WhatsApp/email করো: "
                    "'Are you still looking for help with [problem]?'"
                ),
                "run_tool": "/leads",
            }

        # Default: scale up
        monthly_revenue = converted * best_niche["avg_deal"]
        scale_factor = max(2, int(REVENUE_GOAL / max(monthly_revenue * 12, 1) * 2))
        return {
            "action": "🚀 Volume বাড়াও!",
            "reason": (
                f"Pipeline চলছে! {converted} client, "
                f"est. ${est_revenue:,} revenue। "
                f"$1M-এ পৌঁছাতে {scale_factor}x বেশি leads দরকার।"
            ),
            "expected_result": (
                f"Daily leads {scale_factor}x করো "
                f"→ proportional revenue growth "
                f"→ $1M timeline অনুযায়ী"
            ),
            "niche": best_niche["name"],
            "market": market,
            "quick_win": (
                f"নতুন city target: {mkt_data['best_cities'][converted % len(mkt_data['best_cities'])]}"
            ),
            "run_tool": "/research",
        }


# ═════════════════════════════════════════════════════════════════════════════
# Intent detection — keyword-based, Bengali & English
# ═════════════════════════════════════════════════════════════════════════════

class IntentMatcher:
    """Matches user messages to intents using keyword lists."""

    INTENTS: dict[str, list[str]] = {
        "greeting": [
            "হ্যালো", "হেলো", "আসসালামু", "সালাম",
            "hi", "hello", "hey", "assalam",
        ],
        "what_to_do_today": [
            "আজ কী করব", "আজকে কী", "আজ কি কাজ", "কী করতে হবে",
            "কোথা থেকে শুরু", "শুরু করব", "আজকের কাজ", "কোন কাজ",
            "what to do", "today task", "daily task", "where to start",
            "what should i do", "what next",
        ],
        "how_to_research": [
            "রিসার্চ", "লিড খুঁজ", "নতুন লিড", "গুগল ম্যাপ",
            "কোন নিশ", "কোথায় খুঁজব", "নিশ কি",
            "research", "find leads", "new leads", "google maps", "niche",
        ],
        "how_to_email": [
            "ইমেইল", "মেইল পাঠ", "আউটরিচ", "কিভাবে পাঠাব",
            "সেন্ড করব", "এক্সপোর্ট", "টেমপ্লেট", "কাকে পাঠাব",
            "email", "send email", "outreach", "template", "send mail",
        ],
        "progress": [
            "প্রগ্রেস", "কতটুক হলো", "এগিয়ে", "টার্গেট",
            "রেভিনিউ কত", "কত আয়", "কত হলো", "আমার অবস্থা",
            "progress", "how much done", "revenue", "target", "milestone",
            "how am i doing", "status",
        ],
        "tool_help": [
            "টুলস", "কোন টুল", "কিভাবে ব্যবহার", "টুল কি",
            "কোনটা ব্যবহার করব",
            "tool", "which tool", "how to use", "what tool", "tools",
        ],
        "api_key": [
            "এপিআই", "এপিকী", "key", "api key", "sendgrid", "openai",
            "গুগল কী", "কী কোথায়", "কোথায় পাব",
            "api", "google key", "where to get key",
        ],
        "follow_up": [
            "ফলো আপ", "রিপ্লাই", "পরের মেইল", "কেউ রিপ্লাই দিলে",
            "follow up", "reply", "second email", "no reply",
        ],
        "revenue_target": [
            "১ মিলিয়ন", "এক মিলিয়ন", "টার্গেট কত", "কত আয় করতে হবে",
            "মিলিয়ন ডলার", "goal",
            "1 million", "million", "revenue goal", "how much to earn",
        ],
        "crm_airtable": [
            "এয়ারটেবল", "সিআরএম", "ডেটা সেভ", "লিড সেভ",
            "airtable", "crm", "save data", "database",
        ],
        "replit_setup": [
            "রেপ্লিট", "কিভাবে চালাব", "কিভাবে খুলব", "শুরু করব কিভাবে",
            "replit", "how to run", "how to open", "setup", "start app",
        ],
        "termux_setup": [
            "টার্মাক্স", "অ্যান্ড্রয়েড", "মোবাইলে", "ফোনে চালাব",
            "termux", "android", "mobile", "phone",
        ],
        "lead_scoring": [
            "গ্রেড", "স্কোর", "কোন লিড ভালো", "এ গ্রেড",
            "grade", "score", "best lead", "a grade", "priority",
        ],
        "conversion": [
            "কনভার্ট", "ক্লায়েন্ট হলো", "ডিল", "ক্লোজ",
            "convert", "client", "deal", "close", "signed",
        ],
        "schedule": [
            "কখন করব", "সময়সূচি", "রুটিন", "কখন মেইল",
            "schedule", "routine", "when to send", "what time",
        ],
        "help": [
            "হেল্প", "সাহায্য", "বুঝতে পারছি না", "কনফিউজড",
            "help", "confused", "dont understand", "explain",
        ],
        "next_step": [
            "পরের কাজ", "এরপর কী", "কী করব এখন", "পরবর্তী",
            "next", "after this", "what now", "then what",
        ],
        # ── New advanced intents ─────────────────────────────────────
        "market_intelligence": [
            "কোন মার্কেট", "আমেরিকা মার্কেট", "ইউরোপ", "কানাডা",
            "কোন দেশ", "কোথায় বেশি", "মার্কেট ভ্যালু",
            "market", "usa market", "which country", "best market",
            "america", "europe", "canada", "uk market", "where to target",
        ],
        "niche_advice": [
            "কোন নিশ সেরা", "কোনটায় বেশি লাভ", "কোন বিজনেস", "দ্রুত কোনটা",
            "best niche", "which niche", "fastest niche", "highest paying",
            "most profitable", "niche recommend", "which business type",
        ],
        "strategy": [
            "স্ট্র্যাটেজি", "কৌশল", "কি করা উচিত", "সেরা উপায়",
            "বেস্ট প্ল্যান", "কিভাবে স্কেল", "দ্রুত বাড়াব",
            "strategy", "plan", "best approach", "how to scale",
            "grow fast", "scale up", "best move", "what should i focus",
        ],
        "always_on": [
            "সব সময় চালু", "background", "ফোন বন্ধ", "লক করলে",
            "always running", "background run", "phone locked", "keep running",
            "replit always on", "24/7", "নিরন্তর",
        ],
    }

    @classmethod
    def detect(cls, message: str) -> str:
        """Return the best-matching intent for a message."""
        msg_lower = message.lower().strip()

        scores: dict[str, int] = {}
        for intent, keywords in cls.INTENTS.items():
            score = sum(1 for kw in keywords if kw.lower() in msg_lower)
            if score:
                scores[intent] = score

        if not scores:
            return "unknown"
        return max(scores, key=lambda k: scores[k])


# ═════════════════════════════════════════════════════════════════════════════
# Context loader — reads live data from the project files
# ═════════════════════════════════════════════════════════════════════════════

class ContextLoader:
    """Loads live project data so the AI can give accurate answers."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.tracking_dir = base_dir / "tracking"
        self.progress_file = self.tracking_dir / "app_progress.json"
        self.leads_file = self.tracking_dir / "leads.csv"

    def get_leads_stats(self) -> dict[str, Any]:
        """Return basic lead statistics."""
        import csv
        from collections import Counter

        if not self.leads_file.exists():
            return {"total": 0, "new": 0, "contacted": 0, "replied": 0, "converted": 0}

        try:
            with open(self.leads_file, encoding="utf-8") as f:
                lines = [ln for ln in f if not ln.startswith("#")]
            rows = list(csv.DictReader(lines))
        except Exception:
            return {"total": 0, "new": 0, "contacted": 0, "replied": 0, "converted": 0}

        if not rows:
            return {"total": 0, "new": 0, "contacted": 0, "replied": 0, "converted": 0}

        status_counts = Counter(
            {k: v for k, v in Counter(r.get("status", "new") for r in rows).items()}
        )
        return {
            "total": len(rows),
            "new": status_counts.get("new", 0),
            "contacted": status_counts.get("contacted", 0),
            "replied": status_counts.get("replied", 0),
            "converted": status_counts.get("converted", 0),
        }

    def get_progress(self) -> dict[str, Any]:
        """Return task progress data."""
        if not self.progress_file.exists():
            return {}
        try:
            with open(self.progress_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_pending_tasks(self) -> list[str]:
        """Return list of pending daily task titles (simplified)."""
        progress = self.get_progress()
        today = date.today().isoformat()
        pending = []
        daily_task_ids = [
            ("morning_research", "নতুন লিড রিসার্চ"),
            ("morning_inbox", "Inbox চেক"),
            ("morning_review", "Lead Review"),
            ("outreach_initial", "Initial Email পাঠাও"),
            ("outreach_followup", "Follow-up পাঠাও"),
            ("analytics_stats", "Lead Stats দেখো"),
            ("analytics_sendgrid", "Email Stats চেক"),
            ("analytics_update", "Lead Status আপডেট"),
            ("followup_replies", "Reply-দের উত্তর"),
            ("followup_crm", "CRM Update"),
        ]
        for task_id, title in daily_task_ids:
            rec = progress.get(task_id, {})
            if rec.get("last_done", "") != today:
                pending.append(title)
        return pending

    def get_revenue_progress(self) -> dict[str, Any]:
        """Estimate revenue progress toward $1M goal."""
        stats = self.get_leads_stats()
        converted = stats.get("converted", 0)
        est_revenue = converted * AVG_DEAL_SIZE
        pct = round((est_revenue / REVENUE_GOAL) * 100, 2)
        return {
            "converted_clients": converted,
            "est_revenue": est_revenue,
            "goal": REVENUE_GOAL,
            "pct": pct,
            "remaining": REVENUE_GOAL - est_revenue,
            "leads_needed_for_goal": max(0, (REVENUE_GOAL - est_revenue) // AVG_DEAL_SIZE),
        }


# ═════════════════════════════════════════════════════════════════════════════
# Response generator — rule-based, context-aware
# ═════════════════════════════════════════════════════════════════════════════

class AgencyAI:
    """
    Pure Python AI assistant for agency automation.
    No external API required. Context-aware, Bengali-first.
    """

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.ctx = ContextLoader(base_dir)
        # In-memory conversation history per session (list of dicts)
        self._history: list[dict[str, str]] = []

    # ── Public interface ──────────────────────────────────────────────────────

    def chat(self, user_message: str) -> dict[str, Any]:
        """
        Process a user message and return a structured response.

        Returns:
            {
                "reply": str,          # Main reply text (Markdown)
                "intent": str,         # Detected intent
                "quick_actions": list, # Suggested next buttons
                "tool_link": str|None, # Direct tool URL if applicable
                "run_cmd": str|None,   # Script command to auto-run
            }
        """
        intent = IntentMatcher.detect(user_message)
        self._history.append({"role": "user", "content": user_message, "intent": intent})

        handler = self._get_handler(intent)
        result = handler(user_message)
        result["intent"] = intent

        self._history.append({"role": "assistant", "content": result["reply"]})
        return result

    def get_history(self) -> list[dict[str, str]]:
        """Return conversation history."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history.clear()

    def daily_briefing(self) -> dict[str, Any]:
        """
        Generate a daily briefing — what to do today, revenue status.
        Called automatically when the AI page loads.
        """
        pending = self.ctx.get_pending_tasks()
        stats = self.ctx.get_leads_stats()
        rev = self.ctx.get_revenue_progress()

        now_hour = datetime.now().hour

        if now_hour < 10:
            time_greeting = "🌅 সুপ্রভাত! আজকের সকালের কাজ শুরু করা যাক।"
        elif now_hour < 13:
            time_greeting = "🌤️ গুড মর্নিং! আউটরিচ সময় এসে গেছে।"
        elif now_hour < 17:
            time_greeting = "☀️ বিকেলের Follow-up করার সময়।"
        else:
            time_greeting = "🌙 সন্ধ্যার রিভিউ সময়।"

        lines = [
            f"## {time_greeting}",
            "",
            f"**📊 আজকের Stats:**",
            f"- মোট লিড: **{stats['total']}**",
            f"- Reply: **{stats['replied']}**",
            f"- Client: **{stats['converted']}**",
            f"- Est. Revenue: **${rev['est_revenue']:,}** / $1,000,000",
            "",
        ]

        if rev["pct"] < 1:
            lines.append(
                "🚀 **Revenue Journey শুরু হয়নি।** "
                "প্রথম lead research করো এখনই!"
            )
        else:
            lines.append(
                f"📈 **Goal Progress: {rev['pct']}%** "
                f"(আরও ${rev['remaining']:,} দরকার)"
            )

        lines.append("")

        if pending:
            lines.append(f"**⏳ আজকের {len(pending)}টি কাজ বাকি:**")
            for i, task in enumerate(pending[:5], 1):
                lines.append(f"{i}. {task}")
            if len(pending) > 5:
                lines.append(f"   ...এবং আরও {len(pending) - 5}টি।")
        else:
            lines.append("**✅ আজকের সব কাজ শেষ! দারুণ!**")

        lines += [
            "",
            "**আমাকে জিজ্ঞেস করো:**",
            "👉 _আজ কী করব?_",
            "👉 _আমার প্রগ্রেস কেমন?_",
            "👉 _কোন tool লাগবে?_",
        ]

        quick_actions = [
            {"label": "📋 আজকের কাজ", "msg": "আজ কী করব?"},
            {"label": "📊 আমার progress", "msg": "আমার progress কেমন?"},
            {"label": "🔍 Research করব", "msg": "কিভাবে রিসার্চ করব?"},
            {"label": "📧 Email পাঠাব", "msg": "কিভাবে email পাঠাব?"},
        ]

        return {
            "reply": "\n".join(lines),
            "intent": "briefing",
            "quick_actions": quick_actions,
            "tool_link": None,
            "run_cmd": None,
        }

    # ── Intent handlers ───────────────────────────────────────────────────────

    def _get_handler(self, intent: str):
        handlers = {
            "greeting": self._handle_greeting,
            "what_to_do_today": self._handle_today,
            "how_to_research": self._handle_research,
            "how_to_email": self._handle_email,
            "progress": self._handle_progress,
            "tool_help": self._handle_tools,
            "api_key": self._handle_api_key,
            "follow_up": self._handle_followup,
            "revenue_target": self._handle_revenue,
            "crm_airtable": self._handle_crm,
            "replit_setup": self._handle_replit,
            "termux_setup": self._handle_termux,
            "lead_scoring": self._handle_scoring,
            "conversion": self._handle_conversion,
            "schedule": self._handle_schedule,
            "help": self._handle_help,
            "next_step": self._handle_next_step,
            # ── Advanced intents ──────────────────────────────────────
            "market_intelligence": self._handle_market,
            "niche_advice": self._handle_niche_advice,
            "strategy": self._handle_strategy,
            "always_on": self._handle_always_on,
            "unknown": self._handle_unknown,
        }
        return handlers.get(intent, self._handle_unknown)

    # ─────────────────────────────────────────────────────────────────────────

    def _handle_greeting(self, _msg: str) -> dict[str, Any]:
        rev = self.ctx.get_revenue_progress()
        stats = self.ctx.get_leads_stats()
        return {
            "reply": (
                f"## আস্সালামু আলাইকুম! 👋\n\n"
                f"আমি তোমার Agency AI Assistant। "
                f"আমি **API ছাড়াই** কাজ করি — সম্পূর্ণ offline!\n\n"
                f"**তোমার এখনকার অবস্থা:**\n"
                f"- মোট লিড: **{stats['total']}**\n"
                f"- Client: **{stats['converted']}**\n"
                f"- Est. Revenue: **${rev['est_revenue']:,}**\n"
                f"- Goal: **$1,000,000** ({rev['pct']}% done)\n\n"
                f"**আমাকে জিজ্ঞেস করো যেকোনো কিছু!**\n"
                f"যেমন: _আজ কী করব?_ বা _কিভাবে লিড খুঁজব?_"
            ),
            "quick_actions": [
                {"label": "📋 আজকের কাজ", "msg": "আজ কী করব?"},
                {"label": "📊 Progress দেখাও", "msg": "আমার progress?"},
                {"label": "🛠️ Tools দেখাও", "msg": "কোন tool লাগবে?"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    def _handle_today(self, _msg: str) -> dict[str, Any]:
        pending = self.ctx.get_pending_tasks()
        now_hour = datetime.now().hour

        if now_hour < 10:
            phase = "সকালের কাজ (9-10 AM)"
            tasks = [
                "1️⃣ **Research Tool** খোলো → নতুন লিড খোঁজো (50+ লিড)",
                "2️⃣ **Inbox** চেক করো (Gmail / SendGrid)",
                "3️⃣ নতুন **A/B grade** lead গুলো দেখো",
            ]
        elif now_hour < 13:
            phase = "আউটরিচ সময় (10-11 AM)"
            tasks = [
                "1️⃣ **Outreach Tool** খোলো",
                "2️⃣ প্রথমে **Dry Run** করো (preview)",
                "3️⃣ ঠিক থাকলে **Send** করো (50-200 মেইল)",
                "4️⃣ **Follow-up** ও দাও (3/7/14 দিন পর)",
            ]
        elif now_hour < 17:
            phase = "বিকেলের কাজ (3-4 PM)"
            tasks = [
                "1️⃣ **Inbox** দেখো — reply এসেছে কিনা",
                "2️⃣ আগ্রহী lead-দের ব্যক্তিগত reply করো",
                "3️⃣ Lead **status আপডেট** করো (Leads page)",
                "4️⃣ **Stats** দেখো — আজ কেমন গেলো",
            ]
        else:
            phase = "সন্ধ্যার রিভিউ"
            tasks = [
                "1️⃣ আজকের **পরিসংখ্যান** দেখো",
                "2️⃣ কাল কোন **niche/location** করবে plan করো",
                "3️⃣ **Progress mark** করো — সব done দাও",
            ]

        pending_txt = ""
        if pending:
            pending_txt = (
                f"\n\n**⚠️ এখনো বাকি আছে ({len(pending)}টি):**\n"
                + "\n".join(f"- {t}" for t in pending[:5])
            )

        return {
            "reply": (
                f"## 📋 {phase}\n\n"
                f"**এখন যা করতে হবে:**\n"
                + "\n".join(tasks)
                + pending_txt
                + f"\n\n💡 _নিচের বাটন চাপো বা আমাকে জিজ্ঞেস করো কোনো step নিয়ে।_"
            ),
            "quick_actions": [
                {"label": "🔍 Research শুরু", "msg": "কিভাবে research করব?"},
                {"label": "📧 Email পাঠাব", "msg": "কিভাবে email পাঠাব?"},
                {"label": "📊 Stats দেখাও", "msg": "আমার stats কেমন?"},
                {"label": "✅ Dashboard", "msg": "dashboard দেখাও"},
            ],
            "tool_link": "/",
            "run_cmd": None,
        }

    def _handle_research(self, _msg: str) -> dict[str, Any]:
        stats = self.ctx.get_leads_stats()
        suggestion = ""
        if stats["total"] < 50:
            suggestion = (
                "\n\n⚠️ **তোমার এখনো মাত্র "
                f"{stats['total']}টি লিড আছে।** "
                "আজই ৫০+ লিড research করো!"
            )

        return {
            "reply": (
                "## 🔍 কিভাবে Research করবে?\n\n"
                "**ধাপে ধাপে:**\n\n"
                "**ধাপ ১: Research Tool খোলো**\n"
                "→ নিচে বাটন আছে: _Research Tool খোলো_\n\n"
                "**ধাপ ২: Niche বেছে নাও**\n"
                "ভালো niche (সহজে convert হয়):\n"
                "- 🍽️ **Restaurant** — প্রথম choice\n"
                "- 🦷 **Dentist** — high value\n"
                "- ⚖️ **Lawyer** — premium\n"
                "- 💪 **Gym** — social media দরকার\n\n"
                "**ধাপ ৩: Location দাও**\n"
                "শুরু করো: Dhaka বা Chittagong\n\n"
                "**ধাপ ৪: Count দাও**\n"
                "প্রতিদিন কমপক্ষে **50 লিড** research করো\n\n"
                "**ধাপ ৫: Run করো**\n"
                "→ _রিসার্চ শুরু করো_ বাটন চাপো\n"
                "→ Live output দেখাবে\n"
                "→ Automatically leads.csv-এ save হবে\n\n"
                "**API Key না থাকলে:**\n"
                "→ _Skip scraping_ toggle ON করো\n"
                "→ তারপরও ৫০+ লিড পাবে"
                + suggestion
            ),
            "quick_actions": [
                {"label": "🔍 Research Tool খোলো", "msg": "__goto__/research"},
                {"label": "📊 Leads দেখাও", "msg": "__goto__/leads"},
                {"label": "⏭️ পরের কাজ কী?", "msg": "research করার পরে কী করব?"},
            ],
            "tool_link": "/research",
            "run_cmd": None,
        }

    def _handle_email(self, _msg: str) -> dict[str, Any]:
        stats = self.ctx.get_leads_stats()
        if stats["total"] == 0:
            return {
                "reply": (
                    "## 📧 Email পাঠানোর আগে...\n\n"
                    "⚠️ **এখনো কোনো লিড নেই!**\n\n"
                    "প্রথমে **Research Tool** দিয়ে লিড সংগ্রহ করো,\n"
                    "তারপর email পাঠাও।\n\n"
                    "Research করতে নিচের বাটন চাপো।"
                ),
                "quick_actions": [
                    {"label": "🔍 Research করো আগে", "msg": "__goto__/research"},
                ],
                "tool_link": "/research",
                "run_cmd": None,
            }

        return {
            "reply": (
                "## 📧 কিভাবে Email পাঠাবে?\n\n"
                f"তোমার কাছে এখন **{stats['total']}টি লিড** আছে।\n\n"
                "**ধাপ ১: Outreach Tool খোলো**\n\n"
                "**ধাপ ২: Campaign বেছে নাও**\n"
                "- **Initial** → প্রথম email (নতুন লিড)\n"
                "- **Follow-up** → আগে পাঠানো লিড\n\n"
                "**ধাপ ৩: ⚠️ প্রথমে DRY RUN করো!**\n"
                "→ Dry Run ON রাখো\n"
                "→ Preview দেখো — email ঠিক আছে কিনা\n\n"
                "**ধাপ ৪: Real Send করো**\n"
                "→ Dry Run OFF করো\n"
                "→ Daily limit: **50-200** email\n"
                "→ _পাঠাও_ বাটন চাপো\n\n"
                "**Daily Limit মেনে চলো:**\n"
                "- SendGrid Free: 100/দিন\n"
                "- ধীরে ধীরে বাড়াও spam এড়াতে\n\n"
                "**SendGrid API Key কোথায় পাব?**\n"
                "→ sendgrid.com → free account → Settings → API Keys"
            ),
            "quick_actions": [
                {"label": "📧 Outreach Tool", "msg": "__goto__/outreach"},
                {"label": "🔑 API Key কোথায়?", "msg": "API key কোথায় পাব?"},
                {"label": "📊 Leads দেখো", "msg": "__goto__/leads"},
            ],
            "tool_link": "/outreach",
            "run_cmd": None,
        }

    def _handle_progress(self, _msg: str) -> dict[str, Any]:
        stats = self.ctx.get_leads_stats()
        rev = self.ctx.get_revenue_progress()
        pending = self.ctx.get_pending_tasks()
        progress_data = self.ctx.get_progress()
        done_count = sum(1 for v in progress_data.values() if v.get("done"))

        contacted = stats["contacted"] + stats["replied"]
        reply_rate = round((stats["replied"] / max(contacted, 1)) * 100, 1)

        # Visual progress bar (ASCII)
        bars = int(rev["pct"] / 5)
        bar = "█" * bars + "░" * (20 - bars)

        grade = ""
        if reply_rate >= 10:
            grade = "🔥 Excellent!"
        elif reply_rate >= 5:
            grade = "✅ Good"
        elif reply_rate >= 2:
            grade = "⚡ Keep going"
        else:
            grade = "💪 শুরু করো"

        return {
            "reply": (
                "## 📊 তোমার Progress Report\n\n"
                f"**💰 Revenue Goal:** $1,000,000\n"
                f"```\n[{bar}] {rev['pct']}%\n```\n"
                f"**Est. Revenue:** ${rev['est_revenue']:,}\n"
                f"**Remaining:** ${rev['remaining']:,}\n\n"
                "---\n\n"
                "**📋 Lead Pipeline:**\n"
                f"- নতুন লিড: **{stats['new']}**\n"
                f"- Contacted: **{stats['contacted']}**\n"
                f"- Reply আসা: **{stats['replied']}**\n"
                f"- Client হয়েছে: **{stats['converted']}** 🎉\n\n"
                f"**Reply Rate: {reply_rate}%** {grade}\n\n"
                "---\n\n"
                f"**✅ Tasks Done:** {done_count}\n"
                f"**⏳ আজকের বাকি:** {len(pending)}টি\n\n"
                "**$1M পেতে কত লিড লাগবে:**\n"
                f"- আরও **{rev['leads_needed_for_goal']}** জন client দরকার\n"
                f"- মানে প্রতি $2,000/client হিসেবে\n\n"
                "_Leads বাড়াও → Email পাঠাও → Follow-up করো → Client হবে!_"
            ),
            "quick_actions": [
                {"label": "📈 Dashboard", "msg": "__goto__/"},
                {"label": "🔍 আরো লিড Research", "msg": "কিভাবে research করব?"},
                {"label": "📧 Email পাঠাও", "msg": "কিভাবে email পাঠাব?"},
            ],
            "tool_link": "/reports",
            "run_cmd": None,
        }

    def _handle_tools(self, _msg: str) -> dict[str, Any]:
        return {
            "reply": (
                "## 🛠️ তোমার সব Tools\n\n"
                "**App-এর ভেতরে যা আছে:**\n\n"
                "| Tool | কাজ | Link |\n"
                "|------|-----|------|\n"
                "| 🔍 Research | লিড খোঁজা | `/research` |\n"
                "| 📧 Outreach | Email পাঠানো | `/outreach` |\n"
                "| 👥 Leads | লিড দেখা | `/leads` |\n"
                "| 📊 Reports | রিপোর্ট তৈরি | `/reports` |\n"
                "| 🤖 AI | আমি! Guide করা | `/ai` |\n\n"
                "**Background Scripts:**\n"
                "- `run_research.py` → Research চালায়\n"
                "- `send_outreach.py` → Email পাঠায়\n"
                "- `generate_report.py` → Report তৈরি করে\n"
                "- `scheduler.py` → Auto-schedule\n\n"
                "**কোনো tool-এর সাথে পরিচয় হতে চাও?**\n"
                "বলো: _Research tool কিভাবে ব্যবহার করব?_"
            ),
            "quick_actions": [
                {"label": "🔍 Research Tool", "msg": "কিভাবে research করব?"},
                {"label": "📧 Outreach Tool", "msg": "কিভাবে email পাঠাব?"},
                {"label": "📊 Report Tool", "msg": "report কিভাবে বানাব?"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    def _handle_api_key(self, _msg: str) -> dict[str, Any]:
        return {
            "reply": (
                "## 🔑 API Keys কোথায় পাবে?\n\n"
                "তোমার **GitHub Education** account আছে — "
                "এটা দিয়ে অনেক কিছু free পাবে!\n\n"
                "**১. SendGrid (Email পাঠাতে)**\n"
                "→ sendgrid.com → Sign up (free)\n"
                "→ Free tier: **100 email/day** বিনামূল্যে\n"
                "→ Settings → API Keys → Create Key\n"
                "→ `config/api_keys.env` ফাইলে রাখো:\n"
                "  `SENDGRID_API_KEY=SG.xxxxxxxx`\n\n"
                "**২. Google Places (Lead Research)**\n"
                "→ console.cloud.google.com\n"
                "→ New Project → Enable Places API\n"
                "→ Credentials → API Key\n"
                "→ Free: $200 credit/month\n\n"
                "**৩. OpenAI (Optional)**\n"
                "→ platform.openai.com\n"
                "→ GitHub Education-এ ফ্রি credit পেতে পারো\n\n"
                "**⚠️ API Key ছাড়াও চলবে:**\n"
                "Research-এ _Skip scraping_ ON করো।\n"
                "Email-এ Gmail manually করো।\n\n"
                "**Key কোথায় রাখবে:**\n"
                "Replit → 🔒 Secrets (বেশি secure)\n"
                "বা `config/api_keys.env` ফাইলে"
            ),
            "quick_actions": [
                {"label": "📧 Outreach শুরু করো", "msg": "কিভাবে email পাঠাব?"},
                {"label": "🔍 API ছাড়া Research", "msg": "কিভাবে research করব?"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    def _handle_followup(self, _msg: str) -> dict[str, Any]:
        stats = self.ctx.get_leads_stats()
        return {
            "reply": (
                "## 🔄 Follow-up কিভাবে করবে?\n\n"
                f"তোমার **{stats['contacted']}** জনকে email পাঠানো হয়েছে।\n"
                f"**{stats['replied']}** জন reply করেছে।\n\n"
                "**Follow-up Schedule:**\n"
                "- **3 দিন পর** → 1st follow-up\n"
                "- **7 দিন পর** → 2nd follow-up\n"
                "- **14 দিন পর** → 3rd follow-up (শেষ)\n\n"
                "**Outreach Tool-এ:**\n"
                "→ Campaign = _Follow-up_\n"
                "→ বাকিটা same\n\n"
                "**কেউ Reply করলে:**\n"
                "1. আগ্রহী হলে → 15 min discovery call offer করো\n"
                "2. Calendly link দাও (free: calendly.com)\n"
                "3. Script:\n"
                "_'ধন্যবাদ reply করার জন্য! আপনার business-এর_\n"
                "_জন্য specific ideas আছে। ১৫ মিনিট কথা বলবেন?'_\n\n"
                "**Unsubscribe করলে:**\n"
                "→ Leads page-এ status = _unsubscribed_ দাও"
            ),
            "quick_actions": [
                {"label": "📧 Follow-up পাঠাও", "msg": "__goto__/outreach"},
                {"label": "👥 Leads আপডেট", "msg": "__goto__/leads"},
            ],
            "tool_link": "/outreach",
            "run_cmd": None,
        }

    def _handle_revenue(self, _msg: str) -> dict[str, Any]:
        rev = self.ctx.get_revenue_progress()
        stats = self.ctx.get_leads_stats()

        month = datetime.now().month
        year_month = min(12, month)
        target_min = target_max = 0
        for m_start, m_end, t_min, t_max in MONTHLY_TARGETS:
            if m_start <= year_month <= m_end:
                target_min, target_max = t_min, t_max
                break

        return {
            "reply": (
                "## 💰 $1,000,000 Revenue Plan\n\n"
                "**Annual Roadmap:**\n"
                "| Period | Monthly Target |\n"
                "|--------|---------------|\n"
                "| মাস ১-৩ | $10,000–$20,000 |\n"
                "| মাস ৪-৬ | $30,000–$50,000 |\n"
                "| মাস ৭-৯ | $60,000–$80,000 |\n"
                "| মাস ১০-১২ | $90,000–$100,000 |\n\n"
                f"**এই মাসের Target:** ${target_min:,}–${target_max:,}\n\n"
                "**Math:**\n"
                f"- Per client avg: **$2,000**\n"
                f"- $1M ÷ $2,000 = **500 clients** দরকার\n"
                f"- প্রতি মাসে **~42 clients** = $1M/year\n\n"
                "**এখনকার Progress:**\n"
                f"- Est. Revenue: **${rev['est_revenue']:,}**\n"
                f"- Clients: **{stats['converted']}**\n"
                f"- Remaining: **${rev['remaining']:,}**\n\n"
                "**কিভাবে পৌঁছাবে:**\n"
                "1. প্রতিদিন **50+ লিড** research\n"
                "2. প্রতিদিন **50-200 email** পাঠাও\n"
                "3. Reply rate **5%** রাখো\n"
                "4. Close rate **10%** মানে weekly **1-2 client**\n\n"
                "_Consistency = $1M_"
            ),
            "quick_actions": [
                {"label": "📊 Progress দেখাও", "msg": "আমার progress?"},
                {"label": "🔍 লিড বাড়াও", "msg": "কিভাবে research করব?"},
                {"label": "📧 Email করো", "msg": "কিভাবে email পাঠাব?"},
            ],
            "tool_link": "/reports",
            "run_cmd": None,
        }

    def _handle_crm(self, _msg: str) -> dict[str, Any]:
        return {
            "reply": (
                "## 🗄️ CRM / Data Management\n\n"
                "**App-এ built-in Lead Manager আছে:**\n"
                "→ `/leads` page-এ সব lead দেখো\n"
                "→ Status filter করো\n"
                "→ Grade filter করো\n\n"
                "**Data কোথায় থাকে:**\n"
                "`tracking/leads.csv` ফাইলে সব lead save হয়\n\n"
                "**Airtable-এ import করতে:**\n"
                "1. airtable.com → New Base\n"
                "2. Import → CSV\n"
                "3. `tracking/leads.csv` upload করো\n"
                "4. Field map করো\n\n"
                "**Lead Status Flow:**\n"
                "`new` → `contacted` → `replied` → `interested` → `converted`\n\n"
                "**Backup:**\n"
                "প্রতি সপ্তাহে `leads.csv` → Google Drive-এ upload করো"
            ),
            "quick_actions": [
                {"label": "👥 Leads দেখো", "msg": "__goto__/leads"},
                {"label": "📊 Report বানাও", "msg": "__goto__/reports"},
            ],
            "tool_link": "/leads",
            "run_cmd": None,
        }

    def _handle_replit(self, _msg: str) -> dict[str, Any]:
        return {
            "reply": (
                "## 🟢 Replit-এ App চালানো\n\n"
                "**ধাপ ১: Replit-এ যাও**\n"
                "→ replit.com → Sign in with GitHub\n\n"
                "**ধাপ ২: Repo Import করো**\n"
                "→ `+ Create Repl`\n"
                "→ `Import from GitHub`\n"
                "→ URL: github.com/Joy123123123/agency-research-automation-1m\n\n"
                "**ধাপ ৩: Flask Install করো**\n"
                "→ Shell tab-এ:\n"
                "```\npip install flask\n```\n\n"
                "**ধাপ ৪: App Run করো**\n"
                "```\npython scripts/web_app.py\n```\n\n"
                "**ধাপ ৫: URL Copy করো**\n"
                "→ Replit একটা URL দেবে (যেমন: `https://xxx.repl.co`)\n"
                "→ এই URL মোবাইল browser-এ খোলো\n\n"
                "**✅ Done! মোবাইলে App চলছে!**\n\n"
                "**API Keys:**\n"
                "→ Replit → 🔒 Secrets → Key/Value দাও"
            ),
            "quick_actions": [
                {"label": "🔑 API Keys কোথায়?", "msg": "API key কোথায় পাব?"},
                {"label": "📱 Termux-এ চালাব", "msg": "Termux-এ কিভাবে চালাব?"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    def _handle_termux(self, _msg: str) -> dict[str, Any]:
        return {
            "reply": (
                "## 📱 Android/Termux-এ App চালানো\n\n"
                "**ধাপ ১: Termux Install করো**\n"
                "→ F-Droid থেকে (Play Store-টা পুরনো)\n"
                "→ f-droid.org → Termux search করো\n\n"
                "**ধাপ ২: Setup করো**\n"
                "```\npkg update && pkg upgrade\npkg install python git\n```\n\n"
                "**ধাপ ৩: Repo Clone করো**\n"
                "```\ngit clone https://github.com/Joy123123123/agency-research-automation-1m.git\ncd agency-research-automation-1m\n```\n\n"
                "**ধাপ ৪: Flask Install করো**\n"
                "```\npip install flask\n```\n\n"
                "**ধাপ ৫: App চালু করো**\n"
                "```\npython scripts/web_app.py\n```\n\n"
                "**ধাপ ৬: Browser-এ খোলো**\n"
                "→ Android browser-এ যাও\n"
                "→ URL: `http://localhost:5000`\n"
                "→ **Done! 🎉**\n\n"
                "**💡 Tip:**\n"
                "Termux background-এ রাখতে: `tmux` বা `nohup` use করো"
            ),
            "quick_actions": [
                {"label": "🟢 Replit use করব", "msg": "Replit-এ কিভাবে চালাব?"},
                {"label": "🔑 API Keys", "msg": "API key কোথায় পাব?"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    def _handle_scoring(self, _msg: str) -> dict[str, Any]:
        return {
            "reply": (
                "## 🎯 Lead Scoring — কোনটা Best?\n\n"
                "**Grade A (Score 80+) → সবচেয়ে ভালো:**\n"
                "- Website নেই ✓\n"
                "- Review count < 30 ✓\n"
                "- Email address আছে ✓\n"
                "- Social media নেই ✓\n\n"
                "**Grade B (Score 60-79) → ভালো:**\n"
                "- কিছু কিছু factor আছে\n"
                "- Still worth contacting\n\n"
                "**Grade C/D → এড়িয়ে যাও:**\n"
                "- বড় established business\n"
                "- ২০০+ reviews\n"
                "- Already strong online presence\n\n"
                "**Strategy:**\n"
                "1. **Grade A** leads-এ সবার আগে email করো\n"
                "2. **Grade B** → 2nd batch\n"
                "3. **Grade C/D** → skip\n\n"
                "**Leads page-এ filter করো:**\n"
                "→ Grade = A → সেগুলোতে focus করো"
            ),
            "quick_actions": [
                {"label": "👥 Grade A দেখাও", "msg": "__goto__/leads"},
                {"label": "📧 Email পাঠাও", "msg": "কিভাবে email পাঠাব?"},
            ],
            "tool_link": "/leads",
            "run_cmd": None,
        }

    def _handle_conversion(self, _msg: str) -> dict[str, Any]:
        stats = self.ctx.get_leads_stats()
        return {
            "reply": (
                "## 🎉 Client Conversion Process\n\n"
                f"**এখন পর্যন্ত: {stats['converted']} জন client!**\n\n"
                "**Conversion Pipeline:**\n"
                "1. **Reply আসে** → interested হয়েছে\n"
                "2. **Discovery Call** → 15 min Zoom/WhatsApp\n"
                "   - তাদের সমস্যা বোঝো\n"
                "   - তোমার solution দেখাও\n"
                "3. **Proposal পাঠাও** → price + plan\n"
                "4. **Follow-up** → 2-3 দিন পর\n"
                "5. **Close!** → Contract sign / payment\n\n"
                "**Pricing Structure:**\n"
                "- Basic (Website): $500-1,000\n"
                "- Standard (Website + SEO): $1,500-2,500\n"
                "- Premium (Full Digital): $3,000-5,000\n"
                "- Retainer (Monthly): $500-2,000/month\n\n"
                "**Convert হলে:**\n"
                "→ Leads page-এ status = `converted` দাও\n"
                "→ Revenue automatically track হবে!"
            ),
            "quick_actions": [
                {"label": "👥 Leads আপডেট করো", "msg": "__goto__/leads"},
                {"label": "💰 Revenue দেখাও", "msg": "আমার revenue progress?"},
            ],
            "tool_link": "/leads",
            "run_cmd": None,
        }

    def _handle_schedule(self, _msg: str) -> dict[str, Any]:
        return {
            "reply": (
                "## ⏰ Daily Schedule — সফলতার রুটিন\n\n"
                "**9:00–10:00 AM → Research**\n"
                "- নতুন 50+ লিড খোঁজো\n"
                "- Inbox চেক করো\n"
                "- Lead list review করো\n\n"
                "**10:00–11:00 AM → Outreach**\n"
                "- Initial email পাঠাও\n"
                "- Follow-up পাঠাও\n"
                "- Daily limit: 50-200 email\n\n"
                "**11:00 AM–12:00 PM → Analytics**\n"
                "- Stats দেখো\n"
                "- SendGrid check করো\n"
                "- Lead status আপডেট করো\n\n"
                "**3:00–4:00 PM → Follow-up**\n"
                "- Reply-দের উত্তর দাও\n"
                "- Discovery call schedule করো\n"
                "- CRM আপডেট করো\n\n"
                "**সাপ্তাহিক (সোমবার):**\n"
                "- Weekly report বানাও\n"
                "- Grade A leads review\n"
                "- নতুন niche research\n"
                "- Data backup\n\n"
                "**💡 সর্বমোট:** মাত্র ~3 ঘন্টা/দিন!"
            ),
            "quick_actions": [
                {"label": "📋 আজকের কাজ", "msg": "আজ কী করব?"},
                {"label": "🔍 Research শুরু", "msg": "__goto__/research"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    def _handle_help(self, _msg: str) -> dict[str, Any]:
        return {
            "reply": (
                "## 🆘 Help — আমি সব জানি!\n\n"
                "**আমাকে যেকোনো কিছু জিজ্ঞেস করো:**\n\n"
                "📋 **Workflow:**\n"
                "- _আজ কী করব?_\n"
                "- _কোনটার পর কোনটা করব?_\n"
                "- _কখন email পাঠাব?_\n\n"
                "🔍 **Research:**\n"
                "- _কিভাবে লিড খুঁজব?_\n"
                "- _কোন niche ভালো?_\n\n"
                "📧 **Outreach:**\n"
                "- _কিভাবে email পাঠাব?_\n"
                "- _Follow-up কখন করব?_\n\n"
                "💰 **Revenue:**\n"
                "- _$1M কিভাবে পৌঁছাব?_\n"
                "- _আমার progress কেমন?_\n\n"
                "🔑 **Setup:**\n"
                "- _API key কোথায় পাব?_\n"
                "- _Replit-এ কিভাবে চালাব?_\n\n"
                "**যেকোনো প্রশ্ন করো — আমি সবসময় আছি!** 🤖"
            ),
            "quick_actions": [
                {"label": "📋 আজকের কাজ", "msg": "আজ কী করব?"},
                {"label": "💰 Revenue Plan", "msg": "$1M revenue কিভাবে?"},
                {"label": "🛠️ Tools", "msg": "কোন tool লাগবে?"},
                {"label": "⏰ Schedule", "msg": "daily schedule কী?"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    def _handle_next_step(self, _msg: str) -> dict[str, Any]:
        """Intelligently determine the next step based on current state."""
        stats = self.ctx.get_leads_stats()
        pending = self.ctx.get_pending_tasks()

        # Smart next-step logic
        if stats["total"] == 0:
            next_action = (
                "🔍 **এখনই Research করো!**\n\n"
                "তোমার কোনো লিড নেই। প্রথম কাজ:\n"
                "→ Research Tool খোলো\n"
                "→ Niche: Restaurant বা Dentist\n"
                "→ Location: Dhaka\n"
                "→ Count: 50\n"
                "→ Run করো!"
            )
            link = "/research"
        elif stats["total"] < 20:
            next_action = (
                f"🔍 **আরো লিড দরকার!**\n\n"
                f"মাত্র {stats['total']}টি লিড আছে। আরো research করো।\n"
                f"Target: কমপক্ষে 100+ লিড"
            )
            link = "/research"
        elif stats["contacted"] == 0:
            next_action = (
                f"📧 **Email পাঠাও!**\n\n"
                f"{stats['total']}টি লিড আছে কিন্তু কাউকে email করা হয়নি!\n"
                f"→ Outreach Tool খোলো → Dry Run করো → Send করো"
            )
            link = "/outreach"
        elif stats["replied"] == 0:
            next_action = (
                f"🔄 **Follow-up করো!**\n\n"
                f"{stats['contacted']}জনকে email করা হয়েছে কিন্তু reply নেই।\n"
                f"Follow-up পাঠাও (3/7/14 দিন পর)"
            )
            link = "/outreach"
        elif stats["converted"] == 0:
            next_action = (
                f"📞 **Reply-দের Call করো!**\n\n"
                f"{stats['replied']}জন reply করেছে!\n"
                f"→ Discovery call offer করো\n"
                f"→ 15 min Zoom/WhatsApp call\n"
                f"→ Proposal পাঠাও"
            )
            link = "/leads"
        else:
            next_action = (
                f"🚀 **Scale করো!**\n\n"
                f"তুমি এখন {stats['converted']}জন client পেয়েছে!\n"
                f"→ আরো লিড research করো\n"
                f"→ নতুন niche try করো\n"
                f"→ Email volume বাড়াও"
            )
            link = "/research"

        if pending:
            next_action += f"\n\n**⏳ আজকের বাকি কাজ:** {pending[0]}"

        return {
            "reply": f"## ⏭️ পরের কাজ কী?\n\n{next_action}",
            "quick_actions": [
                {"label": "▶️ এই কাজ করো", "msg": f"__goto__{link}"},
                {"label": "📊 আমার stats", "msg": "আমার progress?"},
            ],
            "tool_link": link,
            "run_cmd": None,
        }

    def _handle_unknown(self, msg: str) -> dict[str, Any]:
        """Fallback for unrecognized queries."""
        # Try to give a helpful response based on last intent
        last_intent = ""
        for h in reversed(self._history[:-1]):
            if h.get("intent") and h["intent"] != "unknown":
                last_intent = h["intent"]
                break

        suggestions = [
            "আজ কী করব?",
            "কিভাবে লিড খুঁজব?",
            "কিভাবে email পাঠাব?",
            "আমার progress কেমন?",
            "API key কোথায় পাব?",
        ]

        return {
            "reply": (
                "## 🤔 বুঝতে পারিনি!\n\n"
                f"_'{msg[:50]}...'_ — এটা সম্পর্কে আমার কাছে নির্দিষ্ট তথ্য নেই।\n\n"
                "**এগুলো জিজ্ঞেস করে দেখো:**\n"
                + "\n".join(f"- _{s}_" for s in suggestions)
                + "\n\nঅথবা নিচের বাটন চাপো।"
            ),
            "quick_actions": [
                {"label": "📋 আজকের কাজ", "msg": "আজ কী করব?"},
                {"label": "💰 Revenue Plan", "msg": "$1M revenue কিভাবে?"},
                {"label": "🆘 সব Help", "msg": "help"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    # ── Advanced handlers ─────────────────────────────────────────────────────

    def _handle_market(self, msg: str) -> dict[str, Any]:
        """Market intelligence — US/Europe/Canada breakdown."""
        msg_lower = msg.lower()
        if "canada" in msg_lower or "কানাডা" in msg_lower:
            focus = "Canada"
        elif "uk" in msg_lower or "england" in msg_lower or "britain" in msg_lower:
            focus = "UK"
        elif "europe" in msg_lower or "ইউরোপ" in msg_lower:
            focus = "Europe"
        elif "australia" in msg_lower or "অস্ট্রেলিয়া" in msg_lower:
            focus = "Australia"
        else:
            focus = "USA"

        rows = []
        for mkt, data in MarketIntelligence.MARKETS.items():
            top = MarketIntelligence.get_top_niches(mkt, top_n=3)
            niche_names = ", ".join(n["label"] for n in top)
            star = " ⭐" if mkt == focus else ""
            rows.append(
                f"| {data['flag']} **{mkt}**{star} "
                f"| {niche_names} "
                f"| {data['avg_response_rate']} "
                f"| {data['send_time']} |"
            )

        focus_data = MarketIntelligence.MARKETS[focus]
        top_niches = MarketIntelligence.get_top_niches(focus, top_n=3)

        niche_details = "\n".join(
            f"**{i + 1}. {n['label']}** (ROI: {n['roi_score']}/100)\n"
            f"   → Avg deal: ${n['avg_deal']:,} | Close: {n['close_days']} days\n"
            f"   → Why: {n['why']}"
            for i, n in enumerate(top_niches)
        )

        return {
            "reply": (
                f"## 🌍 Market Intelligence\n\n"
                f"**তোমার primary market: {focus_data['flag']} {focus}**\n\n"
                f"| Market | Best Niches | Reply Rate | Best Send Time |\n"
                f"|--------|-------------|-----------|---------------|\n"
                + "\n".join(rows)
                + f"\n\n---\n\n"
                f"## {focus_data['flag']} {focus} — Top 3 Niches:\n\n"
                + niche_details
                + f"\n\n**Best cities to target:**\n"
                + ", ".join(focus_data["best_cities"][:6])
                + f"\n\n**Send time:** {focus_data['send_time']}"
            ),
            "quick_actions": [
                {"label": "🇺🇸 USA Details", "msg": "USA market কেমন?"},
                {"label": "🇨🇦 Canada Details", "msg": "Canada market কেমন?"},
                {"label": "🎯 Best Niche বেছে দাও", "msg": "কোন niche সেরা?"},
                {"label": "🔍 Research শুরু", "msg": "__goto__/research"},
            ],
            "tool_link": "/research",
            "run_cmd": None,
        }

    def _handle_niche_advice(self, msg: str) -> dict[str, Any]:
        """AI-powered niche recommendation with ROI ranking."""
        market = "USA"
        for h in self._history:
            txt = h.get("content", "").lower()
            if "canada" in txt or "কানাডা" in txt:
                market = "Canada"
                break
            if "uk" in txt or "england" in txt:
                market = "UK"
                break

        top5 = MarketIntelligence.get_top_niches(market, top_n=5)
        mkt = MarketIntelligence.MARKETS[market]

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        rows = []
        for i, n in enumerate(top5):
            competition_bar = "🔴" * n["competition"] + "⚪" * (5 - n["competition"])
            rows.append(
                f"| {medals[i]} {n['label']} "
                f"| ${n['avg_deal']:,} "
                f"| {n['close_days']} days "
                f"| {n['roi_score']}/100 "
                f"| {competition_bar} |"
            )

        best = top5[0]
        return {
            "reply": (
                f"## 🎯 AI Niche Recommendation — {mkt['flag']} {market}\n\n"
                f"**#1 সুপারিশ: {best['label']}** (ROI Score: {best['roi_score']}/100)\n\n"
                f"> {best['why']}\n\n"
                f"**Email angle:** _{best['email_angle']}_\n\n"
                f"---\n\n"
                f"**Top 5 Niches Ranked:**\n\n"
                f"| Rank | Niche | Deal Size | Close Speed | ROI | Competition |\n"
                f"|------|-------|-----------|-------------|-----|-------------|\n"
                + "\n".join(rows)
                + f"\n\n**💡 Strategy:** শুরু করো {best['label']} দিয়ে।\n"
                f"প্রতিদিন 50 লিড → 5% reply → "
                f"${int(50 * 0.05 * best['avg_deal']):,}/week potential"
            ),
            "quick_actions": [
                {"label": f"🔍 Research শুরু", "msg": "__goto__/research"},
                {"label": "🌍 Market দেখাও", "msg": "market intelligence দেখাও"},
                {"label": "📈 Strategy দাও", "msg": "আমার জন্য best strategy কী?"},
            ],
            "tool_link": "/research",
            "run_cmd": None,
        }

    def _handle_strategy(self, _msg: str) -> dict[str, Any]:
        """CEO-level strategic recommendation based on current pipeline."""
        stats = self.ctx.get_leads_stats()
        rev = self.ctx.get_revenue_progress()
        rec = BusinessStrategist.recommend(stats, rev, market="USA")

        total = stats.get("total", 0)
        contacted = stats.get("contacted", 0)
        replied = stats.get("replied", 0)
        converted = stats.get("converted", 0)
        reply_rate = round((replied / max(contacted, 1)) * 100, 1)
        close_rate = round((converted / max(replied, 1)) * 100, 1)

        funnel = (
            "**Pipeline Funnel:**\n"
            "```\n"
            f"Leads:     {total:>6}\n"
            f"Contacted: {contacted:>6}  ({round(contacted / max(total, 1) * 100)}%)\n"
            f"Replied:   {replied:>6}  ({reply_rate}%)\n"
            f"Converted: {converted:>6}  ({close_rate}%)\n"
            f"Revenue:   ${rev['est_revenue']:>6,}\n"
            "```\n"
        )

        best_niche = MarketIntelligence.get_niche(rec["niche"])
        niche_label = best_niche["label"] if best_niche else rec["niche"]

        return {
            "reply": (
                "## 🧠 AI Strategic Analysis\n\n"
                + funnel
                + "\n---\n\n"
                "## 🎯 #1 Priority Action:\n\n"
                f"### {rec['action']}\n\n"
                f"**কেন এটা করব:** {rec['reason']}\n\n"
                f"**কী হবে:** {rec['expected_result']}\n\n"
                f"**Quick Win:** {rec['quick_win']}\n\n"
                "---\n\n"
                f"**Best Niche এখন:** {niche_label}\n"
                f"**Target Market:** {rec['market']}\n\n"
                "_এই একটা কাজ করো — বাকি সব পরে।_"
            ),
            "quick_actions": [
                {
                    "label": "▶️ এখনই করো",
                    "msg": f"__goto__{rec.get('run_tool', '/')}",
                },
                {"label": "🎯 Best Niche", "msg": "কোন niche সেরা?"},
                {"label": "🌍 Market Intel", "msg": "market intelligence দেখাও"},
                {"label": "📊 Progress", "msg": "আমার progress?"},
            ],
            "tool_link": rec.get("run_tool"),
            "run_cmd": None,
        }

    def _handle_always_on(self, _msg: str) -> dict[str, Any]:
        """Guide for keeping the app always running."""
        return {
            "reply": (
                "## 🔄 App সবসময় Running রাখার উপায়\n\n"
                "ফোন lock হলেও চলবে — এই ৩টি উপায়:\n\n"
                "---\n\n"
                "## ✅ উপায় ১: Replit Always-On (সহজ)\n\n"
                "**GitHub Education দিয়ে FREE পাবে!**\n\n"
                "**ধাপ ১:** replit.com → তোমার Repl খোলো\n\n"
                "**ধাপ ২:** `Deployments` tab ক্লিক করো\n\n"
                "**ধাপ ৩:** `Reserved VM` বা `Always On` enable করো\n"
                "→ GitHub Education = Replit Hacker plan free!\n\n"
                "**ধাপ ৪:** Deploy করো → ২৪/৭ চলবে!\n\n"
                "---\n\n"
                "## ✅ উপায় ২: UptimeRobot (Ping করে জাগিয়ে রাখে)\n\n"
                "**ধাপ ১:** uptimerobot.com → Free account\n\n"
                "**ধাপ ২:** `Add New Monitor`\n"
                "→ Type: HTTP(s)\n"
                "→ URL: তোমার Replit URL\n"
                "→ Interval: 5 minutes\n\n"
                "**ধাপ ৩:** Save → App কখনো sleep যাবে না!\n\n"
                "---\n\n"
                "## ✅ উপায় ৩: Termux:Boot (Android)\n\n"
                "**ধাপ ১:** F-Droid থেকে `Termux:Boot` install করো\n\n"
                "**ধাপ ২:** Boot script তৈরি করো:\n"
                "```\nmkdir -p ~/.termux/boot\n"
                "cat > ~/.termux/boot/start-app.sh << 'EOF'\n"
                "#!/data/data/com.termux/files/usr/bin/sh\n"
                "cd ~/agency-research-automation-1m\n"
                "python scripts/web_app.py &\n"
                "EOF\n"
                "chmod +x ~/.termux/boot/start-app.sh\n```\n\n"
                "**ধাপ ৩:** ফোন restart → App auto-start!\n\n"
                "---\n\n"
                "**💡 Best Choice:**\n"
                "**Replit + UptimeRobot** = সবচেয়ে reliable, সব free!\n"
                "GitHub Education account দিয়ে Replit Hacker plan পাবে।"
            ),
            "quick_actions": [
                {"label": "🟢 Replit Setup", "msg": "Replit-এ কিভাবে চালাব?"},
                {"label": "📱 Termux Setup", "msg": "Termux-এ কিভাবে চালাব?"},
                {"label": "🔑 GitHub Education", "msg": "API key কোথায় পাব?"},
            ],
            "tool_link": None,
            "run_cmd": None,
        }

    # ── Public: recommendation API (called from web routes) ───────────────────

    def get_strategy_recommendation(self, market: str = "USA") -> dict[str, Any]:
        """
        Return a full strategic recommendation for the /api/ai/recommend endpoint.

        Combines pipeline analysis + market intel + niche advice into one response.
        """
        stats = self.ctx.get_leads_stats()
        rev = self.ctx.get_revenue_progress()
        rec = BusinessStrategist.recommend(stats, rev, market=market)
        top_niches = MarketIntelligence.get_top_niches(market, top_n=3)
        mkt = MarketIntelligence.MARKETS.get(market, MarketIntelligence.MARKETS["USA"])

        return {
            "market": market,
            "market_flag": mkt["flag"],
            "recommendation": rec,
            "top_niches": [
                {
                    "name": n["name"],
                    "label": n["label"],
                    "roi_score": n["roi_score"],
                    "avg_deal": n["avg_deal"],
                    "close_days": n["close_days"],
                    "why": n["why"],
                    "email_angle": n["email_angle"],
                }
                for n in top_niches
            ],
            "pipeline": {
                "total": stats.get("total", 0),
                "contacted": stats.get("contacted", 0),
                "replied": stats.get("replied", 0),
                "converted": stats.get("converted", 0),
                "est_revenue": rev.get("est_revenue", 0),
                "goal_pct": rev.get("pct", 0),
            },
            "best_cities": mkt["best_cities"][:6],
            "send_time": mkt["send_time"],
        }
