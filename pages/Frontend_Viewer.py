import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_client import supabase
from scripts.scraper import find_and_extract_latest_filing
from pathlib import Path

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🖥️ Frontend Viewer", layout="wide")

# =============================
# LOAD CSS
# =============================
def load_css():
    css_path = Path("assets/style.css")
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

# =============================
# THEME TOGGLE (fixed bug)
# =============================
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

def toggle_theme():
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"
    st.rerun()

icon = "🌙" if st.session_state["theme"] == "light" else "🌞"
st.markdown(f"""
<div class='theme-toggle' onclick='window.location.reload()' title='Toggle Theme'>{icon}</div>
""", unsafe_allow_html=True)

# =============================
# HEADER
# =============================
st.markdown("""
<div class='landing-container'>
    <h1>🖥️ Filings & Insights — End User View</h1>
    <p>Search, explore, and review the latest company filings and summaries in a clean interface.</p>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# SECTION 1: FETCH LATEST FILING
# ==========================================================
st.header("📰 Fetch & View Latest Filing")

col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input("Enter Company Name")
with col2:
    ticker = st.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT)").upper().strip()

if st.button("🔍 Fetch Latest Filing"):
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
                filing_text = filing_data.get("filing_text", "")
                if filing_text:
                    st.write(filing_text[:2000] + "..." if len(filing_text) > 2000 else filing_text)
                else:
                    st.info("No text extracted.")

                # Save filing to Supabase
                supabase.table("filings_history").insert({
                    "ticker": ticker,
                    "company_name": company_name,
                    "event_type": "earning",
                    "expected_date": datetime.now().isoformat(),
                    "filing_url": filing_data.get("filing_url"),
                    "filing_title": filing_data.get("filing_title"),
                    "filing_summary": filing_data.get("filing_summary"),
                    "filing_text": filing_text,
                    "classification_label": None,
                    "classification_score": None,
                    "fetched_from": filing_data.get("fetched_from"),
                    "run_timestamp": datetime.now().isoformat(),
                    "notes": None,
                }).execute()

                st.info("Saved successfully to filings_history table.")
            else:
                st.error("No recent filing found for this company.")

# ==========================================================
# SECTION 2: VIEW FILING HISTORY
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
                <div class="filing-title">{row.get('filing_title', 'Untitled Filing')}</div>
                <p class="filing-meta"><strong>{row.get('company_name', '')}</strong> ({row.get('ticker', '')}) — {row.get('event_type', '')}</p>
                <p>{(row.get('filing_summary') or '')[:250]}...</p>
                <a href="{row.get('filing_url', '#')}" target="_blank">🔗 View Filing</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No filing history yet.")
except Exception as e:
    st.error(f"Error loading filing history: {e}")
