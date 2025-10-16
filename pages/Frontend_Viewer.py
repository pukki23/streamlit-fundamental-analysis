import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news

# --- Page Config ---
st.set_page_config(page_title="🧭 Company Insights Viewer", layout="wide")
st.title("🧭 Company Insights Viewer")

# --- Load CSS ---
with open("assets/frontend_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Load companies for autofill ---
companies_resp = supabase.table("companies").select("id, ticker, company_name, sector, industry, currency, country").execute()
companies = companies_resp.data or []
company_names = [c["company_name"] for c in companies if c.get("company_name")]
tickers = [c["ticker"] for c in companies if c.get("ticker")]

# --- Input fields ---
st.markdown('<div class="center-container">', unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])
with col1:
    company_input = st.text_input("🏢 Company Name (e.g. Apple, Tesla, MTN):", "")
with col2:
    ticker_input = st.text_input("🔠 Ticker (optional):", "")
st.markdown('</div>', unsafe_allow_html=True)

# Autofill logic
if company_input and not ticker_input:
    match = next((c["ticker"] for c in companies if c["company_name"].lower() == company_input.lower()), "")
    if match:
        ticker_input = match
elif ticker_input and not company_input:
    match = next((c["company_name"] for c in companies if c["ticker"].lower() == ticker_input.lower()), "")
    if match:
        company_input = match

# --- Sidebar configuration ---
st.sidebar.header("📊 Configuration")
metrics_options = [
    "valuation", "profitability", "growth",
    "balance", "cashflow", "dividends", "recommendations", "companies"
]
selected_metrics = st.sidebar.multiselect("Select Metrics", metrics_options, default=["companies"])
fetch_button_sidebar = st.sidebar.button("📡 Fetch Insights")
fetch_button_main = st.button("📡 Fetch Insights", key="main_fetch", use_container_width=True)
fetch_triggered = fetch_button_sidebar or fetch_button_main


# -------- Helper Functions --------
def get_company_record(ticker):
    if not ticker:
        return None
    res = supabase.table("companies").select("*").ilike("ticker", ticker).limit(1).execute()
    return res.data[0] if res.data else None


def get_table_rows(table, company_id=None, ticker=None):
    """Fetch table rows based on either company_id or ticker"""
    if table == "companies":
        if ticker:
            res = supabase.table("companies").select("*").ilike("ticker", ticker).execute()
        else:
            return []
    elif company_id:
        res = supabase.table(table).select("*").eq("company_id", company_id).execute()
    elif ticker:
        res = supabase.table(table).select("*").ilike("ticker", ticker).execute()
    else:
        return []
    return res.data or []


def display_dict_pretty(data_dict):
    for k, v in data_dict.items():
        st.markdown(f"<div class='metric-item'><b>{k}:</b> {v}</div>", unsafe_allow_html=True)


def recent_record_exists(table, ticker):
    try:
        res = supabase.table(table).select("run_timestamp").ilike("ticker", ticker).order("run_timestamp", desc=True).limit(1).execute()
        if not res.data:
            return False
        last_ts = datetime.fromisoformat(res.data[0]["run_timestamp"].replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - last_ts) < timedelta(days=1)
    except Exception:
        return False


# -------- Main Display Logic --------
if fetch_triggered and company_input:
    company_name = company_input.strip()
    ticker = ticker_input.strip().upper()

    # Fetch or trigger analysis
    if not recent_record_exists("fundamentals", ticker):
        analyze_ticker(ticker, selected_metrics)
    push_news(ticker, company_name)

    st.markdown("<div class='complete-box'>✅ Complete</div>", unsafe_allow_html=True)

    company = get_company_record(ticker)
    company_id = company.get("id") if company else None

    st.markdown('<div class="fade-in-results">', unsafe_allow_html=True)

    # ---- COMPANY CARD ----
    if "companies" in selected_metrics:
        st.subheader("🏢 Company Overview")

        companies_data = []
        if ticker:
            companies_data = supabase.table("companies").select("*").ilike("ticker", ticker).execute().data or []
        elif company_name:
            companies_data = supabase.table("companies").select("*").ilike("company_name", company_name).execute().data or []

        if companies_data:
            comp = companies_data[0]
            st.markdown(f"""
            <div class='company-card'>
                <h4>{comp.get('company_name', 'N/A')}</h4>
                <p><b>Ticker:</b> {comp.get('ticker', 'N/A')}</p>
                <p><b>Sector:</b> {comp.get('sector', 'N/A')}</p>
                <p><b>Industry:</b> {comp.get('industry', 'N/A')}</p>
                <p><b>Country:</b> {comp.get('country', 'N/A')}</p>
                <p><b>Exchange:</b> {comp.get('exchange', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption(f"No company data found for '{company_name or ticker}'.")
        selected_metrics = [m for m in selected_metrics if m != "companies"]

    # ---- METRICS SECTION ----
    if selected_metrics:
        st.subheader("📊 Selected Metrics")
        cols = st.columns(len(selected_metrics))
        for idx, metric in enumerate(selected_metrics):
            with cols[idx]:
                rows = get_table_rows(metric, company_id, ticker)
                if not rows:
                    st.caption(f"No data in '{metric}'.")
                    continue
                row = rows[0]
                pretty = {
                    k.replace("_", " ").title(): v
                    for k, v in row.items()
                    if k not in ("id", "created_at", "updated_at", "uniquekey", "unique_key", "company_id")
                }
                st.markdown(f"<div class='metric-card'><h4>{metric.title()}</h4>", unsafe_allow_html=True)
                display_dict_pretty(pretty)
                st.markdown("</div>", unsafe_allow_html=True)

    # ---- RECOMMENDATIONS ----
    if "recommendations" in selected_metrics:
        rec_rows = get_table_rows("recommendations", company_id, ticker)
        if rec_rows:
            st.subheader("💬 Analyst Recommendations")
            cols = st.columns(2)
            for i, rec in enumerate(rec_rows[:4]):
                with cols[i % 2]:
                    pretty = {
                        k.replace("_", " ").title(): v
                        for k, v in rec.items()
                        if k not in ("id", "created_at", "updated_at", "uniquekey", "unique_key", "company_id")
                    }
                    st.markdown("<div class='recommend-card'>", unsafe_allow_html=True)
                    display_dict_pretty(pretty)
                    st.markdown("</div>", unsafe_allow_html=True)

    # ---- FILINGS ----
    st.subheader("📂 Upcoming Filings")
    filings = supabase.table("filings").select("*").ilike("ticker", ticker).execute().data or []
    if filings:
        next_filing = filings[0]
        st.markdown(f"### 🗓️ Next Filing Date: {next_filing.get('next_earnings_date', 'N/A')}")
        with st.expander("View Filing Details"):
            st.markdown(f"**Company:** {next_filing.get('company_name', company_name)}")
            st.markdown(f"**Source:** {next_filing.get('filing_source','N/A')}")
            if next_filing.get("filing_link"):
                st.markdown(f"[🔗 View Filing]({next_filing['filing_link']})", unsafe_allow_html=True)
    else:
        st.info("No upcoming filings found.")

    # ---- NEWS ----
    st.subheader("📰 Latest News")
    news_snapshot = supabase.table("news").select("*").ilike("ticker", ticker).limit(1).execute()
    snapshot = news_snapshot.data[0] if news_snapshot.data else None
    news_list = snapshot.get("news") if snapshot else []
    if news_list:
        for item in news_list[:6]:
            with st.expander(f"🗞️ {item.get('title','(no title)')}"):
                st.markdown(f"**Summary:** {item.get('summary','N/A')}")
                st.markdown(f"[🔗 Source Link]({item.get('link','#')})", unsafe_allow_html=True)
                st.markdown(f"**Published Date:** {item.get('published','N/A')}")
    else:
        st.info("No recent news found.")

    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("Enter a company name and click **Fetch Insights** to display information.")
