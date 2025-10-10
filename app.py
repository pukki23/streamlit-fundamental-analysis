import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Financial Filings App", layout="wide")

# === Theme Setup ===
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

def toggle_theme():
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"
    st.rerun()

theme = st.session_state["theme"]

# === Load CSS ===
def load_css(theme="light"):
    css_path = Path("assets/style.css")
    if css_path.exists():
        with open(css_path) as f:
            css = f.read()
    else:
        css = ""

    if theme == "dark":
        css += """
        body, .stApp { background-color: #0f172a !important; color: #f1f5f9 !important; }
        .main-title, h1, h2, h3, .subtitle { color: #93c5fd !important; }
        .filing-card, .nav-card { background-color: #1e293b !important; border-color: #334155 !important; }
        """

    css += """
    .theme-toggle {
        position: fixed;
        top: 20px;
        right: 25px;
        background-color: #2563eb;
        color: white;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        text-align: center;
        line-height: 40px;
        cursor: pointer;
        font-size: 20px;
        z-index: 9999;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .theme-toggle:hover {
        background-color: #1d4ed8;
        transform: scale(1.1);
    }
    .nav-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        background-color: white;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .nav-card:hover {
        transform: scale(1.03);
        background-color: #f8fafc;
        border-color: #93c5fd;
    }
    .nav-link {
        text-decoration: none;
        font-size: 18px;
        color: #1e3a8a;
        font-weight: 600;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css(theme)

# === Floating Theme Toggle ===
icon = "🌙" if theme == "light" else "🌞"
st.markdown(f"<div class='theme-toggle' onclick='window.location.reload()'>{icon}</div>", unsafe_allow_html=True)

# === MAIN CONTENT ===
st.markdown("<h1 class='main-title' style='text-align:center;'>📊 Financial Filings & News Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle' style='text-align:center;'>Track filings, analyze fundamentals, and read financial news.</p>", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class='nav-card'>
        <h3>🧭 Frontend Viewer</h3>
        <p>A user-friendly interface to browse company fundamentals, filings, and financial reports.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/Frontend_Viewer.py", label="➡️ Go to Frontend Viewer")

with col2:
    st.markdown("""
    <div class='nav-card'>
        <h3>⚙️ Backend Dashboard</h3>
        <p>Manage filings data, trigger scrapers, and monitor system-wide analytics.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/Backend_Dashboard.py", label="➡️ Go to Backend Dashboard")

st.markdown("---")
st.caption("💡 Tip: Use the 🌙 button at the top-right corner to toggle dark/light mode.")
