import os
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

# ======================================
# 📥 Fetch or simulate filings
# ======================================
def fetch_upcoming_filings():
    """
    Simulated function — replace later with your live classification pipeline.
    """
    return [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "event_type": "filing",
            "expected_date": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
            "filing_url": "https://investor.apple.com/news",
            "filing_title": "Apple Announces Q4 2025 Earnings Date",
            "filing_summary": "Apple will report Q4 results on November 16, 2025.",
            "filing_text": "",
            "classification_label": "financial",
            "classification_score": 0.98,
            "fetched_from": "google_news",
            "notes": "Initial pipeline entry."
        },
        {
            "ticker": "MSFT",
            "company_name": "Microsoft Corp.",
            "event_type": "filing",
            "expected_date": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "filing_url": "https://www.microsoft.com/investor",
            "filing_title": "Microsoft Earnings Call Scheduled for Oct 11",
            "filing_summary": "Microsoft will hold its quarterly call on Oct 11, 2025.",
            "filing_text": "",
            "classification_label": "financial",
            "classification_score": 0.95,
            "fetched_from": "company_site",
            "notes": "Initial pipeline entry."
        }
    ]

# ======================================
# 📤 Push filings to Supabase
# ======================================
def push_to_filings_history(entries):
    try:
        for entry in entries:
            supabase.table("filings_history").insert(entry).execute()
        print("✅ Filings successfully pushed to Supabase.")
    except Exception as e:
        print("❌ Error pushing filings to Supabase:", e)

# ======================================
# 🔍 Check for due filings
# ======================================
def check_due_filings():
    """Check if today matches any filing date."""
    today = datetime.now(timezone.utc).date()
    try:
        res = supabase.table("filings_history").select("*").execute()
        due_today = [f for f in res.data if datetime.fromisoformat(f["expected_date"]).date() == today]
        return due_today
    except Exception as e:
        print("⚠️ Could not check due filings:", e)
        return []

# ======================================
# 🖥️ Streamlit Dashboard
# ======================================
st.set_page_config(page_title="Filings Dashboard", page_icon="📊", layout="wide")

st.title("📅 Upcoming Financial Filings Dashboard")

# -- Section 1: Upcoming filings
st.header("🕓 Upcoming Filings")

try:
    filings = supabase.table("filings_history").select("*").order("expected_date", desc=False).execute()
    filings_data = filings.data or []
except Exception as e:
    st.error(f"❌ Error loading filings: {e}")
    filings_data = []

if not filings_data:
    st.info("No upcoming filings yet. Run the pipeline to add some.")
else:
    for f in filings_data:
        st.subheader(f"{f['company_name']} ({f['ticker']})")
        st.write(f"**Type:** {f.get('event_type', '-')}")
        st.write(f"**Expected Date:** {f.get('expected_date', '-')}")
        st.write(f"**Source:** {f.get('fetched_from', '-')}")
        st.write(f"**Title:** {f.get('filing_title', '-')}")
        st.write(f"**Summary:** {f.get('filing_summary', '-')}")
        st.markdown(f"[View Source]({f.get('filing_url', '#')})")
        st.divider()

# -- Section 2: Due today alerts
due_today = check_due_filings()
if due_today:
    st.header("🚨 Filings Due Today")
    for d in due_today:
        st.warning(f"**{d['company_name']} ({d['ticker']})** — Filing expected today!")
else:
    st.header("✅ No filings due today.")

# ======================================
# 🧩 Developer/Local Mode
# ======================================
if st.button("🧠 Run Once & Push Sample Filings"):
    new_entries = fetch_upcoming_filings()
    push_to_filings_history(new_entries)
    st.success("✅ Sample filings added to Supabase. Refresh to see updates.")
