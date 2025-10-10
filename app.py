import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_client import supabase

# --- Import modules ---
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news
from scripts.filings import (
    save_or_update_filing,
    process_expired_or_due_filings,
    get_next_filing,
)
# Import scraper
from script.scraper import find_and_extract_latest_filing

# --- Page setup ---
st.set_page_config(page_title="📊 Fundamental & Filings Dashboard", layout="wide")
st.title("📊 Fundamental Analysis & Filings Tracker Dashboard")

# --- Sidebar navigation ---
menu = st.sidebar.radio(
    "Navigation",
    [
        "📈 Fundamental Analysis",
        "📅 Filings Dashboard",
        "📜 Filings History",
        "📰 Fetch Latest Filing"
    ]
)

# ==========================================================
# SECTION 1: 📈 FUNDAMENTAL ANALYSIS
# ==========================================================
if menu == "📈 Fundamental Analysis":
    st.header("📈 Fundamental Analysis & Market Data")

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
# SECTION 2: 📅 FILINGS DASHBOARD
# ==========================================================
elif menu == "📅 Filings Dashboard":
    st.header("📅 Active & Upcoming Filings Tracker")

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

    st.subheader("🗓️ Active Filings in Database")
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
            csv_hist = df_history.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Filings History CSV",
                data=csv_hist,
                file_name="filings_history.csv",
                mime="text/csv",
            )
        else:
            st.info("No filing history yet.")
    except Exception as e:
        st.error(f"Error loading filing history: {e}")

    st.caption("Past filings automatically archived after due date.")

# ==========================================================
# SECTION 4: 📰 FETCH LATEST FILING (SCRAPER INTEGRATION)
# ==========================================================
elif menu == "📰 Fetch Latest Filing":
    st.header("📰 Fetch Latest Filing (Scraper Integration)")

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
                    st.write(f"### 🧾 Title\n{filing_data['filing_title']}")
                    st.write(f"### 🔗 URL\n{filing_data['filing_url']}")
                    st.write(f"### 📝 Summary\n{filing_data['filing_summary']}")
                    st.write(f"### 📜 Extracted Text")
                    st.write(filing_data['filing_text'][:2000] + "..." if filing_data['filing_text'] else "No text extracted.")

                    # Save to Supabase filings_history
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
