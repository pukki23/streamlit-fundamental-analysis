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
    with open("assets/style.css") as f:
        css = f.read()
    if theme == "dark":
        css += """
        body, .stApp { background-color: #0f172a !important; color: #f1f5f9 !important; }
        .main-title, h1, h2, h3, .subtitle { color: #93c5fd !important; }
        .filing-card, .nav-card { background-color: #1e293b !important; border-color: #334155 !important; }
        """
    # Add floating toggle button style
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
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css(theme)

# === Floating Theme Toggle ===
icon = "🌙" if theme == "light" else "🌞"
if st.button(icon, key="theme_toggle", help="Switch Theme", use_container_width=False):
    toggle_theme()

# Fix placement (since Streamlit buttons don’t natively float)
st.markdown(f"<div class='theme-toggle' onclick='window.location.reload()'>{icon}</div>", unsafe_allow_html=True)

# === MAIN CONTENT ===
st.markdown("<h1 class='main-title'>📈 Financial Filings & News App</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Select a page from the sidebar to get started.</p>", unsafe_allow_html=True)
