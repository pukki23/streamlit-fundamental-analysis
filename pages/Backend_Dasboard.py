import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_client import supabase

# === Load Custom CSS ===
def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# --- Import modules ---
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news
from scripts.filings import (
    save_or_update_filing,
    process_expired_or_due_filings,
    get_next_filing,
)

# --- PAGE CONFIG ---
st.set_page_config(page_title="📊 Backend Dashboard", layout="wide")
st.title("📊 Backend — Fundamental & Filings Management")

# ==========================================================
# FUNDAMENTAL ANALYSIS (Admin Mode)
# ==========================================================
st.header("📈 Fundamental Analysis (Backend View)")

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

if st.sidebar.button("Fetch & Analyze"):
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
# FILINGS DASHBOARD (Admin Mode)
# ==========================================================
st.header("📅 Filings Dashboard (Backend)")

with st.spinner("Processing expired or due filings..."):
    processed = process_expired_or_due_filings()
if processed > 0:
    st.success(f"✅ {processed} filing(s) moved to history.")
else:
    st.info("No filings were due today.")

st.subheader("⏭️ Next Expected Filing")
next_filing = get_next_filing()
if next_filing:
    st.write(f"**Company:** {next_filing['company_name']} ({next_filing['ticker']})")
    st.write(f"**Expected Date:** {next_filing['next_earnings_date']}")
    st.write(f"**Pending:** {'✅ Yes' if next_filing['pending_filing'] else '❌ No'}")
    st.write(f"**Source:** {next_filing.get('filing_source', 'N/A')}")
else:
    st.info("No upcoming filings found.")

st.divider()

# --- Active filings table ---
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

# --- Add or update filing form ---
st.subheader("➕ Add or Update Filing")
with st.form("add_filing_form"):
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("Ticker (e.g., AAPL)", "").strip().upper()
        company = st.text_input("Company Name", "").strip()
    with col2:
        date = st.date_input("Next Filing Date", datetime.now().date())
        source = st.text_input("Source", "manual")

    submit = st.form_submit_button("Save Filing")

    if submit:
        if ticker and company:
            result = save_or_update_filing(ticker, company, date.isoformat(), source)
            st.success(f"✅ Filing {result} successfully.")
        else:
            st.warning("Please fill both ticker and company name.")
