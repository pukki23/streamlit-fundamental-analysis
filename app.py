import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Missing Supabase credentials in .env file")
    st.stop()

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- UI ---
st.set_page_config(page_title="📊 Fundamental Analysis Dashboard", layout="wide")
st.title("📊 Fundamental Analysis Dashboard")

# Sidebar filters
st.sidebar.header("⚙️ Filters")
ticker = st.sidebar.text_input("Company Ticker", "AAPL")

# Example: fetch data from Supabase
if st.sidebar.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        response = supabase.table("companies").select("*").eq("ticker", ticker).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            st.success(f"✅ Found {len(df)} records for {ticker}")
            st.dataframe(df)
        else:
            st.warning("⚠️ No data found for this ticker.")

# Example: Show all metrics table
if st.checkbox("Show All Metrics Table"):
    response = supabase.table("metrics").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)
        st.dataframe(df)
