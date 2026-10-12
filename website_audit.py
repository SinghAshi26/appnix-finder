"""
Appnix Website Audit and Email Finder
-------------------------------------
Audits lead websites for essential technical indicators:
  - Contact email addresses (homepage and contact/about pages)
  - HTTPS security
  - Mobile friendliness (viewport meta tag)
  - Page load latency
  - WordPress / legacy CMS signatures
  - Google PageSpeed Insights mobile performance score (optional)
  - Diagnostic problem descriptions in both English and Hinglish
"""

import argparse
import csv
import os
import re
import sys
import time
from typing import Any, Dict, Optional, Set, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AppnixAudit/1.0)"}
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
JUNK_EMAIL = ("sentry", "example.", "wixpress", "domain.com", "email.com", ".png", ".jpg", ".webp")
CONTACT_HINTS = ("contact", "about", "reach", "support")


def get(url: str, timeout: int = 12) -> Tuple[requests.Response, float]:
    """Fetch URL and measure response duration in seconds."""
    start = time.time()
    r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    return r, round(time.time() - start, 2)


def find_emails(html: str, base_url: str, soup: BeautifulSoup) -> Set[str]:
    """Extract and sanitize business emails from page HTML and mailto links."""
    emails: Set[str] = set(EMAIL_RE.findall(html))
    for a in soup.select('a[href^="mailto:"]'):
        emails.add(a.get("href", "").replace("mailto:", "").split("?")[0].strip())
    clean_emails = {e.lower() for e in emails if e and not any(j in e.lower() for j in JUNK_EMAIL)}
    return clean_emails


def contact_page_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Find contact or about page link from page navigation."""
    for a in soup.find_all("a", href=True):
        text = (a.get_text() + a["href"]).lower()
        if any(h in text for h in CONTACT_HINTS):
            return urljoin(base_url, a["href"])
    return None


def psi_score(url: str, key: str) -> Any:
    """Fetch mobile performance score via Google PageSpeed Insights API."""
    api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    try:
        r = requests.get(api, params={"url": url, "strategy": "mobile", "key": key}, timeout=60)
        if r.status_code != 200:
            return ""
        score = r.json()["lighthouseResult"]["categories"]["performance"]["score"]
        return int(score * 100)
    except Exception:
        return ""


def audit(url: str, use_psi: bool = False, psi_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform technical audit on a website URL.
    Returns technical signals and problem summaries in both English and Hinglish.
    """
    out: Dict[str, Any] = {
        "https": "",
        "mobile_friendly": "",
        "load_sec": "",
        "wordpress": "",
        "psi_mobile": "",
        "found_email": "",
        "problem": "",
        "problem_en": "",
        "problem_hi": "",
    }

    if not url:
        out["problem_en"] = "No website found"
        out["problem_hi"] = "Website hi nahi hai"
        out["problem"] = out["problem_en"]
        return out

    if not url.startswith("http"):
        url = "http://" + url

    try:
        r, secs = get(url)
    except Exception:
        out["problem_en"] = "Website unreachable or down"
        out["problem_hi"] = "Website khul nahi rahi / down hai"
        out["problem"] = out["problem_en"]
        return out

    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    final = r.url

    out["https"] = "yes" if final.startswith("https") else "no"
    out["mobile_friendly"] = "yes" if soup.find("meta", attrs={"name": "viewport"}) else "no"
    out["load_sec"] = secs
    out["wordpress"] = "yes" if "wp-content" in html or "wp-includes" in html else "no"

    emails = find_emails(html, final, soup)
    if not emails:
        c = contact_page_url(soup, final)
        if c:
            try:
                r2, _ = get(c)
                emails = find_emails(r2.text, c, BeautifulSoup(r2.text, "html.parser"))
            except Exception:
                pass
    out["found_email"] = ", ".join(sorted(emails)[:3])

    if use_psi and psi_key:
        out["psi_mobile"] = psi_score(final, psi_key)

    problems_en = []
    problems_hi = []

    if out["https"] == "no":
        problems_en.append("website is not secure (no HTTPS), shows 'Not Secure' warning")
        problems_hi.append("website secure (HTTPS) nahi hai, browser 'Not secure' dikhata hai")

    if out["mobile_friendly"] == "no":
        problems_en.append("website is not mobile-friendly (missing viewport tag)")
        problems_hi.append("mobile par theek se nahi dikhti")

    if secs and secs > 3:
        problems_en.append(f"slow load time ({secs}s)")
        problems_hi.append(f"load hone me {secs} sec lagte hain")

    if out["psi_mobile"] != "" and isinstance(out["psi_mobile"], int) and out["psi_mobile"] < 50:
        problems_en.append(f"Google mobile performance score is low ({out['psi_mobile']}/100)")
        problems_hi.append(f"Google mobile speed score sirf {out['psi_mobile']}/100 hai")

    if not re.search(r"(whatsapp|wa\.me)", html, re.I):
        problems_en.append("no direct WhatsApp chat or inquiry button")
        problems_hi.append("WhatsApp chat/enquiry button nahi hai")

    if problems_en:
        out["problem_en"] = "; ".join(problems_en[:2])
        out["problem_hi"] = "; ".join(problems_hi[:2])
    else:
        out["problem_en"] = "Site looks healthy - pitch WhatsApp automation or custom tools"
        out["problem_hi"] = "Site theek hai - WhatsApp/automation angle use karo"

    out["problem"] = out["problem_en"]
    return out


def main() -> None:
    """CLI tool for auditing a CSV list of leads."""
    ap = argparse.ArgumentParser(description="Audit websites and extract emails from a leads CSV")
    ap.add_argument("csv_in", help="Input CSV filepath")
    ap.add_argument("--out", default="audited.csv", help="Output audited CSV filepath")
    ap.add_argument("--psi", action="store_true", help="Include Google PageSpeed Insights score (slower)")
    args = ap.parse_args()

    psi_key = os.environ.get("PSI_API_KEY")
    if args.psi and not psi_key:
        sys.exit("Error: PSI_API_KEY environment variable is required when using --psi flag.")

    with open(args.csv_in, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        sys.exit("Error: Input CSV file is empty.")

    new_cols = [
        "https",
        "mobile_friendly",
        "load_sec",
        "wordpress",
        "psi_mobile",
        "found_email",
        "problem",
        "problem_en",
        "problem_hi",
    ]
    fieldnames = list(rows[0].keys()) + [c for c in new_cols if c not in rows[0]]

    for i, row in enumerate(rows, 1):
        site = row.get("website", "")
        is_real = site and not row.get("lead_type", "").startswith("HOT")
        name = row.get("name", "")[:40]
        print(f"[{i}/{len(rows)}] Auditing: {name}")
        row.update(audit(site if is_real else "", args.psi, psi_key))
        if row.get("found_email") and not row.get("email"):
            row["email"] = row["found_email"].split(",")[0].strip()
        time.sleep(0.5)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\nAudit complete. Saved to {args.out}.")


if __name__ == "__main__":
    main()