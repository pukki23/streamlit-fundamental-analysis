import streamlit as st
from pathlib import Path

# ---------- Inject CSS ----------
css_path = Path("assets/style.css")
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

#----------- Show Streamlit Version ----------
st.sidebar.info(f"Streamlit version: {st.__version__}")

# ---------- Landing Section ----------
st.markdown("""
<div class='landing-container'>
    <h1>📊 Fundamental & Filings Dashboard</h1>
    <p>Explore insights, data, and filings using an intuitive interface.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Navigation Cards ----------
st.markdown("""
<div class='card-container'>

    <a href="pages/Frontend_Viewer" target="_self" class="nav-card">
        <div class="icon">🧭</div>
        <h3>Frontend Viewer</h3>
        <p>Explore company data, filings, and insights in a user-friendly view.</p>
    </a>

    <a href="pages/Backend_Dashboard" target="_self" class="nav-card">
        <div class="icon">⚙️</div>
        <h3>Backend Dashboard</h3>
        <p>Admin tools for filings, scrapers, and backend management.</p>
    </a>

</div>
""", unsafe_allow_html=True)
