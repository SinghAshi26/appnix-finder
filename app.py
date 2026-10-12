"""
Appnix Lead Finder - UI
Run:  streamlit run app.py
(lead_finder.py aur website_audit.py isi folder me hone chahiye)
"""

import time

import pandas as pd
import streamlit as st

from lead_finder import lead_type, search
from website_audit import audit

st.set_page_config(page_title="Appnix Lead Finder", page_icon="🎯", layout="wide")


def secret(name: str, default: str = "") -> str:
    """st.secrets (cloud / .streamlit/secrets.toml) ya environment se value lo."""
    try:
        return st.secrets[name]
    except Exception:
        import os
        return os.environ.get(name, default)


# ---------- Password gate (deploy ke baad zaroori) ----------
APP_PASSWORD = secret("APP_PASSWORD")
if APP_PASSWORD:
    import hmac

    if not st.session_state.get("authed"):
        st.title("🔒 Appnix Lead Finder")
        pw = st.text_input("Password", type="password")
        if pw:
            if hmac.compare_digest(pw, APP_PASSWORD):
                st.session_state["authed"] = True
                st.rerun()
            else:
                st.error("Galat password")
        st.stop()

st.title("🎯 Appnix Lead Finder")
st.caption("Google Maps se local leads nikalo, website audit karo, email dhundo")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Settings")
    api_key = secret("GOOGLE_API_KEY")
    psi_key = secret("PSI_API_KEY")
    if api_key:
        st.success("Google API key secure secrets se load hui")
    else:
        api_key = st.text_input("Google API Key", type="password", help="Places API (New) wali key")
        psi_key = st.text_input("PageSpeed API Key (optional)", type="password")
    st.markdown("---")
    st.markdown(
        "**Tip:** ek search se max ~60 leads aati hain. "
        "Zyada ke liye area badal ke dobara search karo."
    )

if "leads" not in st.session_state:
    st.session_state.leads = pd.DataFrame()

# ---------- Step 1: Search ----------
st.subheader("1. Leads dhundo")
c1, c2, c3 = st.columns([3, 3, 1])
category = c1.text_input("Business type", placeholder="coaching center, clinic, restaurant...")
city = c2.text_input("City / Area", placeholder="Lucknow Gomti Nagar")
pages = c3.selectbox("Pages", [1, 2, 3], index=2, help="Har page = 20 results")

if st.button("🔍 Search leads", type="primary"):
    if not api_key:
        st.error("Sidebar me Google API Key daalo.")
    elif not category or not city:
        st.error("Business type aur city dono daalo.")
    else:
        with st.spinner("Google Maps se leads la raha hu..."):
            places = search(f"{category} in {city}", api_key, pages)
        rows = []
        for p in places:
            site = p.get("websiteUri", "")
            rows.append(
                {
                    "name": p.get("displayName", {}).get("text", ""),
                    "category": category,
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
                    "status": "New",
                }
            )
        new = pd.DataFrame(rows)
        if not new.empty:
            old = st.session_state.leads
            combined = pd.concat([old, new], ignore_index=True) if not old.empty else new
            st.session_state.leads = combined.drop_duplicates("place_id").reset_index(drop=True)
            st.success(f"{len(new)} businesses mile.")
        else:
            st.warning("Kuch nahi mila. Key, billing ya query check karo.")

df = st.session_state.leads

# ---------- Step 2: Audit ----------
if not df.empty:
    hot = df["lead_type"].str.startswith("HOT").sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total leads", len(df))
    m2.metric("HOT (no website)", int(hot))
    m3.metric("With phone", int((df["phone"] != "").sum()))

    st.subheader("2. Website audit + email")
    if st.button("🩺 Audit websites & find emails"):
        bar = st.progress(0.0, text="Starting...")
        todo = df.index.tolist()
        for n, i in enumerate(todo, 1):
            row = df.loc[i]
            site = row["website"]
            is_real = site and not row["lead_type"].startswith("HOT")
            bar.progress(n / len(todo), text=f"{n}/{len(todo)}  {row['name'][:40]}")
            res = audit(site if is_real else "", bool(psi_key), psi_key or None)
            df.at[i, "problem"] = res["problem"]
            if res["found_email"] and not df.at[i, "email"]:
                df.at[i, "email"] = res["found_email"].split(",")[0].strip()
            time.sleep(0.3)
        st.session_state.leads = df
        bar.empty()
        st.success("Audit complete.")

    # ---------- Table ----------
    st.subheader("3. Leads")
    only_hot = st.checkbox("Sirf HOT leads dikhao")
    view = df[df["lead_type"].str.startswith("HOT")] if only_hot else df

    edited = st.data_editor(
        view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "website": st.column_config.LinkColumn("website"),
            "maps_link": st.column_config.LinkColumn("maps_link"),
            "status": st.column_config.SelectboxColumn(
                "status", options=["New", "Contacted", "Replied", "Meeting", "Closed", "Not interested"]
            ),
        },
        disabled=["place_id", "lead_type", "maps_link"],
    )
    # edits (status/email) wapas save karo
    df.loc[edited.index, edited.columns] = edited
    st.session_state.leads = df

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        "appnix_leads.csv",
        "text/csv",
    )

    # ---------- WhatsApp templates ----------
    st.subheader("4. WhatsApp message bhejo")

    SENDER = "Jitendra, Appnix Technologies"

    # Business type ke hisaab se WhatsApp API ka fayda
    def api_benefit(cat: str) -> str:
        c = (cat or "").lower()
        if any(k in c for k in ("coaching", "school", "institute", "academy", "tuition", "college")):
            return "admission enquiries ka auto-reply, fees reminder aur batch updates"
        if any(k in c for k in ("clinic", "hospital", "doctor", "dental", "pathology", "lab")):
            return "appointment booking, reminders aur report updates"
        if any(k in c for k in ("restaurant", "cafe", "bakery", "food", "sweet")):
            return "order updates, offers aur repeat customers ko bulk messages"
        if any(k in c for k in ("real estate", "property", "builder")):
            return "enquiry ka turant reply aur site-visit follow-ups"
        if any(k in c for k in ("shop", "store", "boutique", "showroom", "fashion", "retail")):
            return "order updates, offers aur festival broadcast"
        return "customer enquiries ka auto-reply aur follow-up messages"

    TEMPLATES = {
        "No website": (
            "Namaste {name} team, main {sender} se.\n\n"
            "Maine Google par {name} dekha, par online koi proper website nahi mili. "
            "Aaj ke time mein log pehle Google par check karte hain, isliye bahut se customers "
            "bina contact kiye hi dusre option par chale jaate hain.\n\n"
            "Hum chhote businesses ke liye affordable website banate hain (enquiry button + WhatsApp link ke saath). "
            "Kya main 2-3 lines mein bata dun ki aapke liye kya ban sakta hai?"
        ),
        "Website redesign": (
            "Namaste {name} team, main {sender} se.\n\n"
            "Aapki website dekhi aur ek cheez notice ki: {problem}.\n"
            "Isse aksar enquiries miss ho jaati hain, kyunki zyadatar visitors mobile se aate hain.\n\n"
            "Hum ise bina poori site banaye theek kar sakte hain. "
            "Chaho to main ek free quick audit report bhej dun?"
        ),
        "WhatsApp API": (
            "Namaste {name} team, main {sender} se.\n\n"
            "Hum businesses ke liye WhatsApp Business API platform banate hain, jisse {benefit} "
            "automatic ho jaata hai, wo bhi aapke apne WhatsApp number se.\n\n"
            "Kya main 2 minute ka demo bhej dun? Pasand na aaye to koi baat nahi."
        ),
        "Follow-up (3 din baad)": (
            "Namaste {name} team, pichle message ka follow-up kar raha tha.\n\n"
            "Agar abhi time na ho to koi baat nahi, bas ek line mein bata dijiye "
            "ki aap abhi is par kaam kar rahe hain ya nahi. Main usi hisaab se aage baat karunga.\n\n"
            "- {sender}"
        ),
    }

    names = [n for n in df["name"].tolist() if n]
    pick = st.selectbox("Lead chuno", names)
    r = df[df["name"] == pick].iloc[0]

    # Lead ke type ke hisaab se template apne aap chuno
    problem = (r.get("problem") or "").strip()
    has_site = bool(r["website"]) and not str(r["lead_type"]).startswith("HOT")
    if not has_site:
        auto = "No website"
    elif not problem or problem.startswith("Site theek hai"):
        auto = "WhatsApp API"
    else:
        auto = "Website redesign"

    keys = list(TEMPLATES.keys())
    tpl_name = st.selectbox(
        f"Template (auto-selected: {auto})",
        keys,
        index=keys.index(auto),
        key=f"tpl_{r['place_id']}",  # har lead par default naya set hoga
    )

    default_msg = TEMPLATES[tpl_name].format(
        name=r["name"],
        problem=problem or "kuch improvements ki gunjaish hai",
        benefit=api_benefit(r.get("category", "")),
        sender=SENDER,
    )
    msg = st.text_area("Message (edit kar sakte ho)", default_msg, height=220,
                       key=f"msg_{r['place_id']}_{tpl_name}")

    digits = "".join(ch for ch in str(r["phone"]) if ch.isdigit())
    if digits:
        from urllib.parse import quote

        st.link_button("📲 WhatsApp kholo", f"https://wa.me/91{digits[-10:]}?text={quote(msg)}")
    else:
        st.info("Is lead ka phone number nahi hai.")