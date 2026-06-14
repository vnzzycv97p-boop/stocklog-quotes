"""
fetch_quotes.py
----------------
Fetches current price, % change, previous close, and previous volume
for all StockLog tickers using yfinance, and writes the result to
quotes.json.
 
Tickers are read from tickers.json, which StockLog (via the
stocklog-sync Cloudflare Worker) keeps up to date automatically.
If tickers.json doesn't exist yet (first run), falls back to the
DEFAULT_TICKERS list below.
 
This script is run automatically once a day by GitHub Actions
(see .github/workflows/update.yml), so the StockLog app can simply
fetch quotes.json to get fresh prices without hitting any API
rate limits.
"""
 
import json
import os
import yfinance as yf
from datetime import datetime, timezone
 
# Fallback list, used only if tickers.json is missing or empty.
DEFAULT_TICKERS = [
    "LLY", "AMD", "AGX", "BAND",
    "BE", "SNDK", "HUT", "TTMI", "MXL", "STX", "MU",
    "AXT", "VIAV", "AAOI", "LITE", "LRCX", "KEYS",
    "VPG", "SPOT", "CIEN", "MS", "TXN", "GS", "WULF", "LWLG", "SILC",
]
 
TICKERS_FILE = "tickers.json"
QUOTES_FILE = "quotes.json"
 
 
def load_tickers() -> list[str]:
    """Read the ticker list StockLog has synced via the Cloudflare Worker."""
    if os.path.exists(TICKERS_FILE):
        try:
            with open(TICKERS_FILE) as f:
                data = json.load(f)
            tickers = data.get("tickers", [])
            if tickers:
                print(f"Loaded {len(tickers)} tickers from {TICKERS_FILE}")
                return tickers
        except Exception as e:
            print(f"  ! could not read {TICKERS_FILE}: {e}")
 
    print(f"Falling back to DEFAULT_TICKERS ({len(DEFAULT_TICKERS)} tickers)")
    return DEFAULT_TICKERS
 
 
def fetch_one(ticker: str) -> dict | None:
    """Fetch price/change/prevClose/prevVolume for a single ticker."""
    try:
        t = yf.Ticker(ticker)
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
    tickers = load_tickers()
    results = {}
    print(f"Fetching {len(tickers)} tickers...")
    for ticker in tickers:
        print(f"  {ticker}...")
        data = fetch_one(ticker)
        if data:
            results[ticker] = data
 
    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "quotes": results,
    }
 
    with open(QUOTES_FILE, "w") as f:
        json.dump(output, f, indent=2)
 
    print(f"Done. Wrote {len(results)}/{len(tickers)} quotes to {QUOTES_FILE}")
 
 
if __name__ == "__main__":
    main()
 
