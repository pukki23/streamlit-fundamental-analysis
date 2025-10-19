import streamlit as st
import requests, json
from datetime import datetime
from supabase_client import supabase
from scripts.analysis_module import analyze_ticker  # ✅ triggers the data refresh

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="🤖 LLM Analysis", layout="wide")
st.title("🤖 AI Fundamental Analysis (FinBERT-powered)")

# ---------------- HELPER: FETCH DATA FROM SUPABASE ----------------
def fetch_metric_data(ticker):
    """Collect all related metric tables for the given ticker."""
    tables = [
        "valuation", "profitability", "growth",
        "balance", "cashflow", "dividends", "recommendations"
    ]
    collected_data = {}
    for table in tables:
        res = supabase.table(table).select("*").ilike("ticker", ticker).execute()
        if res.data:
            collected_data[table] = res.data[0]
    return collected_data


# ---------------- HELPER: CALL HUGGINGFACE MODEL ----------------
def run_finbert_analysis(ticker, collected_data):
    hf_token = st.secrets["HUGGINGFACE_API_TOKEN"]
    headers = {"Authorization": f"Bearer {hf_token}"}
    model_url = "https://api-inference.huggingface.co/models/yiyanghkust/finbert-tone"

    prompt = f"""
    You are an expert financial analyst.
    Perform an in-depth *fundamental analysis* for company ticker {ticker}.
    Use only the data provided below, which includes key metrics across categories.

    DATA SOURCE (metrics selected):
    {json.dumps(collected_data, indent=2)}

    Your response must:
    - Reference the metrics that guided your reasoning
    - Highlight strengths, weaknesses, and growth potential
    - Conclude with a **suggested confidence score (0–100%)**
    - Include the disclaimer: "This is not financial advice."
    """

    with st.spinner("Running FinBERT analysis... please wait..."):
        response = requests.post(model_url, headers=headers, json={"inputs": prompt}, timeout=180)

    if response.status_code == 200:
        try:
            result = response.json()
            if isinstance(result, list):
                return result[0].get("generated_text", "No analysis returned.")
            return str(result)
        except Exception:
            return str(result)
    else:
        return f"❌ Error: {response.text}"


# ---------------- SECTION: HISTORY ----------------
st.subheader("📜 Recent Analyses")

if "analysis_history" not in st.session_state:
    history_resp = supabase.table("llm_analysis").select("*").order("created_at", desc=True).limit(10).execute()
    st.session_state.analysis_history = history_resp.data or []

history = st.session_state.analysis_history

if history:
    selected_analysis = st.selectbox(
        "View Past Analyses (select one):",
        options=["(None)"] + [f"{h['ticker']} — {h['created_at'][:19]}" for h in history]
    )
    if selected_analysis != "(None)":
        chosen = next(
            (h for h in history if f"{h['ticker']} — {h['created_at'][:19]}" == selected_analysis),
            None,
        )
        if chosen:
            st.markdown(f"### 📈 {chosen['ticker']}")
            st.markdown(chosen["analysis_result"])
            st.caption("_This is a previously saved analysis._")
            st.stop()
else:
    st.info("No past analyses found yet.")

# ---------------- SECTION: NEW ANALYSIS ----------------
st.subheader("🧩 Run a New Analysis")

ticker = st.text_input("Enter Ticker Symbol (e.g. AAPL, TSLA, MTN):", "").strip().upper()
run_button = st.button("🚀 Run New Analysis")

if run_button:
    if not ticker:
        st.error("Please enter a valid ticker.")
    else:
        with st.spinner("🔄 Refreshing fundamental data..."):
            analyze_ticker(ticker, [
                "valuation", "profitability", "growth", "balance",
                "cashflow", "dividends", "recommendations"
            ])

        metric_data = fetch_metric_data(ticker)
        if not metric_data:
            st.warning(f"No metrics found for ticker '{ticker}' in Supabase.")
        else:
            result = run_finbert_analysis(ticker, metric_data)

            st.subheader("📊 AI Fundamental Analysis Result")
            st.markdown(result)
            st.caption("_Note: This analysis references the selected metrics and is not financial advice._")

            # Save to database
            entry = {
                "ticker": ticker,
                "analysis_result": result,
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("llm_analysis").insert(entry).execute()

            # Add new result to session history dynamically
            st.session_state.analysis_history.insert(0, entry)
            st.success("✅ Analysis saved and added to history.")
