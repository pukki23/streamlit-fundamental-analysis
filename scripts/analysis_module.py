import yfinance as yf
from datetime import datetime, timezone
from supabase_client import supabase

def upsert_record(table, unique_field, match_value, record):
    """Upsert record into Supabase with created_at/updated_at"""
    now = datetime.now(timezone.utc).isoformat()
    record["updated_at"] = now
    res = supabase.table(table).update(record).eq(unique_field, match_value).execute()
    if res.data:
        return res.data[0].get("id")
    record["created_at"] = now
    res = supabase.table(table).insert(record).execute()
    return res.data[0].get("id") if res.data else None

def analyze_ticker(ticker: str, metrics: list):
    """Analyze a ticker and push selected metrics to Supabase"""
    ticker = ticker.upper()
    stock = yf.Ticker(ticker)
    info = stock.info or {}
    company_name = info.get("longName") or info.get("shortName") or ticker

    # Companies table
    company_payload = {
        "company_name": company_name,
        "ticker": ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "currency": info.get("currency"),
    }
    company_id = upsert_record("companies", "ticker", ticker, company_payload)

    results = {"company_id": company_id, "company_name": company_name}

    # Optional metrics
    if "valuation" in metrics:
        val = {
            "company_id": company_id,
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "uniquekey": f"{ticker}_valuation",
        }
        upsert_record("valuation", "uniquekey", val["uniquekey"], val)
        results["valuation"] = val

    if "profitability" in metrics:
        prof = {
            "company_id": company_id,
            "profit_margins": info.get("profitMargins"),
            "return_on_assets": info.get("returnOnAssets"),
            "return_on_equity": info.get("returnOnEquity"),
            "uniquekey": f"{ticker}_profitability",
        }
        upsert_record("profitability", "uniquekey", prof["uniquekey"], prof)
        results["profitability"] = prof

    if "growth" in metrics:
        growth = {
            "company_id": company_id,
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "quarterly_revenue_growth": info.get("quarterlyRevenueGrowth"),
            "quarterly_earnings_growth": info.get("quarterlyEarningsGrowth"),
            "uniquekey": f"{ticker}_growth",
        }
        upsert_record("growth", "uniquekey", growth["uniquekey"], growth)
        results["growth"] = growth

    if "balance" in metrics:
        balance = {
            "company_id": company_id,
            "total_debt": info.get("totalDebt"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "uniquekey": f"{ticker}_balance",
        }
        upsert_record("balance", "uniquekey", balance["uniquekey"], balance)
        results["balance"] = balance

    if "cashflow" in metrics:
        cashflow = {
            "company_id": company_id,
            "free_cash_flow": info.get("freeCashflow"),
            "operating_cash_flow": info.get("operatingCashflow"),
            "gross_profits": info.get("grossProfits"),
            "ebitda": info.get("ebitda"),
            "uniquekey": f"{ticker}_cashflow",
        }
        upsert_record("cashflow", "uniquekey", cashflow["uniquekey"], cashflow)
        results["cashflow"] = cashflow

    if "dividends" in metrics:
        dividends = {
            "company_id": company_id,
            "dividend_rate": info.get("dividendRate"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "uniquekey": f"{ticker}_dividends",
        }
        upsert_record("dividends", "uniquekey", dividends["uniquekey"], dividends)
        results["dividends"] = dividends

    # Recommendations
    if "recommendations" in metrics:
        try:
            recs = stock.recommendations_summary
        except Exception:
            recs = None
        rec_list = []
        if recs is not None and not recs.empty:
            for period, row in recs.iterrows():
                rec_record = {
                    "company_id": company_id,
                    "period": str(period),
                    "strong_buy": row.get("strongBuy"),
                    "buy": row.get("buy"),
                    "hold": row.get("hold"),
                    "sell": row.get("sell"),
                    "strong_sell": row.get("strongSell"),
                    "uniquekey": f"{ticker}_{period}",
                }
                upsert_record("recommendations", "uniquekey", rec_record["uniquekey"], rec_record)
                rec_list.append(rec_record)
        results["recommendations"] = rec_list

    return results
