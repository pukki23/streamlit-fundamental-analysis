import streamlit as st
from supabase import create_client, Client

# Read from Streamlit secrets instead of .env
SUPABASE_URL = st.secrets["NEXT_PUBLIC_SUPABASE_URL"]
SUPABASE_KEY = st.secrets["NEXT_PUBLIC_SUPABASE_ANON_KEY"]

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
