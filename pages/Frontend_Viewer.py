import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_client import supabase

# modules that perform the fetch + upsert actions (already in your repo)
from scripts.analysis_module import analyze_ticker
from scripts.euronews_module import push_news, fetch_news  # push_news upserts; fetch_news for quick runtime display

# --- load CSS (frontend_style.css expected in assets/) ---
with open("assets/frontend_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page config
st.set_page_config(page_title="🧭 Frontend Viewer — Company Insights", layout="wide")
st.title("🧭 Company Insights Viewer")
st.markdown("<h4 class='subtitle'>Search a company, fetch fresh fundamentals & news, and view results (stored in Supabase).</h4>", unsafe_allow_html=True)

# ----------------------------
# 1) Build company autocomplete (searchable selectbox)
# ----------------------------
# Fetch companies list from Supabase
companies_resp = supabase.table("companies").select("id, ticker, company_name").execute()
companies_rows = companies_resp.data or []

# Build lookup structures
company_options = []
ticker_for_company = {}
company_for_ticker = {}

for r in companies_rows:
    name = (r.get("company_name") or "").strip()
    ticker = (r.get("ticker") or "").strip()
    if name and ticker:
        label = f"{name} — {ticker}"
        company_options.append(label)
        ticker_for_company[label] = ticker
        company_for_ticker[ticker] = name
    elif name:
        company_options.append(name)
        ticker_for_company[name] = ""
    elif ticker:
        company_options.append(ticker)
        ticker_for_company[ticker] = ticker
company_options = sorted(list(dict.fromkeys(company_options)))  # dedupe & keep order stable

st.sidebar.header("🔎 Select Company")
# The selectbox is searchable — acts as autocomplete for company names
selected_label = st.sidebar.selectbox("Choose a company (type to search)", options=["(manual entry)"] + company_options, index=0)

# If manual entry chosen show text inputs, else split label into company/ticker
if selected_label != "(manual entry)":
    inferred_ticker = ticker_for_company.get(selected_label, "")
    # set the company_name and ticker inputs with inferred values, but still editable
    company_input = st.sidebar.text_input("Company Name", value=selected_label.split(" — ")[0] if " — " in selected_label else selected_label)
    ticker_input = st.sidebar.text_input("Ticker (editable)", value=inferred_ticker)
else:
    company_input = st.sidebar.text_input("Company Name", value="")
    ticker_input = st.sidebar.text_input("Ticker (optional)", value="")

# Metric selection similar to backend
metrics_options = [
    "valuation",
    "profitability",
    "growth",
    "balance",
    "cashflow",
    "dividends",
    "recommendations",
]
selected_metrics = st.sidebar.multiselect("Select metrics to fetch & show", options=metrics_options, default=metrics_options)

# Button to run the pipeline
fetch_button = st.sidebar.button("📡 Fetch Insights (runtime → store → display)")

# Helper functions for reading standardized tables from Supabase
def get_company_record_by_ticker(ticker: str):
    if not ticker:
        return None
    res = supabase.table("companies").select("*").eq("ticker", ticker).limit(1).execute()
    return (res.data[0] if res.data else None)

def get_table_by_company_id_or_ticker(table_name: str, company_id=None, ticker=None):
    # prefer company_id, else try ticker filter
    if company_id:
        r = supabase.table(table_name).select("*").eq("company_id", company_id).execute()
    elif ticker:
        # many of your tables use company_id; some may include ticker fields — try both
        r = supabase.table(table_name).select("*").ilike("uniquekey", f"%{ticker}%").execute()
        # fallback: try a direct ticker field
        if not (r.data if r and getattr(r, "data", None) else None):
            try:
                r = supabase.table(table_name).select("*").eq("ticker", ticker).execute()
            except Exception:
                pass
    else:
        r = None
    return r.data if r and getattr(r, "data", None) else []

# Display helpers — hide internal columns and prettify keys
def pretty_row_for_display(row: dict, map_labels: dict = None):
    out = {}
    for k, v in (row or {}).items():
        if k in ("id", "created_at", "updated_at", "uniquekey", "unique_key"):
            continue
        pretty_key = map_labels.get(k, k.replace("_", " ").title()) if map_labels else k.replace("_", " ").title()
        out[pretty_key] = v
    return out

# The on-click flow: run modules that fetch & upsert to Supabase, then read from Supabase to display
if fetch_button:
    company_name = (company_input or "").strip()
    ticker = (ticker_input or "").strip().upper()

    if not company_name or not ticker:
        st.sidebar.error("Please provide both a company name and a ticker (or pick from the list).")
    else:
        st.sidebar.info("Fetching data — this may take a few seconds...")
        # 1) analyze_ticker will upsert fundamentals into Supabase (per your module)
        try:
            analyze_ok = analyze_ticker(ticker, selected_metrics)
        except Exception as e:
            analyze_ok = False
            st.sidebar.error(f"analyze_ticker error: {e}")

        # 2) fetch & push news
        try:
            push_news(ticker, company_name)
        except Exception as e:
            st.sidebar.error(f"push_news error: {e}")

        st.sidebar.success("Fetch complete. Loading stored results from Supabase...")

        # After this we will re-load stored data and show below

# ---------- Display area ----------
st.markdown("---")
st.header("🔎 Results (from Supabase)")

company_display = (company_input or "").strip()
ticker_display = (ticker_input or "").strip().upper()

if not company_display and not ticker_display:
    st.info("Use the sidebar to select a company and ticker, then click 'Fetch Insights'.")
else:
    # 1) Get canonical company record (to find company_id)
    company_rec = get_company_record_by_ticker(ticker_display)
    company_id = company_rec.get("id") if company_rec else None

    # Top summary card
    st.subheader(f"{company_display}  —  {ticker_display}")
    col1, col2, col3 = st.columns(3)
    # try to pull summary metrics from valuation / companies
    # companies table row
    if company_rec:
        col1.metric("Company", company_rec.get("company_name") or company_display)
        col2.metric("Country", company_rec.get("country") or "N/A")
        col3.metric("Industry", company_rec.get("industry") or "N/A")
    else:
        col1.metric("Company", company_display)
        col2.metric("Country", "N/A")
        col3.metric("Industry", "N/A")

    st.markdown("**Fundamentals & Metrics**")
    # For each selected metric table, fetch rows and pretty display — show short preview first
    metrics_cols = st.columns(len(selected_metrics)) if selected_metrics else []

    # We will display each metric in a small json-like box (but prettified)
    for idx, metric in enumerate(selected_metrics):
        # mapping metric -> table name
        table_map = {
            "valuation": "valuation",
            "profitability": "profitability",
            "growth": "growth",
            "balance": "balance",
            "cashflow": "cashflow",
            "dividends": "dividends",
            "recommendations": "recommendations",
        }
        table_name = table_map.get(metric, metric)
        rows = get_table_by_company_id_or_ticker(table_name, company_id=company_id, ticker=ticker_display)
        # show a small preview card for the first row
        with st.expander(f"📦 {metric.title()} (preview)"):
            if rows:
                pretty = pretty_row_for_display(rows[0])
                # display key-values in two columns
                for k, v in pretty.items():
                    st.markdown(f"**{k}:** {v}")
                if len(rows) > 1:
                    st.caption(f"{len(rows)} rows in table '{table_name}'. Expand backend to inspect more.")
            else:
                st.info(f"No {metric} data found in table '{table_name}'.")

    st.divider()

    # Filings — show 2 visible, expandable list for more
    st.subheader("📂 Latest Filings (Active)")
    try:
        filings_resp = supabase.table("filings").select("*").eq("ticker", ticker_display).order("next_earnings_date", desc=False).execute()
        filings_rows = filings_resp.data or []
        if filings_rows:
            # show up to 2 inline expanders, rest inside a 'Show more' expander
            for fr in filings_rows[:2]:
                with st.expander(f"🗂️ {fr.get('company_name', ticker_display)} — Next: {fr.get('next_earnings_date', 'N/A')}"):
                    st.markdown(f"**Next Earnings Date:** {fr.get('next_earnings_date', 'N/A')}")
                    st.markdown(f"**Pending:** {'Yes' if fr.get('pending_filing') else 'No'}")
                    st.markdown(f"**Source:** {fr.get('filing_source', 'N/A')}")
                    if fr.get("filing_link"):
                        st.markdown(f"[🔗 Filing Link]({fr.get('filing_link')})", unsafe_allow_html=True)
            if len(filings_rows) > 2:
                with st.expander("📜 Show More Filings (scrollable)"):
                    st.markdown("<div class='scrollable-section'>", unsafe_allow_html=True)
                    for fr in filings_rows[2:]:
                        st.markdown(f"**{fr.get('company_name','')}:** Next {fr.get('next_earnings_date','N/A')} — Source: {fr.get('filing_source','N/A')}")
                        if fr.get("filing_link"):
                            st.markdown(f"[🔗 Filing Link]({fr.get('filing_link')})", unsafe_allow_html=True)
                        st.markdown("---")
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No active filings for this ticker.")
    except Exception as e:
        st.error(f"Error loading filings: {e}")

    st.divider()

    # Filing history
    st.subheader("🕘 Filing History")
    try:
        history_resp = supabase.table("filings_history").select("*").eq("ticker", ticker_display).order("expected_date", desc=True).limit(200).execute()
        history_rows = history_resp.data or []
        if history_rows:
            # show 2 expanders, rest in Show More
            for hr in history_rows[:2]:
                with st.expander(f"📅 {hr.get('expected_date','N/A')} — {hr.get('filing_title','Untitled')}"):
                    st.markdown(f"**Event:** {hr.get('event_type','N/A')}")
                    st.markdown(f"**Classification:** {hr.get('classification_label','N/A')} ({hr.get('classification_score','N/A')})")
                    if hr.get("filing_url"):
                        st.markdown(f"[🔗 View Source]({hr.get('filing_url')})", unsafe_allow_html=True)
            if len(history_rows) > 2:
                with st.expander("📜 Show More History (scrollable)"):
                    st.dataframe(pd.DataFrame(history_rows).drop(columns=[c for c in ['id','notes','filing_text','filing_summary','run_timestamp'] if c in (pd.DataFrame(history_rows).columns)]), use_container_width=True)
        else:
            st.info("No filing history found.")
    except Exception as e:
        st.error(f"Error loading filing history: {e}")

    st.divider()

    # News — use fetch_news for display, but news were already pushed_to_db by push_news earlier
    st.subheader("📰 Latest News (combined Yahoo + Google RSS)")
    try:
        # Try to show the last pushed news snapshot from news table if present
        news_snapshot = supabase.table("news").select("*").eq("ticker", ticker_display).limit(1).execute()
        snapshot_rows = news_snapshot.data or []
        if snapshot_rows:
            news_list = snapshot_rows[0].get("news") or []
        else:
            # fallback to runtime fetch
            news_list = fetch_news(ticker_display, company_display)
    except Exception:
        news_list = []

    if news_list:
        for item in (news_list[:2] if isinstance(news_list, list) else []):
            with st.expander(f"🗞️ {item.get('title','Untitled')}"):
                st.markdown(f"**Source:** {item.get('source','N/A')} • **Published:** {item.get('published','N/A')}")
                st.markdown(f"{item.get('summary','')[:500]}{'...' if item.get('summary') and len(item.get('summary'))>500 else ''}")
                if item.get("link"):
                    st.markdown(f"[🔗 Read full article]({item.get('link')})", unsafe_allow_html=True)
        if isinstance(news_list, list) and len(news_list) > 2:
            with st.expander("📰 Show More News (scrollable)"):
                st.markdown("<div class='scrollable-section'>", unsafe_allow_html=True)
                for item in news_list[2:]:
                    st.markdown(f"**{item.get('title','Untitled')}** — {item.get('source','N/A')} — {item.get('published','N/A')}")
                    st.markdown(f"[Read]({item.get('link','#')})", unsafe_allow_html=True)
                    st.markdown("---")
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No recent news available.")
