import streamlit as st
import pandas as pd
from supabase_client import supabase
from scripts.supabase_analysis import analyze_ticker  # Modular analysis script
from scripts.euro_news import push_news_to_supabase, fetch_news_with_fallback
from scripts.euro_filings import push_filings, fetch_filings_from_google_news

# --- Page setup ---
st.set_page_config(page_title="📊 Fundamental Analysis Dashboard", layout="wide")
st.title("📊 Fundamental Analysis Dashboard")

# --- Fetch all tickers and companies for dropdowns ---
@st.cache_data(ttl=3600)
def get_companies():
    companies_data = supabase.table("companies").select("ticker, company_name").execute()
    return pd.DataFrame(companies_data.data or [])

companies_df = get_companies()
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

# --- Cache ticker analysis to reduce repeated API calls ---
@st.cache_data(ttl=1800, show_spinner=False)
def get_analysis(ticker, metrics):
    return analyze_ticker(ticker, metrics)

# --- Cache news to reduce repeated API calls ---
@st.cache_data(ttl=1800, show_spinner=False)
def get_news(ticker, company_name):
    return fetch_news_with_fallback(ticker, company_name)

# --- Cache filings ---
@st.cache_data(ttl=1800, show_spinner=False)
def get_filings(ticker, company_name):
    return fetch_filings_from_google_news(company_name)

# --- Fetch & Analyze button ---
if st.sidebar.button("Fetch & Analyze"):
    if not ticker_choice or not company_choice:
        st.warning("Please select both ticker and company.")
    else:
        with st.spinner(f"Fetching data for {ticker_choice}..."):
            analysis_results = get_analysis(ticker_choice, selected_metrics)
            news_results = get_news(ticker_choice, company_choice)
            filings_results = get_filings(ticker_choice, company_choice)

        st.success(f"✅ Data fetched for {ticker_choice} ({company_choice})")

        # --- Display metrics in tabs ---
        metric_tabs = st.tabs(selected_metrics + ["News", "Filings"])
        for idx, metric in enumerate(selected_metrics):
            with metric_tabs[idx]:
                data = analysis_results.get(metric)
                if data:
                    if isinstance(data, list):  # e.g., recommendations
                        st.dataframe(pd.DataFrame(data))
                    else:
                        st.json(data)
                else:
                    st.info(f"No data available for {metric}")

        # --- News tab ---
        with metric_tabs[len(selected_metrics)]:
            if news_results:
                st.subheader("📰 Recent News")
                st.dataframe(pd.DataFrame(news_results))
            else:
                st.info("No recent news found.")

        # --- Filings tab ---
        with metric_tabs[len(selected_metrics) + 1]:
            if filings_results:
                st.subheader("📄 Recent Filings")
                st.dataframe(pd.DataFrame(filings_results))
            else:
                st.info("No recent filings found.")

# --- Optional: show company table ---
if st.checkbox("Show All Companies"):
    st.dataframe(companies_df)
