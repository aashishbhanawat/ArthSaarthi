import sys
import logging
import json
import os

# Attempt to import alternatives
try:
    from yahooquery import Ticker
    YAHOOQUERY_AVAILABLE = True
except ImportError:
    YAHOOQUERY_AVAILABLE = False

try:
    import nsepython
    NSEPYTHON_AVAILABLE = True
except ImportError:
    NSEPYTHON_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def evaluate_yahooquery(symbol):
    print(f"Testing yahooquery for {symbol}...")
    try:
        t = Ticker(symbol)
        # summary_detail contains marketCap, trailingPE, priceToBook, trailingAnnualDividendYield
        # asset_profile contains industry, sector
        data = t.all_modules[symbol]
        
        # Extract specifics
        summary = data.get('summaryDetail', {})
        profile = data.get('assetProfile', {})
        
        result = {
            "industry": profile.get("industry"),
            "marketCap": summary.get("marketCap"),
            "trailingPE": summary.get("trailingPE"),
            "priceToBook": summary.get("priceToBook"),
            "status": "success"
        }
        print(f"  Industry: {result['industry']}")
        print(f"  Market Cap: {result['marketCap']}")
        print(f"  P/E: {result['trailingPE']}")
        print(f"  P/B: {result['priceToBook']}")
        return result
    except Exception as e:
        print(f"  Error: {e}")
        return {"status": "error", "error": str(e)}

def evaluate_nsepython(symbol):
    # nsepython works with NSE symbols (no .NS)
    nse_symbol = symbol.replace('.NS', '')
    print(f"Testing nsepython for {nse_symbol}...")
    try:
        # nse_quote_meta returns basic metadata
        # nse_eq() returns equity info
        meta = nsepython.nse_quote_meta(nse_symbol)
        
        # For full fundamental data, we might need a different function
        # nsepython often scrapes the NSE website directly
        
        result = {
            "industry": meta.get("industry"),
            "status": "success",
            "full_meta": meta # Keep for debugging
        }
        print(f"  Industry: {result['industry']}")
        return result
    except Exception as e:
        print(f"  Error: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    test_symbols = ["RELIANCE.NS", "TCS.NS"]
    
    print("Metadata Alternative Evaluation Script")
    print(f"YahooQuery Available: {YAHOOQUERY_AVAILABLE}")
    print(f"NSEPython Available: {NSEPYTHON_AVAILABLE}")

    summary_results = {}

    for sym in test_symbols:
        summary_results[sym] = {
            "yahooquery": evaluate_yahooquery(sym) if YAHOOQUERY_AVAILABLE else "N/A",
            "nsepython": evaluate_nsepython(sym) if NSEPYTHON_AVAILABLE else "N/A"
        }

    with open("metadata_evaluation_results.json", "w") as f:
        json.dump(summary_results, f, indent=4)
    print(f"\nResults saved to metadata_evaluation_results.json")
