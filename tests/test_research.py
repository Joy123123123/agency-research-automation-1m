"""
Tests for Research Modules
"""
import pytest
from unittest.mock import MagicMock, patch
from src.research.agency_finder import Agency, AgencyFinder
from src.research.market_analyzer import MarketAnalyzer
from src.ai.lead_scorer import LeadScorer


class TestAgency:
    def test_agency_creation(self):
        agency = Agency(name="Test Restaurant", niche="restaurant", location="Dhaka")
        assert agency.name == "Test Restaurant"
        assert agency.niche == "restaurant"
        assert agency.status == "new"

    def test_agency_to_dict(self):
        agency = Agency(name="Test", niche="restaurant", location="Dhaka", email="test@test.com")
        d = agency.to_dict()
        assert d["name"] == "Test"
        assert d["email"] == "test@test.com"


class TestMarketAnalyzer:
    def setup_method(self):
        self.analyzer = MarketAnalyzer()

    def test_analyze_empty_niche(self):
        insight = self.analyzer.analyze_niche("restaurant", "Dhaka", [])
        assert insight.total_businesses == 0
        assert insight.opportunity_score == 0

    def test_analyze_with_agencies(self):
        agencies = [
            Agency("A", "restaurant", "Dhaka", has_website=False, google_rating=3.5, review_count=20),
            Agency("B", "restaurant", "Dhaka", has_website=True, google_rating=4.0, review_count=50),
            Agency("C", "restaurant", "Dhaka", has_website=False, google_rating=4.2, review_count=15),
        ]
        insight = self.analyzer.analyze_niche("restaurant", "Dhaka", agencies)
        assert insight.total_businesses == 3
        assert insight.opportunity_score > 0
        assert insight.recommended_service in ("website", "seo", "google_ads")

    def test_rank_opportunities(self):
        from src.research.market_analyzer import MarketInsight
        insights = [
            MarketInsight("restaurant", "Dhaka", 10, 3.5, 60.0, 70.0, "website", 5000),
            MarketInsight("dentist", "Dhaka", 5, 4.0, 30.0, 40.0, "seo", 2000),
            MarketInsight("lawyer", "Dhaka", 8, 3.8, 50.0, 90.0, "seo", 8000),
        ]
        ranked = self.analyzer.rank_opportunities(insights)
        assert ranked[0].opportunity_score >= ranked[1].opportunity_score


class TestLeadScorer:
    def setup_method(self):
        self.scorer = LeadScorer()

    def test_score_no_website(self):
        lead = {"name": "Test", "has_website": False, "google_rating": 4.0, "review_count": 15}
        scored = self.scorer.score_lead(lead)
        assert scored.score > 50  # Should score above baseline

    def test_score_with_email(self):
        lead = {"name": "Test", "has_website": False, "email": "test@test.com", "review_count": 10}
        scored = self.scorer.score_lead(lead)
        assert scored.score > 70

    def test_score_unsubscribed(self):
        lead = {"name": "Test", "unsubscribed": True}
        scored = self.scorer.score_lead(lead)
        assert scored.score == 0

    def test_grade_assignment(self):
        lead_a = {"name": "A", "has_website": False, "email": "a@a.com", "review_count": 5}
        lead_d = {"name": "D", "unsubscribed": True}
        assert self.scorer.score_lead(lead_a).grade in ("A", "B")
        assert self.scorer.score_lead(lead_d).grade == "D"

    def test_bulk_scoring_sorted(self):
        leads = [
            {"name": "Low", "review_count": 500, "has_website": True},
            {"name": "High", "has_website": False, "email": "h@h.com", "review_count": 5},
        ]
        scored = self.scorer.score_bulk(leads)
        assert scored[0].score >= scored[1].score

    def test_filter_high_priority(self):
        leads = [
            {"name": "High", "has_website": False, "email": "h@h.com", "review_count": 5},
            {"name": "Low", "unsubscribed": True},
        ]
        scored = self.scorer.score_bulk(leads)
        high = self.scorer.filter_high_priority(scored)
        assert all(s.priority in ("high", "medium") for s in high)
