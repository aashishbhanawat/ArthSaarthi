import sys
import logging
import json
import os
from datetime import datetime, timedelta

# Attempt to import defeatbeta_api
try:
    from defeatbeta_api.data.ticker import Ticker
    DEFEATBETA_AVAILABLE = True
except ImportError:
    DEFEATBETA_AVAILABLE = False

# Attempt to import yfinance for comparison
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def evaluate_ticker(symbol):
    results = {
        "symbol": symbol,
        "defeatbeta": {"status": "skipped", "data": None, "error": None},
        "yfinance": {"status": "skipped", "data": None, "error": None}
    }

    print(f"\n{'='*20} Evaluating: {symbol} {'='*20}")

    # 1. Evaluate defeatbeta-api
    if DEFEATBETA_AVAILABLE:
        try:
            print(f"Testing defeatbeta-api for {symbol}...")
            ticker = Ticker(symbol)
            
            # Fetch current price (or most recent price)
            price_data = ticker.price()
            
            results["defeatbeta"]["status"] = "success"
            results["defeatbeta"]["data"] = str(price_data) # Convert to string for display
            print(f"Defeatbeta Success: {price_data}")
            
        except Exception as e:
            results["defeatbeta"]["status"] = "error"
            results["defeatbeta"]["error"] = str(e)
            print(f"Defeatbeta Error: {e}")
    else:
        results["defeatbeta"]["status"] = "missing_package"
        print("Defeatbeta Error: defeatbeta-api package not found.")

    # 2. Evaluate yfinance for comparison
    if YFINANCE_AVAILABLE:
        try:
            print(f"Testing yfinance for {symbol}...")
            yf_ticker = yf.Ticker(symbol)
            hist = yf_ticker.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                results["yfinance"]["status"] = "success"
                results["yfinance"]["data"] = float(current_price)
                print(f"yfinance Success: {current_price}")
            else:
                results["yfinance"]["status"] = "no_data"
                print("yfinance Success: No data returned.")
        except Exception as e:
            results["yfinance"]["status"] = "error"
            results["yfinance"]["error"] = str(e)
            print(f"yfinance Error: {e}")
    else:
        results["yfinance"]["status"] = "missing_package"
        print("yfinance Error: yfinance package not found.")

    return results

if __name__ == "__main__":
    test_symbols = [
        "RELIANCE.NS",  # NSE Stock
        "TCS.NS",       # NSE Stock
        "HDFCBANK.BO",  # BSE Stock
        "AAPL",         # US Stock (for baseline check)
    ]

    print("Defeatbeta-API Evaluation Script")
    print(f"Defeatbeta-API Available: {DEFEATBETA_AVAILABLE}")
    print(f"yfinance Available: {YFINANCE_AVAILABLE}")

    if not DEFEATBETA_AVAILABLE:
        print("\nWARNING: defeatbeta-api is not installed.")

    summary_results = []
    for sym in test_symbols:
        summary_results.append(evaluate_ticker(sym))

    print("\n" + "="*50)
    print("SUMMARY REPORT")
    print("="*50)
    for res in summary_results:
        db_status = res["defeatbeta"]["status"]
        yf_status = res["yfinance"]["status"]
        print(f"Ticker: {res['symbol']:<15} | Defeatbeta: {db_status:<15} | yfinance: {yf_status:<15}")

    # Output JSON for easier parsing if needed
    output_file = "evaluation_results.json"
    with open(output_file, "w") as f:
        json.dump(summary_results, f, indent=4)
    print(f"\nDetailed results saved to {output_file}")
