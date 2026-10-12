# Appnix Lead Finder

A streamlined lead generation, website auditing, and WhatsApp outreach tool designed for local business outreach.

Built with **Python 3.12** and **Streamlit**.

---

## Features

- **Google Places Search:** Discovers local business leads by category and locality via Google Places API (New).
- **Technical Website Audit:** Checks for HTTPS security, mobile responsiveness (viewport), page load latency, WordPress detection, and Google PageSpeed Insights (optional).
- **Email Extraction:** Scans homepage and contact pages for verified business emails.
- **Bilingual WhatsApp Outreach:** Tailored templates in English and Hinglish with category-specific automation benefits and Indian phone formatting (`+91`).
- **Daily Outreach Counter:** Tracks daily WhatsApp message volume with built-in safety recommendations to protect number reputation.

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
PSI_API_KEY = "your_pagespeed_api_key"   # Optional: For PageSpeed scores
APP_PASSWORD = "your_secret_password"   # Optional: Password protect the UI
```

> **Security Note:** Never commit `secrets.toml` to Git. The `.gitignore` file is configured to exclude `secrets.toml`, `.env`, and `.streamlit/secrets.toml`.

---

## 3. Deployment

### Streamlit Community Cloud
1. Push your repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **"New app"**.
3. Select your repository (`HexaNode-Systems/appnix-leads`), branch (`main`), and main file path (`app.py`).
4. Click **Advanced settings** > **Secrets** and paste your secrets in TOML format:
   ```toml
   GOOGLE_API_KEY = "your_google_places_api_key"
   PSI_API_KEY = "your_pagespeed_api_key"
   APP_PASSWORD = "your_secret_password"
   ```
5. Deploy.

### Hugging Face Spaces
1. Create a new Space on [Hugging Face](https://huggingface.co/spaces).
2. Choose **Streamlit** as the Space SDK.
3. Push or link this repository.
4. In Space **Settings** > **Variables and secrets**, add `GOOGLE_API_KEY`, `PSI_API_KEY`, and `APP_PASSWORD`.

---

## 4. CLI Usage

You can also run the backend tools directly from the terminal:

### Lead Finder
```bash
python lead_finder.py "dental clinic" "Noida Sector 62" --max-pages 3 --out clinics.csv
```

### Website Audit
```bash
python website_audit.py clinics.csv --out audited_clinics.csv
```
