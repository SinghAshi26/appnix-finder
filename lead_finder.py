"""
Appnix Local Lead Finder
------------------------
Google Places API (New) se local businesses ki list nikalta hai aur CSV banata hai.

Setup:
    pip install requests
    export GOOGLE_API_KEY=""        (Windows: set GOOGLE_API_KEY=your_key)

Use:
    python lead_finder.py "coaching center" "Lucknow"
    python lead_finder.py "clinic" "Noida Sector 62" --out clinics.csv
    python lead_finder.py "restaurant" "Lucknow Gomti Nagar" --max-pages 3

Tip: ek query se max ~60 results milte hain. Zyada leads ke liye area badal badal ke
chalao (Gomti Nagar, Aliganj, Indira Nagar, Hazratganj...).
"""

import argparse
import csv
import os
import sys
import time

import requests

URL = "https://places.googleapis.com/v1/places:searchText"

# Phone/website/rating wale fields "Enterprise" SKU me aate hain (1,000 free searches/month).
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

# In links ko "asli website" nahi maante: ye log website ke bina hi ginte hain
SOCIAL_HOSTS = (
    "facebook.com", "instagram.com", "justdial.com", "linktr.ee",
    "wa.me", "whatsapp.com", "youtube.com", "twitter.com", "x.com",
    "sulekha.com", "indiamart.com", "business.site",  # business.site = purani Google free site
)


def lead_type(website: str) -> str:
    if not website:
        return "HOT - no website"
    if any(h in website.lower() for h in SOCIAL_HOSTS):
        return "HOT - only social/directory page"
    return "check website (run website_audit.py)"


def search(query: str, api_key: str, max_pages: int):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELDS,
    }
    body = {"textQuery": query, "pageSize": 20, "regionCode": "IN"}
    results = []

    for page in range(max_pages):
        r = requests.post(URL, json=body, headers=headers, timeout=30)
        if r.status_code != 200:
            print(f"API error {r.status_code}: {r.text[:400]}", file=sys.stderr)
            break
        data = r.json()
        results.extend(data.get("places", []))
        token = data.get("nextPageToken")
        if not token:
            break
        body["pageToken"] = token
        time.sleep(2)  # token activate hone me thoda time lagta hai
    return results


def main():
    ap = argparse.ArgumentParser(description="Google Maps se local leads nikalo")
    ap.add_argument("category", help='jaise "coaching center", "clinic", "restaurant"')
    ap.add_argument("city", help='jaise "Lucknow" ya "Noida Sector 62"')
    ap.add_argument("--max-pages", type=int, default=3, help="1-3 (har page 20 results)")
    ap.add_argument("--out", default="leads.csv", help="output CSV file")
    args = ap.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("GOOGLE_API_KEY set nahi hai. README / chat wale steps follow karo.")

    query = f"{args.category} in {args.city}"
    print(f"Searching: {query}")
    places = search(query, api_key, min(args.max_pages, 3))
    print(f"{len(places)} businesses mile")

    # Purani file me jo leads hain unhe dobara mat likho
    seen = set()
    file_exists = os.path.exists(args.out)
    if file_exists:
        with open(args.out, newline="", encoding="utf-8") as f:
            seen = {row["place_id"] for row in csv.DictReader(f)}

    cols = [
        "place_id", "name", "category_searched", "city_searched", "phone",
        "website", "lead_type", "rating", "reviews", "address", "maps_link",
        "email", "status",
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

    print(f"{new_count} nayi leads {args.out} me save hui")
    hot = sum(1 for p in places if lead_type(p.get("websiteUri", "")).startswith("HOT"))
    print(f"Inme se {hot} 'HOT' hain (website nahi / sirf social page)")


if __name__ == "__main__":
    main()