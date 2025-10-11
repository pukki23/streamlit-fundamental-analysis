import streamlit as st
import pandas as pd
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from sripts.scraper import find_and_extract_latest_filing

# --- Load CSS ---
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🧭 Company Insights Viewer")
st.markdown("Explore company fundamentals, filings, and financial reports in a friendly format.")

# --- Search Bar ---
ticker = st.text_input("🔍 Enter Company Ticker or Name (e.g. AAPL, TSLA, MTN):").strip()

if ticker:
    try:
        # --- Fundamental Analysis ---
        st.subheader("📊 Fundamental Analysis")
        with st.spinner("Analyzing fundamentals..."):
            analysis = analyze_ticker(ticker)
        
        if analysis:
            st.success("Analysis fetched successfully!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Market Cap", analysis.get("market_cap", "N/A"))
            col2.metric("P/E Ratio", analysis.get("pe_ratio", "N/A"))
            col3.metric("Dividend Yield", analysis.get("dividend_yield", "N/A"))

            st.markdown("### 📈 Performance Summary")
            st.markdown(f"**Sector:** {analysis.get('sector', 'N/A')}")
            st.markdown(f"**52 Week Range:** {analysis.get('52_week_range', 'N/A')}")
            st.markdown(f"**Beta:** {analysis.get('beta', 'N/A')}")
            st.markdown(f"**Recommendation:** {analysis.get('recommendation', 'N/A')}")
        else:
            st.warning("No analysis data found.")

        # --- Filings Section ---
        st.divider()
        st.subheader("📂 Latest Company Filings")

        filings_data = supabase.table("filings").select("*").eq("ticker", ticker).execute()
        if filings_data.data:
            filings_df = pd.DataFrame(filings_data.data)
            for _, row in filings_df.iterrows():
                with st.expander(f"🗂️ {row['filing_title']} ({row.get('filing_type', 'Unknown')})"):
                    st.markdown(f"**Date:** {row.get('filing_date', 'N/A')}")
                    st.markdown(f"**Summary:** {row.get('filing_summary', 'No summary available')}")
                    if row.get("filing_url"):
                        st.markdown(f"[View Filing]({row['filing_url']})", unsafe_allow_html=True)
        else:
            st.info("No recent filings found for this company.")

        # --- Filing History Section ---
        st.divider()
        st.subheader("🕘 Filing History")

        history_data = supabase.table("filings_history").select("*").eq("ticker", ticker).execute()
        if history_data.data:
            history_df = pd.DataFrame(history_data.data)
            st.dataframe(
                history_df[["event_type", "filing_title", "expected_date", "classification_label", "classification_score"]],
                use_container_width=True
            )
        else:
            st.info("No filing history found for this company.")

        # --- Latest Filing from Scraper ---
        st.divider()
        st.subheader("📰 Latest Financial News Filing")
        news_data = find_and_extract_latest_filing(ticker)
        if news_data:
            st.markdown(f"**{news_data['filing_title']}**")
            st.markdown(news_data['filing_summary'])
            st.markdown(f"[Read full article]({news_data['filing_url']})", unsafe_allow_html=True)
            with st.expander("🧾 View Extracted Full Text"):
                st.markdown(news_data['filing_text'])
        else:
            st.warning("No financial news articles found for this company.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Enter a company ticker or name above to explore insights.")
