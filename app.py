import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_client import supabase

# --- Import modules ---
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news
from scripts.euro_filings_module import push_filings
from scripts.filings import (
    save_or_update_filing,
    process_expired_or_due_filings,
    get_next_filing
)

# --- Page setup ---
st.set_page_config(page_title="📊 Fundamental & Filings Dashboard", layout="wide")
st.title("📊 Fundamental Analysis & Filings Tracker Dashboard")

# --- Sidebar navigation ---
menu = st.sidebar.radio(
    "Navigation",
    ["📈 Fundamental Analysis", "📅 Filings Dashboard", "📜 Filings History"]
)

# ==========================================================
# SECTION 1: 📈 FUNDAMENTAL ANALYSIS
# ==========================================================
if menu == "📈 Fundamental Analysis":
    st.header("📈 Fundamental Analysis & Market Data")

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
    @st.cache_data(ttl=8*60*60)
    def get_fundamentals(ticker, metrics):
        return analyze_ticker(ticker, metrics)

    @st.cache_data(ttl=60*60)
    def get_news(ticker, company_name):
        return push_news(ticker, company_name)

    @st.cache_data(ttl=7*24*60*60)
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

            # --- Tabs for results ---
            tabs = st.tabs(selected_metrics + ["📰 News", "📄 Filings"])
            for idx, metric in enumerate(selected_metrics):
                with tabs[idx]:
                    data = fundamentals.get(metric)
                    if data:
                        st.json(data)
                    else:
                        st.info(f"No data for {metric}")

            # --- News tab ---
            with tabs[len(selected_metrics)]:
                st.subheader("📰 Latest News")
                if news_items:
                    st.dataframe(pd.DataFrame(news_items))
                else:
                    st.info("No news available")

            # --- Filings tab ---
            with tabs[len(selected_metrics) + 1]:
                st.subheader("📄 Latest Filings")
                if filings_items:
                    st.dataframe(pd.DataFrame(filings_items))
                else:
                    st.info("No filings available")

# ==========================================================
# SECTION 2: 📅 FILINGS DASHBOARD
# ==========================================================
elif menu == "📅 Filings Dashboard":
    st.header("📅 Active & Upcoming Filings Tracker")

    # Process expired/due filings
    with st.spinner("Processing expired or due filings..."):
        processed = process_expired_or_due_filings()
    if processed > 0:
        st.success(f"✅ {processed} filing(s) moved to history.")
    else:
        st.info("No filings were due today.")

    # Display next filing
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

    # Active filings table
    st.subheader("🗓️ Active Filings in Database")
    try:
        filings = supabase.table("filings").select("*").order("next_earnings_date", desc=False).execute()
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
        else:
            st.warning("No active filings found.")
    except Exception as e:
        st.error(f"Error fetching filings: {e}")

    st.divider()

    # Add or update filing form
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

# ==========================================================
# SECTION 3: 📜 FILINGS HISTORY
# ==========================================================
elif menu == "📜 Filings History":
    st.header("📜 Filings History Archive")

    try:
        history = (
            supabase.table("filings_history")
            .select("*")
            .order("expected_date", desc=True)
            .limit(100)
            .execute()
        )
        history_data = history.data or []
        if history_data:
            df_history = pd.DataFrame(history_data)
            st.dataframe(
                df_history[
                    [
                        "company_name",
                        "ticker",
                        "event_type",
                        "expected_date",
                        "filing_title",
                        "classification_label",
                        "classification_score",
                        "fetched_from",
                        "run_timestamp",
                        "notes",
                    ]
                ],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No filing history yet.")
    except Exception as e:
        st.error(f"Error loading filing history: {e}")

    st.caption("Past filings automatically archived after due date.")
