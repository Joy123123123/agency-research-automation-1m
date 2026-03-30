"""
Market Analyzer Module
Analyzes market opportunities and scores leads
Owner: Md Jamil Islam
"""
import logging
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MarketInsight:
    niche: str
    location: str
    total_businesses: int
    avg_rating: float
    without_website_pct: float
    opportunity_score: float
    recommended_service: str
    estimated_revenue: float


class MarketAnalyzer:
    """
    Analyzes the market to identify the best opportunities.
    """

    # Service pricing (USD/month)
    SERVICE_PRICES = {
        "website": 3000,
        "seo": 1500,
        "social_media": 1000,
        "google_ads": 2000,
        "content_marketing": 1200,
    }

    # Niche-to-service mapping
    NICHE_SERVICES = {
        "restaurant": ["website", "social_media", "google_ads"],
        "dentist": ["website", "seo", "google_ads"],
        "lawyer": ["website", "seo", "content_marketing"],
        "real estate": ["website", "seo", "google_ads"],
        "gym": ["website", "social_media", "google_ads"],
        "salon": ["website", "social_media"],
        "hotel": ["website", "seo", "google_ads"],
        "pharmacy": ["website", "google_ads"],
    }

    def analyze_niche(
        self,
        niche: str,
        location: str,
        agencies: List
    ) -> MarketInsight:
        """Analyze a niche/location for business opportunity."""
        total = len(agencies)
        if total == 0:
            return MarketInsight(
                niche=niche, location=location, total_businesses=0,
                avg_rating=0, without_website_pct=0, opportunity_score=0,
                recommended_service="website", estimated_revenue=0
            )

        avg_rating = sum(
            a.google_rating for a in agencies if a.google_rating
        ) / max(sum(1 for a in agencies if a.google_rating), 1)

        without_website = sum(1 for a in agencies if not a.has_website)
        without_website_pct = (without_website / total) * 100

        # Opportunity score: higher if more businesses lack website/SEO
        opportunity_score = min(100, (without_website_pct * 0.6) + (10 - avg_rating) * 4)

        # Recommend best service
        recommended_service = "website"
        if without_website_pct > 50:
            recommended_service = "website"
        elif avg_rating < 3.5:
            recommended_service = "google_ads"
        else:
            recommended_service = "seo"

        # Estimate monthly revenue from this niche
        potential_clients = without_website * 0.05  # 5% conversion
        price = self.SERVICE_PRICES.get(recommended_service, 1000)
        estimated_revenue = potential_clients * price

        insight = MarketInsight(
            niche=niche,
            location=location,
            total_businesses=total,
            avg_rating=round(avg_rating, 2),
            without_website_pct=round(without_website_pct, 1),
            opportunity_score=round(opportunity_score, 1),
            recommended_service=recommended_service,
            estimated_revenue=round(estimated_revenue, 2),
        )

        logger.info(
            f"Market insight for {niche} in {location}: "
            f"score={insight.opportunity_score}, "
            f"est. revenue=${insight.estimated_revenue}"
        )
        return insight

    def rank_opportunities(self, insights: List[MarketInsight]) -> List[MarketInsight]:
        """Rank market insights by opportunity score."""
        return sorted(insights, key=lambda x: x.opportunity_score, reverse=True)

    def calculate_lead_score(self, agency) -> float:
        """
        Score a lead from 0-100.
        Higher score = better prospect.
        """
        score = 50.0  # base score

        # Has no website = better opportunity for us
        if not agency.has_website:
            score += 20

        # Lower review count = smaller business, easier to convert
        if agency.review_count:
            if agency.review_count < 20:
                score += 15
            elif agency.review_count < 50:
                score += 10
            elif agency.review_count > 200:
                score -= 10

        # Good rating but not perfect = has room to grow
        if agency.google_rating:
            if 3.5 <= agency.google_rating <= 4.2:
                score += 10
            elif agency.google_rating < 3.5:
                score += 5

        # Has email contact = easier outreach
        if agency.email:
            score += 5

        return min(100, max(0, score))
