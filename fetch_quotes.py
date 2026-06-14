"""
fetch_quotes.py
----------------
Fetches current price, % change, previous close, and previous volume
for all StockLog tickers using yfinance, and writes the result to
quotes.json.

This script is run automatically once a day by GitHub Actions
(see .github/workflows/update.yml), so the StockLog app can simply
fetch this JSON file to get fresh prices without hitting any
API rate limits.
"""

import json
import yfinance as yf
from datetime import datetime, timezone

# ============================================================
# EDIT THIS LIST to match the tickers you track in StockLog.
# Add/remove tickers here whenever your stock universe changes.
# ============================================================
TICKERS = [
    # PRIME
    "LLY", "AMD", "AGX", "BAND",
    # FOCUS
    "BE", "SNDK", "HUT", "TTMI", "MXL", "STX", "MU",
    # CANDIDATE
    "AXT", "VIAV", "AAOI", "LITE", "LRCX", "KEYS",
    # WATCHLIST
    "VPG", "SPOT", "CIEN", "MS", "TXN", "GS", "WULF", "LWLG", "SILC",
]


def fetch_one(ticker: str) -> dict | None:
    """Fetch price/change/prevClose/prevVolume for a single ticker."""
    try:
        t = yf.Ticker(ticker)
        # 2 days of daily data is enough to get "today" + "previous day"
        hist = t.history(period="5d")
        if hist.empty:
            print(f"  ! no data for {ticker}")
            return None

        last_row = hist.iloc[-1]
        price = round(float(last_row["Close"]), 2)

        if len(hist) >= 2:
            prev_row = hist.iloc[-2]
            prev_close = round(float(prev_row["Close"]), 2)
            prev_volume = int(prev_row["Volume"])
        else:
            prev_close = price
            prev_volume = int(last_row["Volume"])

        change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0.0
        change_str = ("+" if change_pct >= 0 else "") + f"{change_pct}%"

        return {
            "price": f"{price:.2f}",
            "change": change_str,
            "prevClose": f"{prev_close:.2f}",
            "prevVolume": str(prev_volume),
        }
    except Exception as e:
        print(f"  ! error fetching {ticker}: {e}")
        return None


def main():
    results = {}
    print(f"Fetching {len(TICKERS)} tickers...")
    for ticker in TICKERS:
        print(f"  {ticker}...")
        data = fetch_one(ticker)
        if data:
            results[ticker] = data

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "quotes": results,
    }

    with open("quotes.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Done. Wrote {len(results)}/{len(TICKERS)} quotes to quotes.json")


if __name__ == "__main__":
    main()
