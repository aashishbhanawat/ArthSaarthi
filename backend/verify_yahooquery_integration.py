import sys
import os
from datetime import date
from decimal import Decimal
import logging

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.getcwd(), "app"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_integration():
    try:
        from app.services.financial_data_service import FinancialDataService
        from app.cache.factory import get_cache_client
        
        # Initialize service with cache (if available)
        service = FinancialDataService(cache_client=None)
        
        print("\n" + "="*30)
        print("TESTING INTEGRATION")
        print("="*30)

        # 1. Test get_asset_details (should now prefer YahooQuery)
        print("\n1. Testing get_asset_details for RELIANCE.NS...")
        details = service.get_asset_details("RELIANCE.NS")
        if details:
            print(f"SUCCESS: Found details - {details.get('name')} ({details.get('exchange')})")
        else:
            print("FAILED: No details found for RELIANCE.NS")

        # 2. Test get_enrichment_data (should now use YahooQuery)
        print("\n2. Testing get_enrichment_data for TCS.NS...")
        enrichment = service.get_enrichment_data("TCS.NS")
        if enrichment:
            print(f"SUCCESS: Found enrichment - Sector: {enrichment.get('sector')}, PE: {enrichment.get('trailing_pe')}")
        else:
            print("FAILED: No enrichment found for TCS.NS")

        # 3. Test fallback to yfinance for US stocks
        print("\n3. Testing fallback for AAPL...")
        aapl_details = service.get_asset_details("AAPL")
        if aapl_details:
             print(f"SUCCESS: Found details for AAPL - {aapl_details.get('name')}")
        else:
            print("FAILED: No details found for AAPL")

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        print("Make sure run_command is executed inside the backend container or with correct path.")
    except Exception as e:
        print(f"ERROR during integration test: {e}")

if __name__ == "__main__":
    # Check if packages are installed
    try:
        import yahooquery
        import yfinance
    except ImportError:
        print("Packages missing. Please run within a container that has yahooquery and yfinance installed.")
        # We'll try to run anyway to see the import error
        
    test_integration()
