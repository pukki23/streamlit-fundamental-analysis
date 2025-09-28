import feedparser
from datetime import datetime, timezone
from supabase_client import supabase

def fetch_filings(company_name, max_results=20):
    query = f"{company_name} filing OR prospectus OR report OR notice"
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
    feed = feedparser.parse(rss_url)
    filings = []
    for entry in feed.entries[:max_results]:
        filings.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published"),
            "summary": entry.get("summary"),
        })
    return filings

def push_filings(ticker, company_name, filings):
    run_time = datetime.now(timezone.utc).isoformat()
    record = {"company_name": company_name, "ticker": ticker, "run_timestamp": run_time, "filings": filings}
    supabase.table("filings").delete().eq("ticker", ticker).execute()
    supabase.table("filings").insert(record).execute()
    supabase.table("filings_history").insert(record).execute()
