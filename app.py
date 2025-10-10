import streamlit as st
from datetime import datetime

# === PAGE CONFIG ===
st.set_page_config(
    page_title="📁 Financial Filings Tracker",
    layout="wide",
    page_icon="📈"
)

# === Load CSS ===
def load_css(theme="light"):
    """Load base CSS + theme overrides."""
    try:
        with open("assets/style.css") as f:
            css = f.read()

        # Inject theme-specific overrides
        if theme == "dark":
            css += """
                body, .stApp {
                    background-color: #0f172a !important;
                    color: #f1f5f9 !important;
                }
                .main-title, .filing-title, h3 {
                    color: #93c5fd !important;
                }
                .subtitle, .filing-meta, p, label, .footer {
                    color: #cbd5e1 !important;
                }
                .nav-card, .filing-card {
                    background-color: #1e293b !important;
                    border-color: #334155 !important;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
                }
                .nav-button {
                    background-color: #2563eb !important;
                    color: white !important;
                }
                .nav-button:hover {
                    background-color: #1d4ed8 !important;
                }
            """
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ CSS file not found at 'assets/style.css'. Please ensure it exists.")


# === THEME TOGGLE (Persistent via Session State) ===
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

col1, col2 = st.columns([8, 2])
with col2:
    theme_choice = st.toggle("🌗 Dark Mode", value=st.session_state["theme"] == "dark")
    st.session_state["theme"] = "dark" if theme_choice else "light"

# Apply CSS based on current theme
load_css(st.session_state["theme"])

# === HEADER ===
st.markdown("<h1 class='main-title'>📁 Financial Filings Tracker</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Track company filings, earnings, and financial reports effortlessly</p>", unsafe_allow_html=True)

# --- Welcome Banner ---
st.markdown(
    """
    <div class='welcome-card'>
        <p>
            Welcome to your unified <strong>Financial Filings Tracker</strong> dashboard.<br>
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
