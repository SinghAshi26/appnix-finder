"""
Appnix Local Lead Finder
------------------------
Extracts local business listings via Google Places API (New) and saves them to CSV.

Setup:
    pip install requests
    export GOOGLE_API_KEY="your_api_key"    (Windows: set GOOGLE_API_KEY=your_api_key)

Usage:
    python lead_finder.py "coaching center" "Lucknow"
    python lead_finder.py "clinic" "Noida Sector 62" --out clinics.csv
    python lead_finder.py "restaurant" "Lucknow Gomti Nagar" --max-pages 3
"""

import argparse
import csv
import os
import sys
import time
from typing import Any, Dict, List

import requests

URL = "https://places.googleapis.com/v1/places:searchText"

# Contact, website, and rating fields fall under Google Places Enterprise SKU
FIELDS = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
        "places.googleMapsUri",
        "places.businessStatus",
        "nextPageToken",
    ]
)

# Domains considered social media or directories rather than official websites
SOCIAL_HOSTS = (
    "facebook.com",
    "instagram.com",
    "justdial.com",
    "linktr.ee",
    "wa.me",
    "whatsapp.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "sulekha.com",
    "indiamart.com",
    "business.site",  # Legacy Google business mini-sites
)


def lead_type(website: str) -> str:
    """Classify lead priority based on website presence."""
    if not website:
        return "HOT - no website"
    if any(h in website.lower() for h in SOCIAL_HOSTS):
        return "HOT - only social/directory page"
    return "Check website"


def search(query: str, api_key: str, max_pages: int) -> List[Dict[str, Any]]:
    """Search Google Places API for businesses matching the query."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELDS,
    }
    body: Dict[str, Any] = {"textQuery": query, "pageSize": 20, "regionCode": "IN"}
    results: List[Dict[str, Any]] = []

    for _ in range(max_pages):
        r = requests.post(URL, json=body, headers=headers, timeout=30)
        if r.status_code != 200:
            print(f"Places API error ({r.status_code}): {r.text[:400]}", file=sys.stderr)
            break
        data = r.json()
        results.extend(data.get("places", []))
        token = data.get("nextPageToken")
        if not token:
            break
        body["pageToken"] = token
        time.sleep(2)  # Wait for Google token propagation
    return results


def main() -> None:
    """CLI entry point for searching leads and writing to CSV."""
    ap = argparse.ArgumentParser(description="Find local business leads via Google Maps Places API")
    ap.add_argument("category", help='Business type, e.g., "coaching center", "clinic", "restaurant"')
    ap.add_argument("city", help='City or neighborhood, e.g., "Lucknow" or "Noida Sector 62"')
    ap.add_argument("--max-pages", type=int, default=3, help="Pages to fetch (1-3, each page has up to 20 results)")
    ap.add_argument("--out", default="leads.csv", help="Output CSV filepath")
    args = ap.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("Error: GOOGLE_API_KEY environment variable is not set. Please configure your key.")

    query = f"{args.category} in {args.city}"
    print(f"Searching: {query}")
    places = search(query, api_key, min(args.max_pages, 3))
    print(f"Found {len(places)} businesses.")

    seen = set()
    file_exists = os.path.exists(args.out)
    if file_exists:
        with open(args.out, newline="", encoding="utf-8") as f:
            seen = {row.get("place_id", "") for row in csv.DictReader(f)}

    cols = [
        "place_id",
        "name",
        "category_searched",
        "city_searched",
        "phone",
        "website",
        "lead_type",
        "rating",
        "reviews",
        "address",
        "maps_link",
        "email",
        "status",
    ]
    new_count = 0
    with open(args.out, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if not file_exists:
            w.writeheader()
        for p in places:
            pid = p.get("id", "")
            if pid in seen or p.get("businessStatus") not in (None, "OPERATIONAL"):
                continue
            site = p.get("websiteUri", "")
            w.writerow(
                {
                    "place_id": pid,
                    "name": p.get("displayName", {}).get("text", ""),
                    "category_searched": args.category,
                    "city_searched": args.city,
                    "phone": p.get("nationalPhoneNumber", ""),
                    "website": site,
                    "lead_type": lead_type(site),
                    "rating": p.get("rating", ""),
                    "reviews": p.get("userRatingCount", ""),
                    "address": p.get("formattedAddress", ""),
                    "maps_link": p.get("googleMapsUri", ""),
                    "email": "",
                    "status": "New",
                }
            )
            new_count += 1

    print(f"Saved {new_count} new leads to {args.out}.")
    hot = sum(1 for p in places if lead_type(p.get("websiteUri", "")).startswith("HOT"))
    print(f"{hot} leads classified as 'HOT' (no website or social-only link).")


if __name__ == "__main__":
    main()