import yfinance as yf
import feedparser
import time
from datetime import datetime, timezone, timedelta
from supabase_client import supabase

def fetch_news(ticker, company_name, days=14):
    news_items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stock = yf.Ticker(ticker)

    # Yahoo Finance
    try:
        for item in stock.news or []:
            dt = datetime.fromtimestamp(item.get("providerPublishTime", 0), tz=timezone.utc)
            if dt < cutoff: continue
            news_items.append({
                "source": "Yahoo Finance",
                "title": item.get("title"),
                "link": item.get("link"),
                "publisher": item.get("publisher"),
                "published": dt.isoformat(),
            })
    except Exception:
        pass

    # Google News RSS
    rss_url = f"https://news.google.com/rss/search?q={company_name.replace(' ', '+')}"
    feed = feedparser.parse(rss_url)
    for entry in feed.entries:
        published_parsed = entry.get("published_parsed")
        if not published_parsed: continue
        dt = datetime.fromtimestamp(time.mktime(published_parsed), tz=timezone.utc)
        if dt < cutoff: continue
        news_items.append({
            "source": "Google News RSS",
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": dt.isoformat(),
        })

    return news_items

def push_news(ticker, company_name, news_items):
    run_time = datetime.now(timezone.utc).isoformat()
    record = {"company_name": company_name, "ticker": ticker, "run_timestamp": run_time, "news": news_items}
    supabase.table("news").delete().eq("ticker", ticker).execute()
    supabase.table("news").insert(record).execute()
    supabase.table("news_history").insert(record).execute()
