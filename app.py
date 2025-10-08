import streamlit as st
import pandas as pd
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news
#from scripts.euro_filings_module import push_filings
from datetime import datetime, timezone

# --- Page setup ---
st.set_page_config(page_title="📊 Fundamental Analysis Dashboard", layout="wide")
st.title("📊 Fundamental Analysis Dashboard")

# --- Fetch tickers & companies ---
companies_data = supabase.table("companies").select("ticker, company_name").execute()
companies_df = pd.DataFrame(companies_data.data or [])
tickers = sorted(companies_df['ticker'].tolist()) if not companies_df.empty else []
company_names = sorted(companies_df['company_name'].tolist()) if not companies_df.empty else []

# --- Sidebar filters ---
st.sidebar.header("⚙️ Filters")
ticker_choice = st.sidebar.selectbox("Select a Company Ticker", options=tickers)
company_choice = st.sidebar.selectbox("Select Company Name", options=company_names)

metrics_options = [
    "valuation", "profitability", "growth", "balance", 
    "cashflow", "dividends", "recommendations"
]
selected_metrics = st.sidebar.multiselect(
    "Select Metrics to Display", options=metrics_options, default=metrics_options
)

# --- Cached data ---
@st.cache_data(ttl=8*60*60)  # 8 hours
def get_fundamentals(ticker, metrics):
    return analyze_ticker(ticker, metrics)

@st.cache_data(ttl=60*60)  # 1 hour
def get_news(ticker, company_name):
    return push_news(ticker, company_name)

@st.cache_data(ttl=7*24*60*60)  # 1 week
def get_filings(ticker, company_name):
    return push_filings(ticker, company_name)

# --- Fetch & display ---
if st.sidebar.button("Fetch & Analyze"):
    if not ticker_choice or not company_choice:
        st.warning("Please select both ticker and company.")
    else:
        with st.spinner("Fetching fundamentals..."):
            fundamentals = get_fundamentals(ticker_choice, selected_metrics)
        with st.spinner("Fetching news..."):
            news_items = get_news(ticker_choice, company_choice)
        with st.spinner("Fetching filings..."):
            filings_items = get_filings(ticker_choice, company_choice)

        st.success(f"✅ Data fetched for {ticker_choice} ({company_choice})")

        # --- Metrics tabs ---
        tabs = st.tabs(selected_metrics + ["News", "Filings"])
        for idx, metric in enumerate(selected_metrics):
            with tabs[idx]:
                data = fundamentals.get(metric)
                if data:
                    st.json(data)
                else:
                    st.info(f"No data for {metric}")

        # --- News tab ---
        with tabs[len(selected_metrics)]:
            if news_items:
                st.dataframe(pd.DataFrame(news_items))
            else:
                st.info("No news available")

        # --- Filings tab ---
        with tabs[len(selected_metrics)+1]:
            if filings_items:
                st.dataframe(pd.DataFrame(filings_items))
            else:
                st.info("No filings available")

# --- Optional: Show all companies ---
if st.checkbox("Show All Companies"):
    st.dataframe(companies_df)
