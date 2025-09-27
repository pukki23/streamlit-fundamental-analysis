import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- Load Supabase credentials from Streamlit Secrets ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Missing Supabase credentials in Streamlit Secrets")
    st.stop()

# --- Initialize Supabase client ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- UI Config ---
st.set_page_config(page_title="📊 Fundamental Analysis Dashboard", layout="wide")
st.title("📊 Fundamental Analysis Dashboard")

# --- Sidebar filters ---
st.sidebar.header("⚙️ Filters")
ticker_filter = st.sidebar.text_input("Company Ticker (optional)", "")

# --- Supabase tables ---
tables = [
    "companies",
    "valuation",
    "profitability",
    "growth",
    "balance",
    "cashflow",
    "dividends",
    "recommendations",
    "fundamentals_history",
    "filings",
    "filings_history",
    "news",
    "news_history",
]

# --- Create tabs for each table ---
tabs = st.tabs(tables)

for tab_name, tab in zip(tables, tabs):
    with tab:
        st.header(f"📋 {tab_name.replace('_',' ').title()} Table")
        
        # Fetch data with optional ticker filter
        query = supabase.table(tab_name).select("*")
        # Only apply ticker filter if column exists
        if ticker_filter:
            try:
                # Test if 'ticker' column exists by checking first row
                test_data = query.limit(1).execute()
                if test_data.data and "ticker" in test_data.data[0]:
                    query = query.eq("ticker", ticker_filter)
            except:
                pass
        
        response = query.execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            st.success(f"✅ Found {len(df)} records in {tab_name}")
            st.dataframe(df)
        else:
            st.warning(f"⚠️ No data found in {tab_name}")
