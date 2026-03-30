#!/usr/bin/env python3
"""
Main Research Runner Script
Runs agency research for given niche and location
Usage: python scripts/run_research.py --niche restaurant --location Dhaka --count 50
Owner: Md Jamil Islam
"""
import sys
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.agency_finder import AgencyFinder
from src.research.contact_scraper import ContactScraper
from src.research.market_analyzer import MarketAnalyzer
from src.ai.lead_scorer import LeadScorer
from config.settings import (
    GOOGLE_API_KEY, RESEARCH_DELAY_SECONDS,
    MAX_LEADS_PER_DAY, TRACKING_DIR, LOG_LEVEL
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/research.log", mode="a"),
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Agency Research Runner")
    parser.add_argument("--niche", default="restaurant", help="Business niche to research")
    parser.add_argument("--location", default="Dhaka", help="Location to search in")
    parser.add_argument("--count", type=int, default=50, help="Max leads to find")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip website scraping")
    parser.add_argument("--output", default=None, help="Output CSV filename")
    args = parser.parse_args()

    logger.info(f"Starting research: niche='{args.niche}', location='{args.location}', count={args.count}")

    # 1. Find agencies
    finder = AgencyFinder(api_key=GOOGLE_API_KEY, delay=RESEARCH_DELAY_SECONDS)
    agencies = finder.find_by_google_maps(args.niche, args.location, args.count)

    if not agencies:
        logger.warning("No agencies found. Exiting.")
        return

    # 2. Filter by quality criteria
    agencies = finder.filter_by_criteria(agencies, min_rating=3.0, needs_website=False)
    logger.info(f"{len(agencies)} agencies after quality filter")

    # 3. Score leads
    scorer = LeadScorer()
    leads_dicts = [a.to_dict() for a in agencies]
    scored_leads = scorer.score_bulk(leads_dicts)
    high_priority = scorer.filter_high_priority(scored_leads)
    logger.info(f"{len(high_priority)} high-priority leads identified")

    # 4. Scrape contact info (optional)
    if not args.skip_scrape:
        scraper = ContactScraper(delay=RESEARCH_DELAY_SECONDS)
        for sl in high_priority:
            website = sl.lead.get("website")
            if website:
                contact = scraper.scrape_website(website)
                if contact.get("emails"):
                    sl.lead["email"] = contact["emails"][0]

    # 5. Analyze market
    analyzer = MarketAnalyzer()
    insight = analyzer.analyze_niche(args.niche, args.location, agencies)
    logger.info(
        f"Market insight: opportunity_score={insight.opportunity_score}, "
        f"recommended_service={insight.recommended_service}"
    )

    # 6. Save to CSV
    Path("logs").mkdir(exist_ok=True)
    TRACKING_DIR.mkdir(exist_ok=True)
    output_file = args.output or str(TRACKING_DIR / "leads.csv")

    fieldnames = list(high_priority[0].lead.keys()) + ["lead_score", "grade", "priority"]
    rows = []
    for sl in high_priority:
        row = sl.lead.copy()
        row["lead_score"] = sl.score
        row["grade"] = sl.grade
        row["priority"] = sl.priority
        row["created_at"] = datetime.now().isoformat()
        rows.append(row)

    # Append to existing CSV or create new
    file_exists = Path(output_file).exists()
    with open(output_file, "a" if file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Saved {len(rows)} leads to {output_file}")
    print(f"\n✅ Research complete!")
    print(f"   Found: {len(agencies)} agencies")
    print(f"   High priority: {len(high_priority)} leads")
    print(f"   Saved to: {output_file}")
    print(f"   Recommended service: {insight.recommended_service}")
    print(f"   Est. monthly revenue: ${insight.estimated_revenue:,.0f}")


if __name__ == "__main__":
    main()
