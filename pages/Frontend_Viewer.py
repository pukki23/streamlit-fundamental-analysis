import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_client import supabase
from scripts.scraper import find_and_extract_latest_filing

# === Load Custom CSS ===
def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

st.set_page_config(page_title="🖥️ Frontend Viewer", layout="wide")
st.title("🖥️ Filings & Insights — End User View")

# ==========================================================
# Section 1: View Latest Filing
# ==========================================================
st.header("📰 Fetch & View Latest Filing")

company_name = st.text_input("Enter Company Name")
ticker = st.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT)").upper().strip()

if st.button("Fetch Latest Filing"):
    if not company_name or not ticker:
        st.warning("Please provide both company name and ticker.")
    else:
        with st.spinner("Fetching latest filing/news..."):
            filing_data = find_and_extract_latest_filing(company_name)

            if filing_data:
                st.success("✅ Filing/news found and extracted!")

                st.markdown(f"""
                <div class="filing-card">
                    <div class="filing-title">{filing_data['filing_title']}</div>
                    <p class="filing-meta"><strong>Company:</strong> {company_name} ({ticker})</p>
                    <p class="filing-meta"><strong>Source:</strong> {filing_data['fetched_from']}</p>
                    <p>{filing_data['filing_summary']}</p>
                    <a href="{filing_data['filing_url']}" target="_blank">🔗 View Original Filing</a>
                </div>
                """, unsafe_allow_html=True)

                st.subheader("📜 Extracted Filing Text (Preview)")
                st.write(filing_data['filing_text'][:2000] + "..." if filing_data['filing_text'] else "No text extracted.")

                # Save filing to Supabase
                supabase.table("filings_history").insert({
                    "ticker": ticker,
                    "company_name": company_name,
                    "event_type": "earning",
                    "expected_date": datetime.now().isoformat(),
                    "filing_url": filing_data["filing_url"],
                    "filing_title": filing_data["filing_title"],
                    "filing_summary": filing_data["filing_summary"],
                    "filing_text": filing_data["filing_text"],
                    "classification_label": None,
                    "classification_score": None,
                    "fetched_from": filing_data["fetched_from"],
                    "run_timestamp": datetime.now().isoformat(),
                    "notes": None,
                }).execute()

                st.info("Saved successfully to filings_history table.")
            else:
                st.error("No recent filing found for this company.")

# ==========================================================
# Section 2: View Filing History
# ==========================================================
st.header("📜 Recent Filings History")

try:
    history = (
        supabase.table("filings_history")
        .select("*")
        .order("expected_date", desc=True)
        .limit(50)
        .execute()
    )
    history_data = history.data or []
    if history_data:
        for row in history_data:
            st.markdown(f"""
            <div class="filing-card">
                <div class="filing-title">{row['filing_title']}</div>
                <p class="filing-meta"><strong>{row['company_name']}</strong> ({row['ticker']}) — {row['event_type']}</p>
                <p>{row['filing_summary'][:250] if row['filing_summary'] else ''}...</p>
                <a href="{row['filing_url']}" target="_blank">🔗 View Filing</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No filing history yet.")
except Exception as e:
    st.error(f"Error loading filing history: {e}")
