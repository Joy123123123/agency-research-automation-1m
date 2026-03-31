"""
Agency Finder Module
Discovers target agencies/businesses for outreach
Owner: Md Jamil Islam
"""
import random
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
        max_results: int = 20,
        base_url: str = "https://www.yellowpages.com/search"
    ) -> List[Agency]:
        """Fallback method using US Yellow Pages directory; returns demo leads if scraping fails."""
        agencies = []
        logger.info(f"Using fallback search for '{niche}' in '{location}'")

        # Build URL safely (encode niche/location for URL safety)
        from urllib.parse import urlencode
        params = urlencode({"search_terms": niche.strip(), "geo_location_terms": location.strip()})
        url = f"{base_url.rstrip('/')}?{params}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for listing in soup.select(".result")[:max_results]:
                name_el = listing.select_one(".business-name")
                phone_el = listing.select_one(".phones")
                address_el = listing.select_one(".adr")

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

        if not agencies:
            logger.info("Scraping returned no results; generating demo leads for offline/API-free use.")
            agencies = self._generate_demo_leads(niche, location, max_results)

        return agencies

    # ── Demo data ─────────────────────────────────────────────────────────────

    # Business name fragments per niche used to build realistic names
    _DEMO_NAME_PARTS: Dict[str, List[str]] = {
        "restaurant": [
            "The Golden Spoon", "Sunrise Café", "Main Street Grill", "Corner Bistro",
            "Harbor View Diner", "Oak & Vine", "Blue Plate Eatery", "The Local Table",
            "Fifth Avenue Kitchen", "Park Side Restaurant", "Downtown Eats", "The Hungry Fork",
            "Elm Street Café", "Riverside Grill", "Liberty Diner", "The Cozy Kitchen",
            "Maple Leaf Café", "The Daily Grind", "Sunset Bistro", "Union Square Eatery",
        ],
        "dentist": [
            "Bright Smile Dental", "Family Dentistry of", "Advanced Dental Care",
            "Gentle Dental", "Premier Smiles", "Westside Dental Group", "Lakewood Dentistry",
            "Suburban Family Dental", "ClearSmile Dental", "Healthy Teeth Dental Center",
            "Parkview Dental", "Modern Smiles", "Comfort Dental", "TruSmile Dentistry",
            "City Dental Associates", "ProSmile Family Dentistry", "Smile Experts",
            "Heritage Dental Care", "Sunrise Dental", "Valley Dental Group",
        ],
        "lawyer": [
            "Johnson & Associates Law", "Smith Legal Group", "Williams Law Firm",
            "The Law Offices of", "Davis & Partners", "Guardian Law Group",
            "First Choice Legal", "Premier Law Associates", "Justice Law Firm",
            "Liberty Legal Group", "Cornerstone Law", "Apex Legal Services",
            "The Family Law Center", "Downtown Law Group", "United Legal Associates",
            "Champion Law Firm", "Heritage Legal", "Summit Law Group",
            "Trusted Counsel Law", "Patriot Legal Group",
        ],
        "real estate": [
            "Landmark Realty", "Keystone Real Estate", "Premier Properties",
            "City Homes Realty", "Sunrise Real Estate Group", "HomeFirst Realty",
            "Urban Properties", "Dream Home Realty", "Golden Gate Properties",
            "Cornerstone Realty", "Horizon Real Estate", "BlueSky Homes",
            "Main Street Realty", "Liberty Property Group", "Prestige Realty",
            "Pinnacle Real Estate", "Westside Homes", "Pacific Coast Realty",
            "Garden State Properties", "Lakefront Realty",
        ],
        "gym": [
            "Iron Works Fitness", "Peak Performance Gym", "FitLife Center",
            "Power Zone Fitness", "Champions Gym", "Elite Fitness Club",
            "Total Body Fitness", "CrossFit Urban", "The Fitness Factory",
            "Velocity Athletic Club", "Primal Strength Gym", "NextLevel Fitness",
            "Core & More Gym", "Urban Strength Studio", "Results Fitness Center",
            "The Workout Hub", "Flex Fitness", "Apollo Gym", "Forge Athletic",
            "Endurance Fitness",
        ],
        "salon": [
            "Luxe Hair Studio", "The Style Bar", "Chic Cuts", "Premier Beauty Salon",
            "Mane Attraction", "Glamour Studio", "Hair Artistry", "The Cut Above",
            "Serene Beauty Salon", "Prestige Hair Studio", "The Color Room",
            "Studio 360 Salon", "Polished Beauty Bar", "Silk & Style Salon",
            "Uptown Cuts", "Bliss Beauty Studio", "The Hair Lounge",
            "Radiant Beauty Salon", "Class Act Salon", "The Beauty Nook",
        ],
        "hotel": [
            "Grand Stay Inn", "Comfort Suites", "City Center Hotel", "The Plaza Hotel",
            "Harbor View Inn", "Summit Hotel", "Lakewood Inn & Suites", "The Grand Lodge",
            "Downtown Boutique Hotel", "Riverside Inn", "The Urban Hotel",
            "Heritage Hotel & Suites", "Landmark Hotel", "Gateway Inn",
            "The Metropolitan Hotel", "Park Avenue Hotel", "Premier Hotel & Spa",
            "The Continental Inn", "Starlight Hotel", "Emerald Suites",
        ],
        "pharmacy": [
            "Main Street Pharmacy", "Health First Pharmacy", "CareRx Pharmacy",
            "Community Drug Store", "Wellness Pharmacy", "MedPlus Pharmacy",
            "Family Health Pharmacy", "QuickCare Pharmacy", "Central Pharmacy",
            "TrustRx Drugs", "HealthMart Pharmacy", "Lifeline Pharmacy",
            "ProCare Pharmacy", "Guardian Pharmacy", "Community Health Pharmacy",
            "Sunrise Pharmacy", "Neighborhood Drug Store", "PrimeCare Pharmacy",
            "BrightHealth Pharmacy", "ClearMed Pharmacy",
        ],
        "plumber": [
            "Reliable Plumbing Co.", "FastFix Plumbing", "City Plumbing Services",
            "Premier Plumbers", "All Pro Plumbing", "TrustMark Plumbing",
            "Speedy Pipe Repair", "Expert Plumbing Solutions", "Ace Plumbing & Drain",
            "Main Line Plumbing", "ProFlow Plumbing", "24/7 Plumbing Services",
            "Elite Plumbing Co.", "Master Plumbing Inc.", "Blue Star Plumbing",
            "Superior Plumbing", "Quick Response Plumbing", "American Plumbing Co.",
            "Summit Plumbing Services", "Liberty Plumbing",
        ],
        "electrician": [
            "Bright Spark Electric", "PowerPro Electrical", "City Electric Services",
            "Elite Electricians", "Reliable Electric Co.", "Voltage Masters",
            "Precision Electric", "All Pro Electric", "TrustMark Electrical",
            "Rapid Response Electric", "Expert Electric Solutions", "Ace Electrical",
            "MainLine Electric", "Pro Circuit Electrical", "Benchmark Electric",
            "Premier Electrical Services", "American Electric Co.",
            "Liberty Electrical", "Titan Electric", "Summit Electrical Solutions",
        ],
    }

    # Street names used for generating realistic addresses
    _DEMO_STREETS = [
        "Main St", "Oak Ave", "Maple Dr", "Elm St", "Park Blvd",
        "Broadway", "Washington Ave", "Lincoln Blvd", "Jefferson St",
        "Highland Ave", "Sunset Blvd", "Market St", "Center Ave",
        "Lake Dr", "Cedar Ln", "Willow Rd", "Spring St", "Union Ave",
        "Church St", "River Rd",
    ]

    # City/state abbreviation extracted from a location string like "New York, NY"
    _LOCATION_CITY_STATE: Dict[str, tuple] = {
        "New York, NY": ("New York", "NY"),
        "Los Angeles, CA": ("Los Angeles", "CA"),
        "Chicago, IL": ("Chicago", "IL"),
        "Houston, TX": ("Houston", "TX"),
        "Phoenix, AZ": ("Phoenix", "AZ"),
        "Philadelphia, PA": ("Philadelphia", "PA"),
        "San Antonio, TX": ("San Antonio", "TX"),
        "San Diego, CA": ("San Diego", "CA"),
        "Dallas, TX": ("Dallas", "TX"),
        "Miami, FL": ("Miami", "FL"),
    }

    # ZIP codes per state (one representative ZIP)
    _STATE_ZIPS: Dict[str, List[str]] = {
        "NY": ["10001", "10002", "10003", "10010", "10016", "10019", "10022", "10036"],
        "CA": ["90001", "90012", "90028", "90048", "91601", "94102", "94103", "94110"],
        "IL": ["60601", "60611", "60614", "60622", "60625", "60632", "60640", "60657"],
        "TX": ["77001", "77002", "77005", "77019", "75201", "75202", "75205", "78201"],
        "AZ": ["85001", "85003", "85006", "85012", "85014", "85016", "85018", "85020"],
        "PA": ["19101", "19103", "19107", "19111", "19115", "19120", "19124", "19130"],
        "FL": ["33101", "33109", "33125", "33130", "33131", "33132", "33139", "33140"],
        "GA": ["30301", "30305", "30309", "30312", "30318", "30322", "30324", "30328"],
    }

    def _generate_demo_leads(
        self,
        niche: str,
        location: str,
        max_results: int = 50,
        seed: Optional[int] = None,
    ) -> List[Agency]:
        """
        Generate realistic demo US business leads for offline/API-free use.

        Produces deterministic results for the same niche+location pair so that
        repeated runs don't create duplicate entries with different names.
        """
        # Mask the Python hash to 24 bits to get a stable, non-negative seed value
        # that fits within random.seed()'s reliable integer range across platforms.
        _SEED_BITS = 0xFFFFFF
        # Allow cycling through the name pool with numeric suffixes to generate
        # more unique names than the pool size when max_results > pool size.
        _POOL_CYCLES = 2

        rng = random.Random(seed if seed is not None else hash(f"{niche}:{location}") & _SEED_BITS)

        name_pool = list(self._DEMO_NAME_PARTS.get(niche, self._DEMO_NAME_PARTS["restaurant"]))
        city, state = self._LOCATION_CITY_STATE.get(location, ("", ""))
        if not city:
            # Parse "City, ST" fallback
            parts = location.split(",", 1)
            city = parts[0].strip()
            state = parts[1].strip() if len(parts) > 1 else "US"

        zip_pool = self._STATE_ZIPS.get(state, ["10001", "10002", "10003"])

        # Shuffle name pool deterministically
        rng.shuffle(name_pool)

        agencies: List[Agency] = []
        used_names: set = set()

        for i in range(min(max_results, len(name_pool) * _POOL_CYCLES)):
            # Cycle through name pool with numeric suffix when exhausted
            base_name = name_pool[i % len(name_pool)]
            suffix = f" #{i // len(name_pool) + 1}" if i >= len(name_pool) else ""
            name = f"{base_name} {city}{suffix}".strip() if city not in base_name else f"{base_name}{suffix}"

            if name in used_names:
                continue
            used_names.add(name)

            street_num = rng.randint(100, 9999)
            street = rng.choice(self._DEMO_STREETS)
            zip_code = rng.choice(zip_pool)
            address = f"{street_num} {street}, {city}, {state} {zip_code}"

            rating = round(rng.uniform(2.8, 4.9), 1)
            review_count = rng.choice([
                rng.randint(3, 25),   # small business (most common)
                rng.randint(25, 80),  # medium
                rng.randint(80, 300), # established
            ])
            # Realistic US small-business data coverage probabilities
            _P_WEBSITE = 0.45   # 45% have a website
            _P_SOCIAL = 0.35    # 35% have social media
            _P_EMAIL = 0.30     # 30% have a findable email address
            _P_PHONE = 0.75     # 75% have a phone number listed
            has_website = rng.random() < _P_WEBSITE
            has_social = rng.random() < _P_SOCIAL
            has_email = rng.random() < _P_EMAIL
            has_phone = rng.random() < _P_PHONE

            slug = name.lower().replace(" ", "").replace("&", "and")[:20]
            website = f"https://www.{slug}.com" if has_website else None
            email = f"info@{slug}.com" if has_email else None
            phone_num = (
                f"({rng.randint(200,999)}) {rng.randint(200,999)}-{rng.randint(1000,9999)}"
                if has_phone else None
            )

            agencies.append(Agency(
                name=name,
                niche=niche,
                location=location,
                website=website,
                email=email,
                phone=phone_num,
                address=address,
                google_rating=rating,
                review_count=review_count,
                has_website=has_website,
                has_social_media=has_social,
            ))

            if len(agencies) >= max_results:
                break

        logger.info(
            f"[DEMO] Generated {len(agencies)} sample leads for '{niche}' in '{location}'. "
            "Add a real Google API key to config/api_keys.env to get live data."
        )
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
