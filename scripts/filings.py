import datetime
from supabase_client import supabase
from scripts.scraper import find_and_extract_latest_filing


def save_or_update_filing(ticker, company_name, next_date, source="manual"):
    """Insert or update a filing record in the 'filings' table."""
    record = {
        "company_name": company_name,
        "ticker": ticker,
        "next_earnings_date": next_date,
        "pending_filing": True,
        "last_checked": datetime.datetime.utcnow().isoformat(),
        "filing_source": source,
        "past_earnings_dates": [],
        "next_earnings_dates": [],
    }

    existing = supabase.table("filings").select("*").eq("ticker", ticker).execute().data
    if existing:
        supabase.table("filings").update(record).eq("ticker", ticker).execute()
        return "updated"
    else:
        supabase.table("filings").insert(record).execute()
        return "inserted"


def archive_filing_to_history(filing, filing_data=None):
    """Move a filing record to history, optionally including scraped data."""
    entry = {
        "ticker": filing["ticker"],
        "company_name": filing["company_name"],
        "event_type": "earning",
        "expected_date": filing["next_earnings_date"],
        "fetched_from": filing.get("filing_source", "unknown"),
        "notes": "Auto-archived after release",
    }

    if filing_data:
        entry.update({
            "filing_url": filing_data.get("filing_url"),
            "filing_title": filing_data.get("filing_title"),
            "filing_summary": filing_data.get("filing_summary"),
            "filing_text": filing_data.get("filing_text"),
        })

    supabase.table("filings_history").insert(entry).execute()
    supabase.table("filings").delete().eq("ticker", filing["ticker"]).execute()


def process_expired_or_due_filings():
    """Detect filings that are due today or past due and scrape their data."""
    now = datetime.datetime.utcnow()
    due_filings = (
        supabase.table("filings")
        .select("*")
        .lte("next_earnings_date", now.isoformat())
        .execute()
        .data or []
    )

    processed = 0
    for filing in due_filings:
        filing_data = find_and_extract_latest_filing(filing["company_name"])
        archive_filing_to_history(filing, filing_data)
        processed += 1

    return processed


def get_next_filing():
    """Return the next upcoming filing."""
    response = (
        supabase.table("filings")
        .select("*")
        .order("next_earnings_date", desc=False)
        .limit(1)
        .execute()
    )
    data = response.data
    return data[0] if data else None
