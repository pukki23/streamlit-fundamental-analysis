import yfinance as yf
from datetime import datetime, timezone, timedelta
import feedparser
from supabase_client import supabase

def fetch_news(ticker, company_name, days=14):
    """Fetch news (Yahoo Finance + Google News RSS)"""
    news_items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Yahoo Finance
    try:
        ynews = yf.Ticker(ticker).news
    except Exception:
        ynews = []

    for item in ynews or []:
        dt = datetime.fromtimestamp(item.get("providerPublishTime", 0), tz=timezone.utc)
        if dt < cutoff:
            continue
        news_items.append({
            "source": "Yahoo Finance",
            "title": item.get("title"),
            "link": item.get("link"),
            "publisher": item.get("publisher"),
            "published": dt.isoformat()
        })

    # Google News RSS
    rss_url = f"https://news.google.com/rss/search?q={company_name.replace(' ','+')}"
    feed = feedparser.parse(rss_url)
    for entry in feed.entries:
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            dt = datetime.fromtimestamp(
                datetime(*published_parsed[:6]).timestamp(), tz=timezone.utc
            )
            if dt < cutoff:
                continue
        else:
            dt = None
        news_items.append({
            "source": "Google News RSS",
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": dt.isoformat() if dt else None
        })
    return news_items

def push_news(ticker, company_name):
    news_items = fetch_news(ticker, company_name)
    record = {
        "company_name": company_name,
        "ticker": ticker,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "news": news_items
    }
    # Replace latest news
    supabase.table("news").delete().eq("ticker", ticker).execute()
    supabase.table("news").insert(record).execute()
    supabase.table("news_history").insert(record).execute()
    return news_items
