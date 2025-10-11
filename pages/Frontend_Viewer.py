import streamlit as st
import pandas as pd
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import fetch_news

# --- Load CSS ---
with open("assets/frontend_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🧭 Company Insights Viewer")
st.markdown("<h4 class='subtitle'>Explore company data, filings, and news in a clean, user-friendly format.</h4>", unsafe_allow_html=True)

# --- Input Section ---
col1, col2 = st.columns([2, 1])
with col1:
    company_name = st.text_input("🏢 Company Name (e.g. Apple, Tesla, MTN):").strip()
with col2:
    ticker = st.text_input("🔠 Ticker (optional):").strip()

if company_name or ticker:
    try:
        # --- Fundamental Analysis ---
        st.subheader("📊 Fundamental Analysis")
        with st.spinner("Analyzing company fundamentals..."):
            analysis = analyze_ticker(ticker or company_name, metrics=["market_cap", "pe_ratio", "dividend_yield", "sector", "beta", "52_week_range", "recommendation"])

        if analysis:
            st.success("✅ Analysis loaded successfully!")

            col1, col2, col3 = st.columns(3)
            col1.metric("Market Cap", analysis.get("market_cap", "N/A"))
            col2.metric("P/E Ratio", analysis.get("pe_ratio", "N/A"))
            col3.metric("Dividend Yield", analysis.get("dividend_yield", "N/A"))

            st.markdown(f"**Sector:** {analysis.get('sector', 'N/A')}")
            st.markdown(f"**52 Week Range:** {analysis.get('52_week_range', 'N/A')}")
            st.markdown(f"**Beta:** {analysis.get('beta', 'N/A')}")
            st.markdown(f"**Recommendation:** {analysis.get('recommendation', 'N/A')}")
        else:
            st.warning("No analysis data found.")

        # --- Filings Section ---
        st.divider()
        st.subheader("📂 Recent Filings")

        filings_data = supabase.table("filings").select("*").eq("ticker", ticker).execute()
        filings_df = pd.DataFrame(filings_data.data) if filings_data.data else pd.DataFrame()

        if not filings_df.empty:
            visible_filings = filings_df.head(2)
            for _, row in visible_filings.iterrows():
                with st.expander(f"🗂️ {row.get('filing_title', 'Untitled')} - {row.get('filing_date', 'N/A')}"):
                    st.markdown(f"**Filing Type:** {row.get('filing_type', 'N/A')}")
                    st.markdown(f"**Date:** {row.get('filing_date', 'N/A')}")
                    st.markdown(f"**Summary:** {row.get('filing_summary', 'No summary available')}")
                    if row.get("filing_url"):
                        st.markdown(f"[🔗 View Full Filing]({row['filing_url']})", unsafe_allow_html=True)

            if len(filings_df) > 2:
                with st.expander("📜 Show More Filings"):
                    for _, row in filings_df.iloc[2:].iterrows():
                        st.markdown(f"**{row.get('filing_title', 'Untitled')}**  \n📅 {row.get('filing_date', 'N/A')}  \n[{row.get('filing_type', 'View Filing')}]({row.get('filing_url', '#')})")
                        st.divider()
        else:
            st.info("No filings found for this company.")

        # --- Filing History Section ---
        st.divider()
        st.subheader("🕘 Filing History")

        history_data = supabase.table("filings_history").select("*").eq("ticker", ticker).execute()
        history_df = pd.DataFrame(history_data.data) if history_data.data else pd.DataFrame()

        if not history_df.empty:
            visible_history = history_df.head(2)
            for _, row in visible_history.iterrows():
                with st.expander(f"📅 {row.get('expected_date', 'N/A')} - {row.get('filing_title', 'Unknown')}"):
                    st.markdown(f"**Event:** {row.get('event_type', 'N/A')}")
                    st.markdown(f"**Classification:** {row.get('classification_label', 'N/A')} ({row.get('classification_score', 'N/A')})")

            if len(history_df) > 2:
                with st.expander("📜 Show More Filing History"):
                    st.dataframe(
                        history_df[["event_type", "filing_title", "expected_date", "classification_label", "classification_score"]],
                        use_container_width=True,
                    )
        else:
            st.info("No filing history available.")

        # --- News Section ---
        st.divider()
        st.subheader("📰 Latest Company News")
        with st.spinner("Fetching latest news..."):
            news_items = fetch_news(ticker or company_name, company_name)

        if news_items:
            visible_news = news_items[:2]
            for item in visible_news:
                with st.expander(f"🗞️ {item['title']}"):
                    st.markdown(f"<div class='news-card'><b>Source:</b> {item['source']}<br><b>Date:</b> {item.get('published', 'N/A')}<br><a href='{item['link']}' target='_blank'>Read full article</a></div>", unsafe_allow_html=True)

            if len(news_items) > 2:
                with st.expander("📰 Show More News (Scrollable)"):
                    st.markdown("<div class='scrollable-section'>", unsafe_allow_html=True)
                    for item in news_items[2:]:
                        st.markdown(f"<div class='news-card'><b>{item['title']}</b><br><i>{item['source']}</i><br><a href='{item['link']}' target='_blank'>Read</a></div>", unsafe_allow_html=True)
                        st.markdown("<hr>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No recent news found for this company.")

    except Exception as e:
        st.error(f"❌ Error: {e}")

else:
    st.info("Enter a company name or ticker above to explore insights.")
