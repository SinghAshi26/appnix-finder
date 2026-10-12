# Appnix Lead Finder

A streamlined lead generation, website auditing, and manual outreach platform designed for local businesses.

Built with **Python 3.12** and **Streamlit**.

---

## Features

- **Google Places Search:** Discovers local business listings by category and locality via Google Places API (New).
- **Places API Call Counter:** Tracks monthly API call volumes with automatic progress bars, safety threshold alerts (80%+), and hard stops in `usage.json`.
- **Deep Technical Website Audit:**
  - **SSL Certificate Expiry:** Connects via `socket` and `ssl` to measure days until certificate expiration and flag expiring/expired certificates.
  - **Broken Internal Links:** Samples up to 15 internal links on the homepage to detect 404 or 5xx broken links.
  - **On-Page SEO & UX Basics:** Checks for `<title>`, meta descriptions, `<h1>` headlines, mobile viewport tags, outdated copyright dates (>2 years), contact forms, and WhatsApp buttons.
  - **Google PageSpeed Insights (Optional):** Fetches mobile performance scores, Largest Contentful Paint (LCP), and Cumulative Layout Shift (CLS).
- **Advanced Email Discovery:**
  - Scans homepage and contact/about/privacy subpages.
  - Extracts `mailto:` links, plain-text emails, and obfuscated email formats (e.g. `name [at] domain [dot] com`).
  - Reads schema.org `email` from `<script type="application/ld+json">` and meta tags.
  - Ranks emails by confidence (same-domain vs personal vs role accounts) and filters junk addresses.
  - Suggests unverified email pattern guesses (`info@`, `contact@`, `hello@`) if no verified email exists.
  - Extracts social profile links (Instagram, Facebook, LinkedIn).
- **Manual WhatsApp Outreach:** Bilingual templates (English & Hinglish) with category-specific benefits, Indian phone formatting (`+91`), and daily safety counters (25 conversations/day limit).
- **Manual Email Outreach:** Bilingual plain-text templates (80–120 words), direct "Open in Gmail" / "Open in Mail App" launch buttons, and 3-day duplicate follow-up warnings.

---

## 1. Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/HexaNode-Systems/appnix-leads.git
cd appnix-leads

# Install required dependencies
pip install -r requirements.txt
```

### Running the App
```bash
streamlit run app.py
```

---

## 2. Secrets Configuration

Configure credentials either in `.streamlit/secrets.toml` (locally) or via environment variables:

```toml
# .streamlit/secrets.toml
GOOGLE_API_KEY = "your_google_places_api_key"
PSI_API_KEY = "your_pagespeed_api_key"   # Optional: For PageSpeed mobile scores
APP_PASSWORD = "your_secret_password"   # Optional: Password protect the UI
```

> **Security Note:** Never commit `secrets.toml` or API keys to Git. The `.gitignore` file is configured to exclude `secrets.toml`, `.env`, and `.streamlit/secrets.toml`.

---

## 3. How the PageSpeed API Key Works

- If `PSI_API_KEY` is provided, the audit calls the Google PageSpeed Insights API (mobile strategy) for each website.
- It extracts:
  - **Performance Score** (0–100)
  - **LCP (Largest Contentful Paint)** in seconds
  - **CLS (Cumulative Layout Shift)**
- If the API returns a rate limit (HTTP 429) or quota error, the app handles it gracefully without interrupting the rest of the audit.
- If no PageSpeed key is configured, all other technical audit checks (SSL, broken links, mobile viewport, email discovery) continue to run normally.

---

## 4. Cold Email Sending Rules & Best Practices

To ensure high inbox placement and protect your domain reputation:

1. **Send from your business domain:** Never send cold outreach from free `@gmail.com` addresses.
2. **Setup Domain Authentication:** Ensure **SPF**, **DKIM**, and **DMARC** DNS records are properly configured for your sending domain.
3. **Pace your volume:** Limit manual cold sending to **20–30 emails per day** from a new or warmed inbox.
4. **Manual review:** Review and personalize the observation in every message before sending. The app provides one-click links to open drafts in Gmail or your default email client.
5. **Honor opt-outs:** All provided templates conclude with a clear, polite opt-out sentence.
6. **Duplicate Guard:** The app logs outreach dates and warns you if you attempt to contact the same lead again within 3 days.

---

## 5. Deployment

### Streamlit Community Cloud
1. Push your repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app from your repository (`main` branch, `app.py`).
3. Under **App settings** > **Secrets**, enter your keys:
   ```toml
   GOOGLE_API_KEY = "your_google_places_api_key"
   PSI_API_KEY = "your_pagespeed_api_key"
   APP_PASSWORD = "your_app_password"
   ```
4. Deploy.

### Hugging Face Spaces
1. Create a Space on [Hugging Face](https://huggingface.co/spaces) with SDK set to **Streamlit**.
2. In Space **Settings** > **Variables and secrets**, add `GOOGLE_API_KEY`, `PSI_API_KEY`, and `APP_PASSWORD`.

---

## 6. CLI Usage

### Lead Finder
```bash
python lead_finder.py "dental clinic" "Noida Sector 62" --max-pages 3 --out clinics.csv
```

### Deep Website Audit
```bash
python website_audit.py clinics.csv --out audited_clinics.csv --psi
```
