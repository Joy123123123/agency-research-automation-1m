# Agency Research Automation Scripts
# Author: Md Jamil Islam

import requests
import csv
import json
import time
from datetime import datetime


def search_agencies(niche: str, location: str, limit: int = 50) -> list:
    """
    Search for marketing agencies based on niche and location.
    Returns a list of agency data dictionaries.
    
    Args:
        niche: Agency specialization (e.g., 'SEO', 'PPC', 'social media')
        location: Target location (e.g., 'New York', 'London')
        limit: Maximum number of results to return
    
    Returns:
        List of agency dictionaries with name, website, contact info
    """
    print(f"Searching for {niche} agencies in {location}...")
    
    # Example: Scrape Clutch.co or use their API
    # Replace with actual API calls as needed
    agencies = []
    
    # Simulated data structure - replace with real API integration
    sample_agency = {
        "name": f"Sample {niche} Agency",
        "website": "https://example.com",
        "location": location,
        "email": "contact@example.com",
        "linkedin": "https://linkedin.com/company/sample",
        "employees": "5-20",
        "niche": niche,
        "found_date": datetime.now().strftime("%Y-%m-%d"),
    }
    agencies.append(sample_agency)
    
    print(f"Found {len(agencies)} agencies")
    return agencies[:limit]


def export_to_csv(agencies: list, filename: str = "tracking/client_tracker.csv"):
    """
    Export agency list to CSV for tracking.
    
    Args:
        agencies: List of agency dictionaries
        filename: Output CSV file path
    """
    if not agencies:
        print("No agencies to export")
        return
    
    fieldnames = list(agencies[0].keys()) + ["status", "outreach_date", "follow_up_date", "notes"]
    
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for agency in agencies:
            row = {**agency, "status": "new", "outreach_date": "", "follow_up_date": "", "notes": ""}
            writer.writerow(row)
    
    print(f"Exported {len(agencies)} agencies to {filename}")


def filter_agencies_by_budget(agencies: list, min_employees: int = 2, max_employees: int = 50) -> list:
    """
    Filter agencies based on estimated size/budget indicators.
    
    Args:
        agencies: List of agency dictionaries
        min_employees: Minimum number of employees
        max_employees: Maximum number of employees
    
    Returns:
        Filtered list of agencies
    """
    filtered = []
    for agency in agencies:
        emp_str = agency.get("employees", "1-5")
        try:
            emp_min = int(emp_str.split("-")[0])
            if min_employees <= emp_min <= max_employees:
                filtered.append(agency)
        except (ValueError, IndexError):
            filtered.append(agency)
    
    print(f"Filtered to {len(filtered)} agencies (size {min_employees}-{max_employees} employees)")
    return filtered


if __name__ == "__main__":
    # Example usage
    niches = ["SEO", "PPC", "social media", "content marketing"]
    locations = ["New York", "London", "Toronto", "Sydney"]
    
    all_agencies = []
    for niche in niches[:2]:  # Start with 2 niches
        for location in locations[:2]:  # Start with 2 locations
            agencies = search_agencies(niche, location, limit=25)
            all_agencies.extend(agencies)
            time.sleep(1)  # Be respectful with rate limiting
    
    # Filter for ideal client size
    filtered = filter_agencies_by_budget(all_agencies, min_employees=2, max_employees=30)
    
    # Export to tracking sheet
    export_to_csv(filtered)
    print(f"\nTotal agencies ready for outreach: {len(filtered)}")
