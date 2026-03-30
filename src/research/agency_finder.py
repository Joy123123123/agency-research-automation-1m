"""
Agency Finder Module
Discovers target agencies/businesses for outreach
Owner: Md Jamil Islam
"""
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Agency:
    """Represents a potential agency/business lead."""
    name: str
    niche: str
    location: str
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    google_rating: Optional[float] = None
    review_count: Optional[int] = None
    has_website: bool = False
    has_social_media: bool = False
    lead_score: Optional[float] = None
    status: str = "new"

    def to_dict(self) -> Dict:
        return asdict(self)


class AgencyFinder:
    """
    Finds and discovers agencies/businesses for research.
    Uses Google Maps, Yellow Pages, and other sources.
    """

    def __init__(self, api_key: str = "", delay: float = 2.0):
        self.api_key = api_key
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

    def find_by_google_maps(
        self,
        niche: str,
        location: str,
        max_results: int = 50
    ) -> List[Agency]:
        """Find businesses via Google Maps API."""
        agencies = []

        if not self.api_key:
            logger.warning("No Google API key set. Using fallback method.")
            return self._find_fallback(niche, location, max_results)

        base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        query = f"{niche} in {location}"
        next_page_token = None

        while len(agencies) < max_results:
            params = {
                "query": query,
                "key": self.api_key,
            }
            if next_page_token:
                params["pagetoken"] = next_page_token

            try:
                response = self.session.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                for place in data.get("results", []):
                    agency = Agency(
                        name=place.get("name", ""),
                        niche=niche,
                        location=location,
                        address=place.get("formatted_address", ""),
                        google_rating=place.get("rating"),
                        review_count=place.get("user_ratings_total"),
                        has_website="website" in place,
                    )
                    agencies.append(agency)

                    if len(agencies) >= max_results:
                        break

                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break

                time.sleep(2)  # Required by Google API

            except requests.RequestException as e:
                logger.error(f"Google Maps API error: {e}")
                break

        logger.info(f"Found {len(agencies)} agencies for '{niche}' in '{location}'")
        return agencies

    def _find_fallback(
        self,
        niche: str,
        location: str,
        max_results: int = 20
    ) -> List[Agency]:
        """Fallback method using public business directories."""
        agencies = []
        logger.info(f"Using fallback search for '{niche}' in '{location}'")

        # Example: Yellow Pages Bangladesh or similar
        url = f"https://www.yellowpages.com.bd/search/{niche}/{location}"

        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")

            for listing in soup.select(".business-listing")[:max_results]:
                name_el = listing.select_one(".business-name")
                phone_el = listing.select_one(".business-phone")
                address_el = listing.select_one(".business-address")

                if name_el:
                    agency = Agency(
                        name=name_el.get_text(strip=True),
                        niche=niche,
                        location=location,
                        phone=phone_el.get_text(strip=True) if phone_el else None,
                        address=address_el.get_text(strip=True) if address_el else None,
                    )
                    agencies.append(agency)

            time.sleep(self.delay)

        except Exception as e:
            logger.error(f"Fallback search error: {e}")

        return agencies

    def filter_by_criteria(
        self,
        agencies: List[Agency],
        min_rating: float = 3.5,
        max_reviews: int = 100,
        needs_website: bool = True
    ) -> List[Agency]:
        """
        Filter agencies by quality criteria.
        Best leads: decent rating, not too many reviews (smaller businesses), needs website.
        """
        filtered = []
        for agency in agencies:
            if needs_website and agency.has_website:
                continue
            if agency.google_rating and agency.google_rating < min_rating:
                continue
            if agency.review_count and agency.review_count > max_reviews:
                continue
            filtered.append(agency)

        logger.info(f"Filtered to {len(filtered)} quality leads from {len(agencies)} total")
        return filtered
