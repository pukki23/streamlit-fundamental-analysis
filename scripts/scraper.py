import feedparser
from newspaper import Article
import trafilatura
import datetime


def fetch_recent_filings_from_news(company_name):
    """Fetch most recent filings or financial report news articles."""
    query = f"{company_name} financial report OR earnings OR results OR filing"
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries[:10]:
        articles.append({
            "title": entry.title,
            "summary": entry.get("summary", ""),
            "link": entry.link,
            "published": entry.get("published", ""),
        })
    return articles


def extract_full_text(url):
    """Hybrid extractor using trafilatura and newspaper3k."""
    text = ""
    try:
        downloaded = trafilatura.fetch_url(url, timeout=15)
        if downloaded:
            text = trafilatura.extract(downloaded)
    except Exception:
        pass

    if not text:
        try:
            article = Article(url)
            article.download()
            article.parse()
            text = article.text
        except Exception:
            pass

    return text.strip() if text else ""


def find_and_extract_latest_filing(company_name):
    """Find the latest news related to the company's financial filing."""
    articles = fetch_recent_filings_from_news(company_name)
    if not articles:
        return None

    # Get the most relevant article (latest)
    latest = articles[0]
    full_text = extract_full_text(latest["link"])

    return {
        "filing_url": latest["link"],
        "filing_title": latest["title"],
        "filing_summary": latest.get("summary", ""),
        "filing_text": full_text,
        "fetched_from": "google_news",
    }
