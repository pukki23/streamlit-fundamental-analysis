import streamlit as st
import pandas as pd
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news
from scripts.scraper import find_and_extract_latest_filing

# === Load Custom CSS ===
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === PAGE CONFIG ===
st.set_page_config(page_title="🧭 Company Insights Viewer", layout="wide")
st.title("🧭 Company Insights Viewer")
st.markdown("Explore company fundamentals, filings, and global financial news in a friendly, visual format.")

# === INPUT SECTION ===
st.divider()
ticker = st.text_input("🔍 Enter Company Ticker or Name (e.g. AAPL, TSLA, MTN):").strip()

# =====================================================================
# MAIN LOGIC
# =====================================================================
if ticker:
    try:
        # --------------------------------------------------------------
        # SECTION 1: FUNDAMENTAL ANALYSIS
        # --------------------------------------------------------------
        st.header("📊 Fundamental Analysis")
        with st.spinner("Fetching and analyzing fundamentals..."):
            fundamentals = analyze_ticker(ticker)

        if fundamentals:
            st.success("✅ Analysis fetched successfully!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Market Cap", fundamentals.get("market_cap", "N/A"))
            col2.metric("P/E Ratio", fundamentals.get("pe_ratio", "N/A"))
            col3.metric("Dividend Yield", fundamentals.get("dividend_yield", "N/A"))

            st.markdown("### 📈 Performance Overview")
            perf_cols = st.columns(2)
            with perf_cols[0]:
                st.markdown(f"**Sector:** {fundamentals.get('sector', 'N/A')}")
                st.markdown(f"**52 Week Range:** {fundamentals.get('52_week_range', 'N/A')}")
                st.markdown(f"**Beta:** {fundamentals.get('beta', 'N/A')}")
            with perf_cols[1]:
                st.markdown(f"**Recommendation:** {fundamentals.get('recommendation', 'N/A')}")
                st.markdown(f"**Growth Score:** {fundamentals.get('growth_score', 'N/A')}")
                st.markdown(f"**Profitability:** {fundamentals.get('profitability', 'N/A')}")
        else:
            st.warning("⚠️ No fundamentals found for this company.")

        # --------------------------------------------------------------
        # SECTION 2: FILINGS
        # --------------------------------------------------------------
        st.divider()
        st.header("📂 Latest Company Filings")
        filings_data = supabase.table("filings").select("*").eq("ticker", ticker).execute()

        if filings_data.data:
            filings_df = pd.DataFrame(filings_data.data)
            for _, row in filings_df.iterrows():
                st.markdown(f"""
                <div class="filing-card">
                    <div class="filing-title">🗂️ {row.get('filing_title', 'Untitled')}</div>
                    <p class="filing-meta">
                        <strong>Date:</strong> {row.get('next_earnings_date', 'N/A')}<br>
                        <strong>Source:</strong> {row.get('filing_source', 'N/A')}
                    </p>
                    <p>{row.get('filing_summary', 'No summary available')}</p>
                    <a href="{row.get('filing_url', '#')}" target="_blank">🔗 View Filing</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No active filings found for this company.")

        # --------------------------------------------------------------
        # SECTION 3: FILING HISTORY
        # --------------------------------------------------------------
        st.divider()
        st.header("🕘 Filing History")

        history_data = supabase.table("filings_history").select("*").eq("ticker", ticker).execute()
        if history_data.data:
            history_df = pd.DataFrame(history_data.data)
            st.dataframe(
                history_df[
                    ["event_type", "filing_title", "expected_date", "classification_label", "classification_score"]
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No filing history available.")

        # --------------------------------------------------------------
        # SECTION 4: SCRAPED FILINGS / NEWS
        # --------------------------------------------------------------
        st.divider()
        st.header("📰 Latest Financial News Filing")

        scraped_news = find_and_extract_latest_filing(ticker)
        if scraped_news:
            st.markdown(f"""
            <div class="filing-card">
                <div class="filing-title">{scraped_news['filing_title']}</div>
                <p>{scraped_news['filing_summary']}</p>
                <a href="{scraped_news['filing_url']}" target="_blank">🔗 View Full Article</a>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("🧾 View Extracted Full Text"):
                st.markdown(scraped_news['filing_text'])
        else:
            st.warning("No recent financial news filing found for this ticker.")

        # --------------------------------------------------------------
        # SECTION 5: EURONEWS INTEGRATION
        # --------------------------------------------------------------
        st.divider()
        st.header("🌍 Global Financial & Business News (Euronews)")

        with st.spinner("Fetching latest Euronews stories..."):
            euronews_items = push_news(ticker, ticker)

        if euronews_items:
            for news in euronews_items[:5]:
                st.markdown(f"""
                <div class="news-card">
                    <h4>📰 {news.get('title', 'Untitled')}</h4>
                    <p>{news.get('summary', '')}</p>
                    <a href="{news.get('url', '#')}" target="_blank">🔗 Read Article</a>
                    <p class="news-meta">Source: Euronews | Date: {news.get('published_date', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No relevant Euronews stories found.")

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("Enter a company ticker or name above to explore insights.")
