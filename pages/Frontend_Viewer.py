import streamlit as st
import pandas as pd
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news

# === Load CSS ===
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === PAGE CONFIG ===
st.set_page_config(page_title="🧭 Frontend Viewer", layout="wide")
st.title("🧭 Company Insights Viewer")
st.markdown("Discover company fundamentals, filings, and curated news in a simple and elegant interface.")

st.divider()

# === INPUT AREA ===
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    company_name = st.text_input("🏢 Company Name (auto-filled if ticker found):").strip()

with col2:
    ticker = st.text_input("🔍 Company Ticker (e.g., AAPL, MTNN, TSLA):").strip()

# Auto-fill company name from Supabase
if ticker and not company_name:
    with st.spinner("🔎 Looking up company name..."):
        res = supabase.table("companies").select("company_name").eq("ticker", ticker.upper()).execute()
        if res.data:
            company_name = res.data[0]["company_name"]
            st.session_state["company_name"] = company_name
            st.success(f"✅ Found company: {company_name}")
        else:
            st.warning("⚠️ Company name not found for this ticker. Please type manually.")

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    run_analysis = st.button("🚀 Run Analysis", use_container_width=True)

# === METRIC SELECTION ===
with st.expander("⚙️ Select Metrics to Analyze"):
    metrics = st.multiselect(
        "Choose metrics:",
        [
            "valuation",
            "profitability",
            "growth",
            "balance",
            "cashflow",
            "dividends",
            "recommendations",
        ],
        default=["valuation", "profitability", "growth"]
    )

# === Column Rename Map (for Supabase tables) ===
column_rename_map = {
    "filing_title": "Filing Title",
    "filing_type": "Filing Type",
    "filing_date": "Filing Date",
    "filing_summary": "Summary",
    "next_earnings_date": "Next Filing Date",
    "previous_earnings_date": "Previous Filing Date",
    "classification_label": "Classification",
    "classification_score": "Confidence",
    "expected_date": "Expected Date",
    "event_type": "Event Type"
}

# === MAIN EXECUTION ===
if run_analysis and ticker and company_name:
    try:
        with st.spinner(f"Fetching insights for {company_name} ({ticker})..."):
            fundamentals = analyze_ticker(ticker, metrics)
            news_items = push_news(company_name, ticker)

        st.success(f"✅ Analysis complete for {company_name} ({ticker})")

        # === Tabs Layout ===
        overview_tab, filings_tab, history_tab, news_tab = st.tabs(
            ["📊 Overview", "📂 Filings", "🕘 History", "🌍 News"]
        )

        # --------------------------------------------------------------------
        # TAB 1 — OVERVIEW
        # --------------------------------------------------------------------
        with overview_tab:
            st.header(f"📊 Fundamentals — {company_name}")
            for metric in metrics:
                data = fundamentals.get(metric, {})
                if not data:
                    continue

                st.subheader(metric.capitalize())
                if isinstance(data, dict):
                    items = list(data.items())
                    for i in range(0, len(items), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(items):
                                key, value = items[i + j]
                                cols[j].markdown(
                                    f"""
                                    <div class="metric-card">
                                        <div class="metric-key">{key.replace('_', ' ').title()}</div>
                                        <div class="metric-value">{value}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                elif isinstance(data, pd.DataFrame):
                    st.dataframe(data, use_container_width=True)
                else:
                    st.write(data)

        # --------------------------------------------------------------------
        # TAB 2 — FILINGS
        # --------------------------------------------------------------------
        with filings_tab:
            st.header(f"📂 Recent Filings — {company_name}")
            filings = supabase.table("filings").select("*").eq("ticker", ticker).execute()

            if filings.data:
                filings_df = pd.DataFrame(filings.data)
                filings_df.rename(columns=column_rename_map, inplace=True)
                filings_df = filings_df.sort_values(by="Next Filing Date", ascending=False)

                for _, row in filings_df.iterrows():
                    st.markdown(f"""
                    <div class="filing-card">
                        <div class="filing-title">{row.get('Filing Title', 'Untitled')}</div>
                        <p><strong>Type:</strong> {row.get('Filing Type', 'N/A')}<br>
                        <strong>Date:</strong> {row.get('Filing Date', 'N/A')}<br>
                        <strong>Next Filing:</strong> {row.get('Next Filing Date', 'N/A')}<br>
                        <strong>Previous Filing:</strong> {row.get('Previous Filing Date', 'N/A')}</p>
                        <p>{row.get('Summary', 'No summary available')}</p>
                        <a href="{row.get('filing_url', '#')}" target="_blank">🔗 View Full Filing</a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No filings found for this company.")

        # --------------------------------------------------------------------
        # TAB 3 — HISTORY
        # --------------------------------------------------------------------
        with history_tab:
            st.header(f"🕘 Filing History — {company_name}")
            history = supabase.table("filings_history").select("*").eq("ticker", ticker).execute()
            if history.data:
                df_history = pd.DataFrame(history.data)
                df_history.rename(columns=column_rename_map, inplace=True)
                st.dataframe(df_history, use_container_width=True, hide_index=True)
            else:
                st.info("No filing history found.")

        # --------------------------------------------------------------------
        # TAB 4 — NEWS
        # --------------------------------------------------------------------
        with news_tab:
            st.header(f"🌍 Latest News — {company_name}")
            if news_items:
                for news in news_items:
                    st.markdown(f"""
                    <div class="news-card">
                        <div class="news-header">
                            <h4>{news.get('title', 'Untitled')}</h4>
                            <p class="news-meta">🗓️ {news.get('published_date', 'N/A')}</p>
                        </div>
                        <p>{news.get('summary', 'No summary available')}</p>
                        <a href="{news.get('url', '#')}" target="_blank">🔗 Read full article →</a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent news found for this company.")

    except Exception as e:
        st.error(f"❌ Error: {e}")

else:
    st.info("Enter both the **Company Name** and **Ticker**, select metrics, then click **Run Analysis**.")
