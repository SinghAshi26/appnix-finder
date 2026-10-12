"""
Appnix Lead Finder - Main Application
------------------------------------
Find local business leads via Google Places API (New), audit websites,
extract emails, and perform bilingual WhatsApp outreach.
"""

import datetime
import hmac
import os
import time
from urllib.parse import quote

import pandas as pd
import streamlit as st

from lead_finder import lead_type, search
from templates import TEMPLATES, api_benefit, format_message
from ui import apply_custom_css, render_header, render_metrics
from website_audit import audit

# Page configuration
st.set_page_config(
    page_title="Appnix Lead Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom styling
apply_custom_css()


def secret(name: str, default: str = "") -> str:
    """Safely fetch sensitive credentials from st.secrets or environment variables."""
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


# Password Gate
APP_PASSWORD = secret("APP_PASSWORD")
if APP_PASSWORD:
    if not st.session_state.get("authed", False):
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
        col_center = st.columns([1, 2, 1])[1]
        with col_center:
            st.subheader("🔒 Appnix Lead Finder")
            st.caption("Please enter your access password to continue.")
            entered_pw = st.text_input("Password", type="password", key="gate_password")
            if entered_pw:
                if hmac.compare_digest(entered_pw, APP_PASSWORD):
                    st.session_state["authed"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
        st.stop()

# Initialize session state
if "leads" not in st.session_state:
    st.session_state.leads = pd.DataFrame(
        columns=[
            "name",
            "category",
            "phone",
            "website",
            "lead_type",
            "rating",
            "reviews",
            "address",
            "maps_link",
            "place_id",
            "email",
            "problem",
            "problem_en",
            "problem_hi",
            "contacted_date",
            "status",
        ]
    )

if "sender_name" not in st.session_state:
    st.session_state["sender_name"] = "Jitendra, Appnix Technologies"

# Sidebar: Settings
with st.sidebar:
    st.header("Settings")

    # API Keys status / fallback inputs
    env_google_key = secret("GOOGLE_API_KEY")
    if env_google_key:
        api_key = env_google_key
        st.success("Google Places API: Configured securely")
    else:
        api_key = st.text_input(
            "Google Places API Key",
            type="password",
            help="Enter your Google Maps Places API (New) key",
            key="input_google_key",
        )

    env_psi_key = secret("PSI_API_KEY")
    if env_psi_key:
        psi_key = env_psi_key
        st.success("PageSpeed API: Configured securely")
    else:
        psi_key = st.text_input(
            "PageSpeed API Key (Optional)",
            type="password",
            help="Optional Google PageSpeed Insights API key",
            key="input_psi_key",
        )

    st.markdown("---")
    st.subheader("Outreach Settings")
    sender_input = st.text_input(
        "Sender Name / Organization",
        value=st.session_state["sender_name"],
        help="Included in WhatsApp outreach templates as {sender}",
    )
    if sender_input:
        st.session_state["sender_name"] = sender_input.strip()

    st.markdown("---")
    st.caption(
        "**Best Practice:** Search by specific localities (e.g., 'Gomti Nagar', 'Indira Nagar') "
        "to discover higher volumes of local business listings."
    )

# Render main app header
render_header(
    title="Appnix Lead Finder",
    subtitle="Find local business leads, perform technical website audits, and send tailored WhatsApp messages.",
)

df = st.session_state.leads

# Calculate summary metrics
total_leads = len(df)
hot_leads = int(df["lead_type"].str.startswith("HOT").sum()) if not df.empty else 0
with_phone = int((df["phone"].fillna("").astype(str).str.strip() != "").sum()) if not df.empty else 0
with_email = int((df["email"].fillna("").astype(str).str.strip() != "").sum()) if not df.empty else 0
contacted_count = int((df["status"] == "Contacted").sum()) if not df.empty else 0

# Top metrics bar
render_metrics(
    total=total_leads,
    hot=hot_leads,
    with_phone=with_phone,
    with_email=with_email,
    contacted=contacted_count,
)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Main Application Tabs
tab_find, tab_audit, tab_outreach, tab_export = st.tabs(
    ["Find Leads", "Audit & Emails", "Outreach", "Export"]
)

# -------------------- TAB 1: FIND LEADS --------------------
with tab_find:
    st.subheader("1. Search Google Places")
    c1, c2, c3 = st.columns([3, 3, 1])
    category_in = c1.text_input("Business Category", placeholder="e.g. coaching center, dental clinic, restaurant")
    city_in = c2.text_input("City or Neighborhood", placeholder="e.g. Lucknow Gomti Nagar, Noida Sector 62")
    pages_in = c3.selectbox("Pages", [1, 2, 3], index=2, help="Each page fetches up to 20 business results")

    if st.button("Search Leads", type="primary", use_container_width=False):
        if not api_key:
            st.error("Google Places API Key is missing. Please configure it in the sidebar settings.")
        elif not category_in.strip() or not city_in.strip():
            st.error("Please provide both a business category and a target city/area.")
        else:
            with st.spinner("Searching Google Places API for verified listings..."):
                query_str = f"{category_in.strip()} in {city_in.strip()}"
                places = search(query_str, api_key, pages_in)

            if places:
                new_rows = []
                for p in places:
                    site = p.get("websiteUri", "")
                    new_rows.append(
                        {
                            "name": p.get("displayName", {}).get("text", ""),
                            "category": category_in.strip(),
                            "phone": p.get("nationalPhoneNumber", ""),
                            "website": site,
                            "lead_type": lead_type(site),
                            "rating": p.get("rating", ""),
                            "reviews": p.get("userRatingCount", ""),
                            "address": p.get("formattedAddress", ""),
                            "maps_link": p.get("googleMapsUri", ""),
                            "place_id": p.get("id", ""),
                            "email": "",
                            "problem": "",
                            "problem_en": "",
                            "problem_hi": "",
                            "contacted_date": "",
                            "status": "New",
                        }
                    )
                new_df = pd.DataFrame(new_rows)
                combined = pd.concat([df, new_df], ignore_index=True) if not df.empty else new_df
                deduped = combined.drop_duplicates(subset=["place_id"], keep="first").reset_index(drop=True)
                st.session_state.leads = deduped
                st.success(f"Retrieved {len(new_rows)} leads. Total unique leads in session: {len(deduped)}.")
                st.rerun()
            else:
                st.warning("No listings found. Please verify your query, location, and Google API billing setup.")

    st.markdown("---")
    st.subheader("Current Leads")
    if df.empty:
        st.info("No leads found yet. Enter a business type and area above to start searching.")
    else:
        st.dataframe(
            df[["name", "category", "phone", "website", "lead_type", "rating", "reviews", "status"]],
            use_container_width=True,
            hide_index=True,
        )

# -------------------- TAB 2: AUDIT & EMAILS --------------------
with tab_audit:
    st.subheader("2. Technical Website Audit & Email Extraction")
    if df.empty:
        st.info("No leads yet. Search a business type and area to begin.")
    else:
        st.write(
            "Audit website responsiveness, HTTPS certificates, page speed, and scan home & contact pages for business emails."
        )
        if st.button("Audit Websites & Find Emails", type="primary"):
            progress_bar = st.progress(0.0, text="Initializing audit...")
            todo_indices = df.index.tolist()
            total_items = len(todo_indices)

            for idx, row_idx in enumerate(todo_indices, 1):
                lead_row = df.loc[row_idx]
                site_url = lead_row["website"]
                is_real_site = site_url and not str(lead_row["lead_type"]).startswith("HOT")

                progress_bar.progress(
                    idx / total_items,
                    text=f"Auditing {idx}/{total_items}: {lead_row['name'][:35]}",
                )

                audit_res = audit(site_url if is_real_site else "", bool(psi_key), psi_key or None)

                df.at[row_idx, "problem_en"] = audit_res["problem_en"]
                df.at[row_idx, "problem_hi"] = audit_res["problem_hi"]
                df.at[row_idx, "problem"] = audit_res["problem"]

                if audit_res.get("found_email") and not df.at[row_idx, "email"]:
                    df.at[row_idx, "email"] = audit_res["found_email"].split(",")[0].strip()

                time.sleep(0.2)

            st.session_state.leads = df
            progress_bar.empty()
            st.toast("Website audits and email discovery completed successfully!")
            st.success("Website audits completed.")
            st.rerun()

        st.markdown("---")
        st.subheader("Audited Leads Management")

        # Table filter controls
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 1.5])
        search_query = f_col1.text_input("Search Leads", placeholder="Filter by name or address...")
        lead_type_filter = f_col2.selectbox("Lead Type", ["All", "Hot leads only", "Has website"])
        status_filter = f_col3.selectbox(
            "Status",
            ["All", "New", "Contacted", "Replied", "Meeting", "Closed", "Not interested"],
        )
        has_email_only = f_col4.checkbox("Has Email", value=False)

        # Apply table filters
        filtered_df = df.copy()
        if search_query.strip():
            q = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["name"].astype(str).str.lower().str.contains(q)
                | filtered_df["address"].astype(str).str.lower().str.contains(q)
            ]
        if lead_type_filter == "Hot leads only":
            filtered_df = filtered_df[filtered_df["lead_type"].str.startswith("HOT")]
        elif lead_type_filter == "Has website":
            filtered_df = filtered_df[~filtered_df["lead_type"].str.startswith("HOT")]
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df["status"] == status_filter]
        if has_email_only:
            filtered_df = filtered_df[filtered_df["email"].fillna("").astype(str).str.strip() != ""]

        status_options = ["New", "Contacted", "Replied", "Meeting", "Closed", "Not interested"]

        edited_data = st.data_editor(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "website": st.column_config.LinkColumn("Website"),
                "maps_link": st.column_config.LinkColumn("Google Maps"),
                "status": st.column_config.SelectboxColumn("Status", options=status_options),
            },
            disabled=["place_id", "lead_type", "maps_link"],
        )

        # Synchronize inline edits back to session state
        if edited_data is not None and not edited_data.empty:
            today_str = datetime.date.today().isoformat()
            for row_id in edited_data.index:
                # If updated to Contacted, record the contacted date
                new_status = edited_data.at[row_id, "status"]
                if new_status == "Contacted" and not df.at[row_id, "contacted_date"]:
                    df.at[row_id, "contacted_date"] = today_str
            df.loc[edited_data.index, edited_data.columns] = edited_data
            st.session_state.leads = df

# -------------------- TAB 3: OUTREACH --------------------
with tab_outreach:
    st.subheader("3. WhatsApp Outreach Generator")

    if df.empty:
        st.info("No leads yet. Search a business type and area to begin.")
    else:
        # Daily outreach counter
        today_iso = datetime.date.today().isoformat()
        contacted_today = int((df["contacted_date"] == today_iso).sum())

        metric_col, warning_col = st.columns([1, 2])
        metric_col.metric("Daily Outreach Counter", f"{contacted_today} / 25 sent today")

        if contacted_today >= 25:
            warning_col.warning(
                "⚠️ Sending too many cold WhatsApp messages in a day can get your number blocked. "
                "We recommend pacing yourself to 20-25 messages per day."
            )
        else:
            warning_col.info(
                "Maintain a safe sending pace (under 25 conversations per day) to preserve phone number reputation."
            )

        st.markdown("---")

        lead_names = [n for n in df["name"].tolist() if n]
        selected_lead_name = st.selectbox("Select Target Lead", lead_names)
        lead_row = df[df["name"] == selected_lead_name].iloc[0]

        has_site = bool(lead_row.get("website")) and not str(lead_row.get("lead_type")).startswith("HOT")
        prob_en = (lead_row.get("problem_en") or lead_row.get("problem") or "").strip()
        prob_hi = (lead_row.get("problem_hi") or "").strip()

        # Determine auto-selected template
        if not has_site:
            default_tpl = "No website"
        elif not prob_en or prob_en.startswith("Site looks healthy"):
            default_tpl = "WhatsApp API"
        else:
            default_tpl = "Website redesign"

        lang_col, tpl_col = st.columns([1, 2])
        selected_lang = lang_col.radio("Language", ["English", "Hinglish"], horizontal=True)

        template_choices = list(TEMPLATES[selected_lang].keys())
        default_index = template_choices.index(default_tpl) if default_tpl in template_choices else 0
        selected_template = tpl_col.selectbox(
            f"Template (Auto-selected: {default_tpl})",
            template_choices,
            index=default_index,
            key=f"tpl_select_{lead_row['place_id']}",
        )

        # Prepare parameters for selected language
        problem_text = prob_hi if selected_lang == "Hinglish" else prob_en
        if not problem_text:
            problem_text = (
                "kuch technical improvements ki gunjaish hai"
                if selected_lang == "Hinglish"
                else "minor technical improvements are needed"
            )

        benefit_text = api_benefit(lead_row.get("category", ""), language=selected_lang)
        sender_name = st.session_state.get("sender_name", "Jitendra, Appnix Technologies")

        raw_template = TEMPLATES[selected_lang][selected_template]
        initial_message = format_message(
            raw_template,
            name=lead_row["name"],
            sender=sender_name,
            problem=problem_text,
            benefit=benefit_text,
        )

        st.caption("Note: This message is a starting point. Review and personalize the details before sending.")
        message_body = st.text_area(
            "Message Content",
            value=initial_message,
            height=200,
            key=f"msg_area_{lead_row['place_id']}_{selected_template}_{selected_lang}",
        )

        # Live character and word count
        char_count = len(message_body)
        word_count = len(message_body.split())
        st.markdown(
            f"<div class='meta-hint'>Length: <strong>{char_count}</strong> characters | "
            f"<strong>{word_count}</strong> words</div>",
            unsafe_allow_html=True,
        )

        st.markdown("#### Message Preview & Quick Copy")
        st.code(message_body, language=None)

        # Phone extraction and WhatsApp link
        phone_raw = str(lead_row.get("phone", ""))
        digits = "".join(ch for ch in phone_raw if ch.isdigit())

        btn_col1, btn_col2 = st.columns([1, 1])
        if len(digits) >= 10:
            formatted_phone = "91" + digits[-10:]
            wa_link = f"https://wa.me/{formatted_phone}?text={quote(message_body)}"
            btn_col1.link_button("📲 Open WhatsApp", wa_link, type="primary")
        else:
            btn_col1.info("No valid phone number available for this business.")

        # Quick mark as contacted button
        if btn_col2.button("Mark as Contacted Today", key=f"btn_contact_{lead_row['place_id']}"):
            lead_idx = df[df["place_id"] == lead_row["place_id"]].index[0]
            df.at[lead_idx, "status"] = "Contacted"
            df.at[lead_idx, "contacted_date"] = datetime.date.today().isoformat()
            st.session_state.leads = df
            st.toast(f"Marked '{lead_row['name']}' as Contacted!")
            st.rerun()

# -------------------- TAB 4: EXPORT --------------------
with tab_export:
    st.subheader("4. Export Leads & Reports")
    if df.empty:
        st.info("No leads available to export. Search or import leads to download data.")
    else:
        st.write(f"Export all **{len(df)}** discovered leads with audit insights and outreach history.")

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Leads CSV",
            data=csv_bytes,
            file_name=f"appnix_leads_{datetime.date.today().isoformat()}.csv",
            mime="text/csv",
            type="primary",
        )

        st.markdown("---")
        st.subheader("Dataset Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)