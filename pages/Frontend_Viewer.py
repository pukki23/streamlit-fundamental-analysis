import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news

# --- Load CSS ---
with open("assets/frontend_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="🧭 Company Insights Viewer", layout="wide")
st.title("🧭 Company Insights Viewer")

# -------- Fetch companies for autofill --------
companies_resp = supabase.table("companies").select("id, ticker, company_name").execute()
companies = companies_resp.data or []

company_names = [c["company_name"] for c in companies if c.get("company_name")]
tickers = [c["ticker"] for c in companies if c.get("ticker")]

# -------- User Input Section --------
st.markdown('<div class="center-container">', unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])
with col1:
    company_input = st.text_input("🏢 Company Name (e.g. Apple, Tesla, MTN):", "")
with col2:
    ticker_input = st.text_input("🔠 Ticker (optional):", "")
st.markdown('</div>', unsafe_allow_html=True)

# --- Autofill logic (case-insensitive) ---
if company_input and not ticker_input:
    match = next((c["ticker"] for c in companies if c["company_name"].lower() == company_input.lower()), "")
    if match:
        ticker_input = match
elif ticker_input and not company_input:
    match = next((c["company_name"] for c in companies if c["ticker"].lower() == ticker_input.lower()), "")
    if match:
        company_input = match

# -------- Sidebar controls --------
st.sidebar.header("📊 Configuration")
metrics_options = [
    "valuation", "profitability", "growth",
    "balance", "cashflow", "dividends", "recommendations", "companies"
]
selected_metrics = st.sidebar.multiselect("Select Metrics", metrics_options, default=["companies"])
fetch_button_sidebar = st.sidebar.button("📡 Fetch Insights")

# --- Centered Fetch Button on Main Page ---
fetch_button_main = st.button("📡 Fetch Insights", key="main_fetch", use_container_width=True)

# Merge button logic
fetch_triggered = fetch_button_sidebar or fetch_button_main


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

def display_dict_pretty(data_dict):
    """Displays key-value pairs inside styled cards."""
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


# ----------- MAIN LOGIC ------------
if fetch_triggered and company_input:
    company_name = company_input.strip()
    ticker = ticker_input.strip().upper()

    # Dimmed overlay + spinner
    spinner_html = """
    <div class="dim-overlay" id="dim-overlay">
        <div class="big-spinner">🚀 Fetching insights... Please wait</div>
    </div>
    """
    st.markdown(spinner_html, unsafe_allow_html=True)

    if not recent_record_exists("fundamentals", ticker):
        analyze_ticker(ticker, selected_metrics)
    push_news(ticker, company_name)

    # Hide overlay
    st.markdown("<script>document.getElementById('dim-overlay').remove();</script>", unsafe_allow_html=True)
    st.markdown("<div class='complete-box'>✅ Complete</div>", unsafe_allow_html=True)

    company = get_company_record(ticker)
    company_id = company.get("id") if company else None

    # Animated container
    st.markdown('<div class="fade-in-results">', unsafe_allow_html=True)

    # ---- METRICS SECTION ----
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
            st.markdown(f"<div class='metric-card'><h4>{metric.title()}</h4>", unsafe_allow_html=True)
            display_dict_pretty(pretty)
            st.markdown("</div>", unsafe_allow_html=True)

    # ---- RECOMMENDATIONS ----
    if "recommendations" in selected_metrics:
        rec_rows = get_table_rows("recommendations", company_id, ticker)
        if rec_rows:
            st.subheader("💬 Analyst Recommendations (Full Detail)")
            cols = st.columns(2)
            for i, rec in enumerate(rec_rows[:4]):
                col = cols[i % 2]
                with col:
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
        for f in filings[:2]:
            with st.expander(f"🗓️ Next Filing Date: {f.get('next_earnings_date', 'N/A')}"):
                st.markdown(f"**Company:** {f.get('company_name', company_name)}")
                st.markdown(f"**Source:** {f.get('filing_source','N/A')}")
                if f.get("filing_link"):
                    st.markdown(f"[🔗 View Filing]({f['filing_link']})", unsafe_allow_html=True)
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
                st.markdown(f"**Published Date** {item.get('published','N/A')}")
    else:
        st.info("No recent news found.")

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Enter a company name and click **Fetch Insights** to display information.")
