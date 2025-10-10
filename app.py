import streamlit as st
from datetime import datetime

# === Load Custom CSS ===
def load_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ CSS file not found at 'assets/style.css'. Please make sure it exists.")

load_css()

# === PAGE CONFIG ===
st.set_page_config(
    page_title="📁 Financial Filings Tracker",
    layout="wide",
    page_icon="📈"
)

# === HEADER ===
st.markdown("<h1 class='main-title'>📁 Financial Filings Tracker</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Track company filings, earnings, and financial reports effortlessly</p>", unsafe_allow_html=True)

# --- Welcome Banner ---
st.markdown(
    """
    <div class='welcome-card'>
        <p>
            Welcome to your unified <strong>Financial Filings Tracker</strong> dashboard.  
            Use the panels below to navigate between the <strong>Backend Admin Dashboard</strong>  
            and the <strong>Frontend Viewer</strong> for end users.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Split Columns for Navigation ---
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div class='nav-card'>
            <h3>⚙️ Backend Dashboard</h3>
            <p>
                Manage and analyze filings, company metrics, and financial data directly from your Supabase instance.
            </p>
            <a class='nav-button' href='/1_%F0%9F%93%8A_Backend_Dashboard' target='_self'>
                Open Backend Dashboard
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class='nav-card'>
            <h3>🖥️ Frontend Viewer</h3>
            <p>
                User-friendly interface to browse filings, news, and company insights in a card-based format.
            </p>
            <a class='nav-button' href='/2_%F0%9F%96%A5%EF%B8%8F_Frontend_Viewer' target='_self'>
                Open Frontend Viewer
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Footer Section ---
st.markdown(
    f"""
    <hr class='divider'>
    <div class='footer'>
        <p>🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Built with ❤️ using Streamlit and Supabase</p>
    </div>
    """,
    unsafe_allow_html=True,
)
