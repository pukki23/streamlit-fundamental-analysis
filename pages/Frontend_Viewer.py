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
st.markdown("Explore company fundamentals, filings, and global news in a clean, user-friendly interface.")

# === INPUT AREA ===
st.divider()
col1, col2 = st.columns([2, 1])
with col1:
    ticker = st.text_input("🔍 Enter Company Ticker (e.g., AAPL, MSFT, MTN):").strip()
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    run_analysis = st.button("🚀 Run Analysis", use_container_width=True)

# === METRICS SELECTION ===
with st.expander("⚙️ Select Metrics to Analyze"):
    metrics = st.multiselect(
        "Choose metrics to analyze:",
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

# =====================================================================
# MAIN LOGIC
# =====================================================================
if run_analysis and ticker:
    try:
        with st.spinner(f"Fetching data for {ticker}..."):
            results = analyze_ticker(ticker, metrics)

        if not results:
            st.warning("No analysis results found.")
        else:
            st.success(f"✅ Analysis complete for {ticker}!")

            # ==========================================================
            # SECTION 1: FUNDAMENTAL ANALYSIS
            # ==========================================================
            st.header("📊 Fundamental Analysis")

            for metric in metrics:
                data = results.get(metric, {})
                if not data:
                    continue

                st.markdown(f"### {metric.capitalize()}")

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

            # ==========================================================
            # SECTION 2: FILINGS (without scraper)
            # ==========================================================
            st.divider()
            st.header("📂 Latest Company Filings")

            filings = supabase.table("filings").select("*").eq("ticker", ticker).execute()
            if filings.data:
                filings_df = pd.DataFrame(filings.data)
                filings_df = filings_df.sort_values(by="next_earnings_date", ascending=False)

                for _, row in filings_df.iterrows():
                    st.markdown(f"""
                    <div class="filing-card">
                        <div class="filing-title">{row.get('filing_title', 'Untitled')}</div>
                        <p class="filing-meta">
                            <strong>Filing Type:</strong> {row.get('filing_type', 'N/A')}<br>
                            <strong>Next Filing Date:</strong> {row.get('next_earnings_date', 'N/A')}<br>
                            <strong>Previous Filing Date:</strong> {row.get('previous_earnings_date', 'N/A')}
                        </p>
                        <p>{row.get('filing_summary', 'No summary available')}</p>
                        <a href="{row.get('filing_url', '#')}" target="_blank">🔗 View Full Filing</a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent filings found for this company.")

            # ==========================================================
            # SECTION 3: FILING HISTORY (table only)
            # ==========================================================
            st.divider()
            st.header("🕘 Filing History")

            filing_history = supabase.table("filings_history").select("*").eq("ticker", ticker).execute()
            if filing_history.data:
                df_history = pd.DataFrame(filing_history.data)
                df_history = df_history.sort_values(by="expected_date", ascending=False)
                st.dataframe(
                    df_history[
                        ["event_type", "filing_title", "expected_date", "classification_label", "classification_score"]
                    ],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No filing history available for this company.")

            # ==========================================================
            # SECTION 4: EURONEWS
            # ==========================================================
            st.divider()
            st.header("🌍 Latest Euronews Articles")

            news_items = push_news(ticker, ticker)
            if news_items:
                for news in news_items[:5]:
                    st.markdown(f"""
                    <div class="news-card">
                        <h4>📰 {news.get('title', 'Untitled')}</h4>
                        <p>{news.get('summary', '')}</p>
                        <a href="{news.get('url', '#')}" target="_blank">🔗 Read More</a>
                        <p class="news-meta">Published: {news.get('published_date', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent Euronews stories found.")

    except Exception as e:
        st.error(f"❌ Error: {e}")

else:
    st.info("Enter a ticker, select metrics, and click **Run Analysis** to begin.")
