"""
Outreach templates and benefit mapping for WhatsApp communication.
Provides templates in English and Hinglish with language-aware category benefits.
"""

from typing import Dict

TEMPLATES: Dict[str, Dict[str, str]] = {
    "English": {
        "No website": (
            "Hello {name} team, this is {sender}.\n\n"
            "I came across {name} on Google Maps and noticed you do not have an active website yet. "
            "Most customers check online before visiting, so businesses without a site often miss out on new inquiries.\n\n"
            "We build clean, fast websites with direct WhatsApp booking. "
            "Could I share a quick 2-minute preview of how it would look?"
        ),
        "Website redesign": (
            "Hello {name} team, this is {sender}.\n\n"
            "I reviewed your website and noticed an issue: {problem}. "
            "Since most visitors browse on smartphones today, this could lead to lost inquiries.\n\n"
            "We fix these issues quickly without rebuilding your entire website from scratch. "
            "Would you be open to a quick, free audit report?"
        ),
        "WhatsApp API": (
            "Hello {name} team, this is {sender}.\n\n"
            "We set up WhatsApp Business automation for businesses like yours to handle "
            "{benefit} automatically from your own WhatsApp number.\n\n"
            "Could I share a quick 2-minute demo? Absolutely no pressure if you are not interested right now."
        ),
        "Follow-up (after 3 days)": (
            "Hello {name} team, just following up on my previous message.\n\n"
            "No worries at all if you are busy. Just wanted to see if upgrading your online presence "
            "or WhatsApp workflow is on your radar this month.\n\n"
            "Best regards,\n{sender}"
        ),
        "Final nudge (after 7 days)": (
            "Hello {name} team, one last check-in from my side.\n\n"
            "I understand you might have other priorities right now, so I will not follow up again. "
            "If you ever need help with web design or WhatsApp automation, feel free to reach out anytime!\n\n"
            "Best regards,\n{sender}"
        ),
    },
    "Hinglish": {
        "No website": (
            "Namaste {name} team, main {sender} se.\n\n"
            "Maine Google par {name} dekha, par online koi active website nahi mili. "
            "Aaj kal zyadatar customers pehle online search karte hain aur website na milne par "
            "dusre option par chale jaate hain.\n\n"
            "Hum local businesses ke liye clean aur fast website banate hain (direct WhatsApp button ke saath). "
            "Kya main 2 minute mein ek sample preview share karun?"
        ),
        "Website redesign": (
            "Namaste {name} team, main {sender} se.\n\n"
            "Aapki website dekhi aur ek issue notice kiya: {problem}.\n"
            "Zyadatar log mobile se browse karte hain, isliye kai enquiries miss ho sakti hain.\n\n"
            "Hum ise bina poori site dobara banaye aasani se fix kar sakte hain. "
            "Kya main aapko ek free quick audit report bhej dun?"
        ),
        "WhatsApp API": (
            "Namaste {name} team, main {sender} se.\n\n"
            "Hum local businesses ke liye WhatsApp Business platform set up karte hain, "
            "jisse {benefit} aapke apne WhatsApp number se automatic ho jaata hai.\n\n"
            "Kya main 2 minute ka demo bhej dun? Agar pasand na aaye toh koi baat nahi."
        ),
        "Follow-up (after 3 days)": (
            "Namaste {name} team, pichle message ke regarding follow-up kar raha tha.\n\n"
            "Agar abhi time na ho toh koi baat nahi, bas bata dijiye ki aap abhi is par plan kar rahe hain ya nahi. "
            "Main usi hisaab se connect karunga.\n\n"
            "- {sender}"
        ),
        "Final nudge (after 7 days)": (
            "Namaste {name} team, meri taraf se ek aakhri quick follow-up.\n\n"
            "Main samajh sakta hu aap busy honge, isliye ab dobara follow-up nahi karunga. "
            "Agar future mein website upgrade ya WhatsApp automation ki zaroorat ho, toh aap kabhi bhi connect kar sakte hain.\n\n"
            "- {sender}"
        ),
    },
}


def api_benefit(category: str, language: str = "English") -> str:
    """Return tailored business automation benefits in English or Hinglish."""
    c = (category or "").lower()
    is_hi = language.lower() == "hinglish"

    if any(k in c for k in ("coaching", "school", "institute", "academy", "tuition", "college", "classes")):
        return (
            "admission enquiries ka auto-reply, fees reminder aur batch updates"
            if is_hi
            else "instant admission inquiries, fee reminders, and batch schedule updates"
        )
    if any(k in c for k in ("clinic", "hospital", "doctor", "dental", "pathology", "lab", "health")):
        return (
            "appointment booking, reminders aur report updates"
            if is_hi
            else "automated appointment bookings, patient reminders, and lab report delivery"
        )
    if any(k in c for k in ("restaurant", "cafe", "bakery", "food", "sweet", "hotel")):
        return (
            "order updates, offers aur repeat customers ko bulk messages"
            if is_hi
            else "order confirmations, menu sharing, and special offers to repeat diners"
        )
    if any(k in c for k in ("real estate", "property", "builder", "realtor")):
        return (
            "enquiry ka turant reply aur site-visit follow-ups"
            if is_hi
            else "instant inquiry responses and site-visit scheduling"
        )
    if any(k in c for k in ("shop", "store", "boutique", "showroom", "fashion", "retail")):
        return (
            "catalog sharing, order updates aur festival broadcast"
            if is_hi
            else "product catalog sharing, order tracking, and seasonal promotional alerts"
        )

    return (
        "customer enquiries ka auto-reply aur follow-up messages"
        if is_hi
        else "automated customer inquiry responses and smart follow-ups"
    )


def format_message(
    template: str,
    name: str,
    sender: str,
    problem: str = "",
    benefit: str = "",
) -> str:
    """Format outreach template string safely without missing key errors."""
    clean_name = (name or "there").strip()
    clean_sender = (sender or "Appnix Technologies").strip()
    clean_problem = (problem or "").strip()
    clean_benefit = (benefit or "").strip()

    return template.format(
        name=clean_name,
        sender=clean_sender,
        problem=clean_problem,
        benefit=clean_benefit,
    )
