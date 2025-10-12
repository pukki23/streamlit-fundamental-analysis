import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news, fetch_news

# --- Load CSS ---
with open("assets/frontend_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="🧭 Company Insights Viewer", layout="wide")
st.title("🧭 Company Insights Viewer")

# -------- Sidebar controls --------
companies_resp = supabase.table("companies").select("id, ticker, company_name").execute()
companies_rows = companies_resp.data or []

company_options = []
ticker_for_company = {}

for r in companies_rows:
    name = (r.get("company_name") or "").strip()
    ticker = (r.get("ticker") or "").strip()
    if name:
        label = f"{name} — {ticker}" if ticker else name
        company_options.append(label)
        ticker_for_company[label] = ticker

st.sidebar.header("🔎 Select Company")
selected_label = st.sidebar.selectbox(
    "Choose a company (type to search)", ["(manual entry)"] + sorted(company_options)
)

if selected_label != "(manual entry)":
    company_input = selected_label.split(" — ")[0]
    ticker_input = ticker_for_company.get(selected_label, "")
else:
    company_input = st.sidebar.text_input("Company Name", "")
    ticker_input = st.sidebar.text_input("Ticker (optional)", "")

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
    "Select metrics to fetch & show", metrics_options, default=["recommendations"]
)
fetch_button = st.sidebar.button("📡 Fetch Insights")

# -------- Helper Functions --------
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
    """Show a dictionary in two Streamlit columns for compactness."""
    if not data_dict:
        return
    items = list(data_dict.items())
    col1, col2 = st.columns(2)
    for i, (k, v) in enumerate(items):
        target = col1 if i % 2 == 0 else col2
        target.markdown(f"**{k}:** {v}")

def recent_record_exists(table, ticker):
    """Prevent duplicate push if recent record exists (<1 day old)."""
    try:
        res = supabase.table(table).select("run_timestamp").ilike("ticker", ticker).order("run_timestamp", desc=True).limit(1).execute()
        if not res.data:
            return False
        last_ts = datetime.fromisoformat(res.data[0]["run_timestamp"].replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - last_ts) < timedelta(days=1)
    except Exception:
        return False

# ----------- MAIN LOGIC ------------
if fetch_button and company_input:
    company_name = company_input.strip()
    ticker = ticker_input.strip().upper()

    st.info(f"Fetching data for **{company_name} ({ticker})** ...")

    # Avoid duplicate insert if recent
    if not recent_record_exists("fundamentals", ticker):
        try:
            analyze_ticker(ticker, selected_metrics)
        except Exception as e:
            st.error(f"Analyze error: {e}")

    if not recent_record_exists("news", ticker):
        try:
            push_news(ticker, company_name)
        except Exception as e:
            st.error(f"News push error: {e}")

    st.success("✅ Data fetch complete. Displaying stored results...")

    company = get_company_record(ticker)
    company_id = company.get("id") if company else None

    # ---- METRICS TABLES SIDE BY SIDE ----
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
                if k not in ("id", "created_at", "updated_at", "uniquekey", "unique_key")
            }
            st.markdown(f"#### {metric.title()}")
            display_dict_in_columns(pretty)

    # ---- RECOMMENDATIONS DETAILED VIEW ----
    if "recommendations" in selected_metrics:
        rec_rows = get_table_rows("recommendations", company_id, ticker)
        if rec_rows:
            st.subheader("💬 Analyst Recommendations (Full Detail)")
            for rec in rec_rows[:4]:
                pretty = {
                    k.replace("_", " ").title(): v
                    for k, v in rec.items()
                    if k not in ("id", "created_at", "updated_at", "uniquekey", "unique_key")
                }
                with st.expander(f"📈 {pretty.get('Firm', 'Analyst')} — {pretty.get('Rating', 'N/A')}"):
                    display_dict_in_columns(pretty)

    # ---- FILINGS SECTION ----
    st.subheader("📂 Upcoming Filings")
    filings = supabase.table("filings").select("*").ilike("ticker", ticker).execute().data or []
    if filings:
        for f in filings[:2]:
            with st.expander(f"🗓️ Next Filing Date: {f.get('next_earnings_date', 'N/A')}"):
                st.markdown(f"**Company:** {f.get('company_name', company_name)}")
                st.markdown(f"**Source:** {f.get('filing_source','N/A')}")
                if f.get("filing_link"):
                    st.markdown(f"[🔗 View Filing]({f['filing_link']})", unsafe_allow_html=True)
    else:
        st.info("No upcoming filings found.")

    # ---- NEWS SECTION ----
    st.subheader("📰 Latest News")
    news_snapshot = supabase.table("news").select("*").ilike("ticker", ticker).limit(1).execute()
    snapshot = news_snapshot.data[0] if news_snapshot.data else None
    news_list = snapshot.get("news") if snapshot else []
    if news_list:
        cols = st.columns(2)
        for i, item in enumerate(news_list[:4]):
            col = cols[i % 2]
            with col.expander(f"🗞️ {item.get('title','(no title)')}"):
                col.markdown(f"**Source:** {item.get('source','N/A')} — {item.get('published','N/A')}")
                col.markdown(f"[Read More]({item.get('link','#')})", unsafe_allow_html=True)
    else:
        st.info("No recent news found.")

else:
    st.info("Enter a company name and click **Fetch Insights** to display information.")
