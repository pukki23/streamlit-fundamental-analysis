import streamlit as st
import requests

def run_finbert_analysis(text):
    """Send text to FinBERT for financial sentiment/analysis using Streamlit Secrets."""
    api_token = st.secrets.get("HUGGINGFACE_API_TOKEN", None)

    if not api_token:
        return "⚠️ Missing Hugging Face API token in Streamlit secrets."

    headers = {"Authorization": f"Bearer {api_token}"}
    API_URL = "https://api-inference.huggingface.co/models/ProsusAI/finbert"

    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": text}, timeout=30)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            top = max(result[0], key=lambda x: x['score'])
            sentiment = top['label']
            score = round(top['score'] * 100, 2)
            return f"🧠 **FinBERT Sentiment:** {sentiment} ({score}% confidence)"
        else:
            return "⚠️ Unexpected FinBERT response format."
    except Exception as e:
        return f"❌ FinBERT error: {str(e)}"
