import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_client import supabase
from pathlib import Path

# === PAGE CONFIG ===
st.set_page_config(page_title="📊 Backend Dashboard", layout="wide")

# === LOAD CSS ===
def load_css():
    css_path = Path("assets/style.css")
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

# === THEME TOGGLE (fixed) ===
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

def toggle_theme():
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"
    st.rerun()

icon = "🌙" if st.session_state["theme"] == "light" else "🌞"
st.markdown(f"""
<div class='theme-toggle' onclick='window.location.reload()' title='Toggle Theme'>{icon}</div>
""", unsafe_allow_html=True)

# === IMPORT MODULES ===
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news
from scripts.filings import (
    save_or_update_filing,
    process_expired_or_due_filings,
    get_next_filing,
)

# === HEADER ===
st.markdown("""
<div class='landing-container'>
    <h1>📊 Backend — Fundamental & Filings Management</h1>
    <p>Admin view for analyzing fundamentals, managing filings, and running backend processes.</p>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# FUNDAMENTAL ANALYSIS
# ==========================================================
st.header("📈 Fundamental Analysis")

companies_data = supabase.table("companies").select("ticker, company_name").execute()
companies_df = pd.DataFrame(companies_data.data or [])

tickers = sorted(companies_df["ticker"].tolist()) if not companies_df.empty else []
company_names = sorted(companies_df["company_name"].tolist()) if not companies_df.empty else []

st.sidebar.header("⚙️ Filters")
ticker_choice = st.sidebar.selectbox("Select a Company Ticker", options=tickers)
company_choice = st.sidebar.selectbox("Select Company Name", options=company_names)

metrics_options = [
    "valuation",
    "profitability",
    "growth",
    "balance",
    "cashflow",
    "dividends",
    "recommendations",
]
selected_metrics = st.sidebar.multiselect(
    "Select Metrics to Display", options=metrics_options, default=metrics_options
)

@st.cache_data(ttl=8 * 60 * 60)
def get_fundamentals(ticker, metrics):
    return analyze_ticker(ticker, metrics)

@st.cache_data(ttl=60 * 60)
def get_news(ticker, company_name):
    return push_news(ticker, company_name)

if st.sidebar.button("🔍 Fetch & Analyze"):
    if not ticker_choice or not company_choice:
        st.warning("Please select both ticker and company.")
    else:
        with st.spinner("Fetching fundamentals..."):
            fundamentals = get_fundamentals(ticker_choice, selected_metrics)
        with st.spinner("Fetching news..."):
            news_items = get_news(ticker_choice, company_choice)

        st.success(f"✅ Data fetched for {ticker_choice} ({company_choice})")

        tabs = st.tabs(selected_metrics + ["📰 News"])
        for idx, metric in enumerate(selected_metrics):
            with tabs[idx]:
                data = fundamentals.get(metric)
                if data:
                    st.json(data)
                else:
                    st.info(f"No data for {metric}")

        with tabs[len(selected_metrics)]:
            st.subheader("📰 Latest News")
            if news_items:
                st.dataframe(pd.DataFrame(news_items))
            else:
                st.info("No news available")

# ==========================================================
# FILINGS DASHBOARD
# ==========================================================
st.header("📅 Filings Dashboard")

with st.spinner("Processing expired or due filings..."):
    processed = process_expired_or_due_filings()
if processed > 0:
    st.success(f"✅ {processed} filing(s) moved to history.")
else:
    st.info("No filings were due today.")

st.subheader("⏭️ Next Expected Filing")
next_filing = get_next_filing()
if next_filing:
    st.markdown(f"""
    <div class="filing-card">
        <div class="filing-title">{next_filing['company_name']} ({next_filing['ticker']})</div>
        <p><strong>Expected Date:</strong> {next_filing['next_earnings_date']}</p>
        <p><strong>Pending:</strong> {'✅ Yes' if next_filing['pending_filing'] else '❌ No'}</p>
        <p><strong>Source:</strong> {next_filing.get('filing_source', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No upcoming filings found.")

st.divider()

# --- ACTIVE FILINGS ---
st.subheader("🗓️ Active Filings")
try:
    filings = (
        supabase.table("filings")
        .select("*")
        .order("next_earnings_date", desc=False)
        .execute()
    )
    filings_data = filings.data or []
    if filings_data:
        df_filings = pd.DataFrame(filings_data)
        st.dataframe(
            df_filings[
                [
                    "company_name",
                    "ticker",
                    "next_earnings_date",
                    "pending_filing",
                    "filing_source",
                    "last_checked",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )
        csv = df_filings.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Active Filings CSV",
            data=csv,
            file_name="active_filings.csv",
            mime="text/csv",
        )
    else:
        st.warning("No active filings found.")
except Exception as e:
    st.error(f"Error fetching filings: {e}")

st.divider()

# --- ADD/UPDATE FILING FORM ---
st.subheader("➕ Add or Update Filing")
with st.form("add_filing_form"):
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("Ticker (e.g., AAPL)", "").strip().upper()
        company = st.text_input("Company Name", "").strip()
    with col2:
        date = st.date_input("Next Filing Date", datetime.now().date())
        source = st.text_input("Source", "manual")

    submit = st.form_submit_button("💾 Save Filing")

    if submit:
        if ticker and company:
            result = save_or_update_filing(ticker, company, date.isoformat(), source)
            st.success(f"✅ Filing {result} successfully.")
        else:
            st.warning("Please fill both ticker and company name.")
