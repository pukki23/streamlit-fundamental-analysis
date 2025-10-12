import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news

# ---------- Load CSS ----------
with open("assets/frontend_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="🧭 Company Insights Viewer", layout="wide")
st.title("🧭 Company Insights Viewer")

# ---------- Sidebar ----------
companies_resp = supabase.table("companies").select("id, ticker, company_name").execute()
companies_rows = companies_resp.data or []

company_names = [r["company_name"] for r in companies_rows if r.get("company_name")]
ticker_map = {r["company_name"]: r["ticker"] for r in companies_rows if r.get("ticker")}
ticker_names = [r["ticker"] for r in companies_rows if r.get("ticker")]
name_map = {r["ticker"]: r["company_name"] for r in companies_rows if r.get("ticker")}

st.sidebar.header("🔎 Select Company")

col1, col2 = st.sidebar.columns(2)
with col1:
    company_input = st.text_input("🏢 Company Name (e.g. Apple, Tesla, MTN):", "").strip()
with col2:
    ticker_input = st.text_input("🔠 Ticker (optional):", "").strip().upper()

# Auto-fill logic
if company_input and not ticker_input and company_input in ticker_map:
    ticker_input = ticker_map[company_input]
elif ticker_input and not company_input and ticker_input in name_map:
    company_input = name_map[ticker_input]

# ---------- Metrics Selection ----------
metrics_options = [
    "valuation",
    "profitability",
    "growth",
    "balance",
    "cashflow",
    "dividends",
    "recommendations",
]
selected_metrics = st.sidebar.multiselect("Select Metrics", metrics_options, default=["recommendations"])

# ---------- Fetch Button ----------
fetch_button = st.sidebar.button("📡 Fetch Insights")

# ---------- Utility Functions ----------
def get_company_record(ticker):
    if not ticker:
        return None
    res = supabase.table("companies").select("*").ilike("ticker", ticker).limit(1).execute()
    return res.data[0] if res.data else None

def get_table_rows(table, company_id=None, ticker=None):
    if company_id:
        res = supabase.table(table).select("*").eq("company_id", company_id).execute()
    elif ticker:
        res = supabase.table(table).select("*").ilike("ticker", ticker).execute()
    else:
        return []
    return res.data or []

def display_dict_in_columns(data_dict):
    """Show dictionary neatly in two Streamlit columns."""
    if not data_dict:
        return
    items = list(data_dict.items())
    col1, col2 = st.columns(2)
    for i, (k, v) in enumerate(items):
        target = col1 if i % 2 == 0 else col2
        target.markdown(f"**{k}:** {v}")

def recent_record_exists(table, ticker):
    try:
        res = (
            supabase.table(table)
            .select("run_timestamp")
            .ilike("ticker", ticker)
            .order("run_timestamp", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data:
            return False
        last_ts = datetime.fromisoformat(res.data[0]["run_timestamp"].replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - last_ts) < timedelta(days=1)
    except Exception:
        return False

# ---------- Overlay Spinner ----------
st.markdown("""
<div class="overlay"><div class="big-spinner-container">
<div class="big-spinner"></div><p>⏳ Fetching fresh insights...</p></div></div>
""", unsafe_allow_html=True)

st.markdown("""
<script>
function showSpinner() { document.querySelector('.overlay').classList.add('show'); }
function hideSpinner() { document.querySelector('.overlay').classList.remove('show'); }
</script>
""", unsafe_allow_html=True)

# ---------- Main Logic ----------
if fetch_button and company_input:
    st.markdown('<script>showSpinner()</script>', unsafe_allow_html=True)

    company_name = company_input.strip()
    ticker = ticker_input.strip().upper()

    # Run modules if data not fresh
    if not recent_record_exists("fundamentals", ticker):
        analyze_ticker(ticker, selected_metrics)

    if not recent_record_exists("news", ticker):
        push_news(ticker, company_name)

    st.markdown('<script>hideSpinner()</script>', unsafe_allow_html=True)
    st.success("Complete ✅")

    # Fetch from Supabase for display
    company = get_company_record(ticker)
    company_id = company.get("id") if company else None

    # ---- Metrics Display ----
    st.subheader("📊 Selected Metrics")
    cols = st.columns(len(selected_metrics)) if selected_metrics else []

    for idx, metric in enumerate(selected_metrics):
        with cols[idx]:
            table = metric
            rows = get_table_rows(table, company_id, ticker)
            if not rows:
                st.caption(f"No data in '{table}'.")
                continue
            row = rows[0]
            pretty = {
                k.replace("_", " ").title(): v
                for k, v in row.items()
                if k not in ("id", "created_at", "updated_at", "uniquekey", "unique_key", "company_id")
            }
            st.markdown(f"#### {metric.title()}")
            display_dict_in_columns(pretty)

    # ---- Analyst Recommendations ----
    if "recommendations" in selected_metrics:
        rec_rows = get_table_rows("recommendations", company_id, ticker)
        if rec_rows:
            st.subheader("💬 Analyst Recommendations (Full Detail)")
            cols = st.columns(2)
            for i, rec in enumerate(rec_rows[:4]):
                col = cols[i % 2]
                pretty = {
                    k.replace("_", " ").title(): v
                    for k, v in rec.items()
                    if k not in ("id", "created_at", "updated_at", "uniquekey", "unique_key", "company_id")
                }
                col.markdown("------")
                col.markdown(f"**{pretty.get('Firm', 'Analyst')}** — {pretty.get('Rating', 'N/A')}")
                col.caption(f"Target: {pretty.get('Target Price', 'N/A')}")
                col.caption(f"Date: {pretty.get('Date', 'N/A')}")

    # ---- Filings ----
    st.subheader("📂 Upcoming Filings")
    filings = supabase.table("filings").select("*").ilike("ticker", ticker).execute().data or []
    if filings:
        for f in filings[:2]:
            with st.expander(f"🗓️ Next Filing Date: {f.get('next_earnings_date', 'N/A')}"):
                st.markdown(f"**Company:** {f.get('company_name', company_name)}")
                st.markdown(f"**Source:** {f.get('filing_source', 'N/A')}")
                if f.get("filing_link"):
                    st.markdown(f"[🔗 View Filing]({f['filing_link']})", unsafe_allow_html=True)
    else:
        st.info("No upcoming filings found.")

    # ---- News ----
    st.subheader("📰 Latest News")
    news_snapshot = supabase.table("news").select("*").ilike("ticker", ticker).limit(1).execute()
    snapshot = news_snapshot.data[0] if news_snapshot.data else None
    news_list = snapshot.get("news") if snapshot else []

    if news_list:
        cols = st.columns(2)
        for i, item in enumerate(news_list[:4]):
            col = cols[i % 2]
            with col.expander(f"🗞️ {item.get('title', '(no title)')}"):
                col.markdown(f"**Source:** [Read on {item.get('source', 'Link')}]({item.get('link', '#')})")
                col.caption(f"Published: {item.get('published', 'N/A')}")
    else:
        st.info("No recent news found.")

else:
    st.info("Enter a company name or ticker, then click **Fetch Insights** to display information.")
