"""
Contact Scraper Module
Extracts contact information from business websites
Owner: Md Jamil Islam
"""
import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class ContactScraper:
    """
    Scrapes contact information (email, phone, social) from business websites.
    """

    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )
    PHONE_PATTERN = re.compile(
        r"(\+?880|0)[-\s]?1[3-9]\d{8}|"
        r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    )

    def __init__(self, delay: float = 1.5, timeout: int = 10):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
        })

    def scrape_website(self, url: str) -> Dict:
        """
        Scrape contact info from a website.
        Returns dict with email, phone, facebook, instagram, etc.
        """
        if not url.startswith("http"):
            url = "https://" + url

        contact_info = {
            "url": url,
            "emails": [],
            "phones": [],
            "facebook": None,
            "instagram": None,
            "twitter": None,
            "linkedin": None,
            "whatsapp": None,
        }

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract emails
            text = response.text
            emails = list(set(self.EMAIL_PATTERN.findall(text)))
            contact_info["emails"] = [
                e for e in emails
                if not any(skip in e for skip in ["example.", "test.", "noreply"])
            ]

            # Extract phones
            phones = list(set(self.PHONE_PATTERN.findall(text)))
            contact_info["phones"] = [p[0] or p[1] for p in phones if p[0] or p[1]]

            # Extract social media links
            for link in soup.find_all("a", href=True):
                href = link["href"].lower()
                if "facebook.com" in href and not contact_info["facebook"]:
                    contact_info["facebook"] = link["href"]
                elif "instagram.com" in href and not contact_info["instagram"]:
                    contact_info["instagram"] = link["href"]
                elif "twitter.com" in href and not contact_info["twitter"]:
                    contact_info["twitter"] = link["href"]
                elif "linkedin.com" in href and not contact_info["linkedin"]:
                    contact_info["linkedin"] = link["href"]
                elif "wa.me" in href or "whatsapp.com" in href:
                    contact_info["whatsapp"] = link["href"]

            # Also check contact page
            contact_page = self._find_contact_page(soup, url)
            if contact_page:
                contact_info.update(self._scrape_contact_page(contact_page))

            time.sleep(self.delay)

        except requests.RequestException as e:
            logger.warning(f"Could not scrape {url}: {e}")

        return contact_info

    def _find_contact_page(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find the contact page URL from a website."""
        contact_keywords = ["contact", "contact-us", "contacts", "about", "reach-us"]
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if any(kw in href for kw in contact_keywords):
                return urljoin(base_url, link["href"])
        return None

    def _scrape_contact_page(self, url: str) -> Dict:
        """Scrape additional contact info from contact page."""
        result = {}
        try:
            response = self.session.get(url, timeout=self.timeout)
            text = response.text
            emails = list(set(self.EMAIL_PATTERN.findall(text)))
            if emails:
                result["emails"] = [
                    e for e in emails
                    if not any(s in e for s in ["example.", "test.", "noreply"])
                ]
            time.sleep(self.delay)
        except Exception:
            pass
        return result

    def scrape_bulk(self, urls: List[str]) -> List[Dict]:
        """Scrape contact info from multiple websites."""
        results = []
        for i, url in enumerate(urls):
            logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
            result = self.scrape_website(url)
            results.append(result)
        return results
