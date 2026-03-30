"""
Lead Scorer Module
AI-powered lead scoring and prioritization
Owner: Md Jamil Islam
"""
import logging
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScoredLead:
    lead: Dict
    score: float
    grade: str  # A, B, C, D
    priority: str  # high, medium, low
    reason: str


class LeadScorer:
    """
    Scores and prioritizes leads based on multiple factors.
    Uses rule-based scoring (upgradeable to ML model).
    """

    def score_lead(self, lead: Dict) -> ScoredLead:
        """Score a single lead from 0-100."""
        score = 50.0
        reasons = []

        # --- Positive factors ---
        if not lead.get("has_website"):
            score += 20
            reasons.append("no website")

        if lead.get("email"):
            score += 10
            reasons.append("has email")

        review_count = lead.get("review_count", 0) or 0
        if review_count < 30:
            score += 10
            reasons.append("small business")
        elif review_count > 200:
            score -= 15
            reasons.append("established (harder to convert)")

        rating = lead.get("google_rating") or 0
        if 3.0 <= rating <= 4.2:
            score += 5
            reasons.append("needs reputation boost")

        if lead.get("phone"):
            score += 3

        if not lead.get("has_social_media"):
            score += 7
            reasons.append("no social media")

        # --- Negative factors ---
        if lead.get("status") == "contacted":
            score -= 30

        if lead.get("unsubscribed"):
            score = 0

        score = min(100, max(0, score))

        # Determine grade
        if score >= 80:
            grade, priority = "A", "high"
        elif score >= 60:
            grade, priority = "B", "medium"
        elif score >= 40:
            grade, priority = "C", "low"
        else:
            grade, priority = "D", "skip"

        return ScoredLead(
            lead=lead,
            score=round(score, 1),
            grade=grade,
            priority=priority,
            reason=", ".join(reasons) if reasons else "standard lead"
        )

    def score_bulk(self, leads: List[Dict]) -> List[ScoredLead]:
        """Score and sort a list of leads."""
        scored = [self.score_lead(lead) for lead in leads]
        scored.sort(key=lambda x: x.score, reverse=True)
        logger.info(
            f"Scored {len(scored)} leads: "
            f"{sum(1 for s in scored if s.grade == 'A')} A-grade, "
            f"{sum(1 for s in scored if s.grade == 'B')} B-grade"
        )
        return scored

    def filter_high_priority(self, scored_leads: List[ScoredLead]) -> List[ScoredLead]:
        """Return only high and medium priority leads."""
        return [s for s in scored_leads if s.priority in ("high", "medium")]
