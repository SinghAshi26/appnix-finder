"""
Appnix Website Audit + Email Finder
-----------------------------------
leads.csv ki har website check karta hai aur ye nikalta hai:
  - email (homepage + contact page se)
  - HTTPS hai ya nahi
  - mobile-friendly (viewport tag) hai ya nahi
  - load time
  - WordPress / purani site ke signs
  - ek line ka "problem" jo cold email me directly use kar sakte ho

Setup:
    pip install requests beautifulsoup4

Use:
    python website_audit.py leads.csv
    python website_audit.py leads.csv --out audited.csv

Optional (Google PageSpeed score ke liye, free key):
    export PSI_API_KEY=""
    python website_audit.py leads.csv --psi
"""

import argparse
import csv
import os
import re
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AppnixAudit/1.0)"}
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
JUNK_EMAIL = ("sentry", "example.", "wixpress", "domain.com", "email.com", ".png", ".jpg", ".webp")
CONTACT_HINTS = ("contact", "about", "reach")


def get(url, timeout=12):
    start = time.time()
    r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    return r, round(time.time() - start, 2)


def find_emails(html, base_url, soup):
    emails = set(EMAIL_RE.findall(html))
    for a in soup.select('a[href^="mailto:"]'):
        emails.add(a["href"].replace("mailto:", "").split("?")[0].strip())
    emails = {e.lower() for e in emails if not any(j in e.lower() for j in JUNK_EMAIL)}
    return emails


def contact_page_url(soup, base_url):
    for a in soup.find_all("a", href=True):
        text = (a.get_text() + a["href"]).lower()
        if any(h in text for h in CONTACT_HINTS):
            return urljoin(base_url, a["href"])
    return None


def psi_score(url, key):
    api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    r = requests.get(api, params={"url": url, "strategy": "mobile", "key": key}, timeout=60)
    if r.status_code != 200:
        return ""
    score = r.json()["lighthouseResult"]["categories"]["performance"]["score"]
    return int(score * 100)


def audit(url, use_psi, psi_key):
    out = {"https": "", "mobile_friendly": "", "load_sec": "", "wordpress": "",
           "psi_mobile": "", "found_email": "", "problem": ""}
    if not url:
        out["problem"] = "Website hi nahi hai"
        return out
    if not url.startswith("http"):
        url = "http://" + url

    try:
        r, secs = get(url)
    except Exception:
        out["problem"] = "Website khul nahi rahi / down hai"
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

    # Cold email me use hone wali problem line (sabse bada issue pehle)
    problems = []
    if out["https"] == "no":
        problems.append("website secure (HTTPS) nahi hai, browser 'Not secure' dikhata hai")
    if out["mobile_friendly"] == "no":
        problems.append("mobile par theek se nahi dikhti")
    if secs and secs > 3:
        problems.append(f"load hone me {secs} sec lagte hain")
    if out["psi_mobile"] != "" and out["psi_mobile"] < 50:
        problems.append(f"Google mobile speed score sirf {out['psi_mobile']}/100 hai")
    if not re.search(r"(whatsapp|wa\.me)", html, re.I):
        problems.append("WhatsApp chat/enquiry button nahi hai")
    out["problem"] = "; ".join(problems[:2]) if problems else "Site theek hai - WhatsApp/automation angle use karo"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_in")
    ap.add_argument("--out", default="audited.csv")
    ap.add_argument("--psi", action="store_true", help="Google PageSpeed score bhi lo (slow)")
    args = ap.parse_args()

    psi_key = os.environ.get("PSI_API_KEY")
    if args.psi and not psi_key:
        sys.exit("PSI_API_KEY set karo ya --psi hata do.")

    with open(args.csv_in, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    new_cols = ["https", "mobile_friendly", "load_sec", "wordpress", "psi_mobile", "found_email", "problem"]
    fieldnames = list(rows[0].keys()) + [c for c in new_cols if c not in rows[0]]

    for i, row in enumerate(rows, 1):
        site = row.get("website", "")
        # social/directory page ko website nahi maante
        is_real = site and not row.get("lead_type", "").startswith("HOT")
        print(f"[{i}/{len(rows)}] {row.get('name', '')[:40]}")
        row.update(audit(site if is_real else "", args.psi, psi_key))
        if row.get("found_email") and not row.get("email"):
            row["email"] = row["found_email"].split(",")[0].strip()
        time.sleep(0.5)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nDone. {args.out} me save hua. 'problem' column cold email me use karo.")


if __name__ == "__main__":
    main()