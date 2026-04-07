import logging

from alembic.config import Config
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from alembic import command
from app.core import config
from app.core import dependencies as deps
from app.db.base import Base  # Import Base with all models registered
from app.db.session import engine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reset-db", status_code=status.HTTP_204_NO_CONTENT)
def reset_db(
    db: Session = Depends(deps.get_db),
) -> Response:
    """
    Resets the database to a clean state for E2E testing.

    This endpoint is database-aware. For SQLite, it drops and recreates all tables
    directly from the models to avoid Alembic's limited support for ALTER TABLE.
    For PostgreSQL, it uses the standard Alembic downgrade/upgrade cycle.

    This endpoint is only available in a test environment and will raise a
    403 Forbidden error otherwise.
    """
    if config.settings.ENVIRONMENT != "test":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in the test environment.",
        )

    logger.info(f"E2E: Resetting database (Type: {config.settings.DATABASE_TYPE})...")

    if config.settings.DATABASE_TYPE == "sqlite":
        # For SQLite, Alembic downgrades can fail due to limited ALTER TABLE support.
        # A robust reset is to drop and recreate all tables from the current models.
        logger.info("E2E: Using drop/create all for SQLite.")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        # After recreating, we need to stamp it again so the next test run doesn't fail.
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        logger.info("E2E: SQLite database reset and stamped successfully.")
    else:
        # For PostgreSQL, using Alembic is the correct way to ensure a clean schema.
        logger.info("E2E: Using alembic downgrade/upgrade for PostgreSQL.")
        try:
            alembic_cfg = Config("alembic.ini")
            command.downgrade(alembic_cfg, "base")
            command.upgrade(alembic_cfg, "head")
            logger.info("E2E: Database reset via Alembic successful.")
        except Exception as e:
            logger.error(f"E2E: Alembic command failed: {e}", exc_info=True)
            # Re-raise as an HTTPException to provide feedback to the test runner
            raise HTTPException(status_code=500, detail="Alembic command failed.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/yahoo-test")
def trigger_yahoo_header_test(
    db: Session = Depends(deps.get_db),
):
    logger.info("Function trigger_yahoo_header_test() called.")
    """
    Triggers a background test that rotates through various header configurations
    and tickers to identify what works on Android to bypass 429 rate limits.
    """
    import threading
    import time
    import random
    import requests
    from yahooquery import Ticker
    import yfinance as yf
    import yahooquery.utils as yq_utils

    tickers_to_test = [
        "NTPC.NS", "NTPC.BO", "GAIL.NS", "GAIL.BO", 
        "COALINDIA.NS", "COALINDIA.BO", "HAPPSTMNDS.NS", "COFORGE.NS"
    ]

    header_sets = [
        {
            "name": "Android Chrome (Current)",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://finance.yahoo.com/",
                "Sec-Ch-Ua": '"Chromium";v="123", "Not:A-Brand";v="8", "Google Chrome";v="123"',
                "Sec-Ch-Ua-Mobile": "?1",
                "Sec-Ch-Ua-Platform": '"Android"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Upgrade-Insecure-Requests": "1",
                "Priority": "u=0, i",
            }
        },
        {
            "name": "Desktop Chrome Windows",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
            }
        },
        {
            "name": "iPhone Safari",
            "headers": {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            }
        },
        {
            "name": "Minimal Requests",
            "headers": {
                "User-Agent": "python-requests/2.31.0",
                "Accept": "*/*",
            }
        }
    ]

    def test_loop():
        logger.info("### STARTING YAHOO HEADER TEST LOOP ###")
        
        # DNS Bypass: If query2 fails to resolve, we use a known Yahoo Edge IP.
        # This is a common issue on some Android/Chaquopy environments.
        YAHOO_IPS = ["27.123.42.204", "27.123.43.205", "69.147.88.7", "69.147.88.8"]
        
        from requests.adapters import HTTPAdapter
        from urllib3.poolmanager import PoolManager
        
        class DNSResolverAdapter(HTTPAdapter):
            def __init__(self, *args, **kwargs):
                self.host_to_ip = {
                    "query1.finance.yahoo.com": YAHOO_IPS[0],
                    "query2.finance.yahoo.com": YAHOO_IPS[1],
                    "finance.yahoo.com": YAHOO_IPS[2]
                }
                super().__init__(*args, **kwargs)

            def resolve(self, url):
                import urllib.parse
                parsed = urllib.parse.urlparse(url)
                if parsed.hostname in self.host_to_ip:
                    # In a real environment we'd swap the hostname in the URL and set the Host header.
                    # For simplicity, we'll rely on system DNS first, then fallback if it fails.
                    pass
                return url

        for h_set in header_sets:
            logger.info(f"--- Testing Header Set: {h_set['name']} ---")
            
            # Create session for this set
            session = requests.Session()
            session.headers.update(h_set['headers'])
            
            # PRIME THE SESSION: Visit finance.yahoo.com to get cookies
            try:
                logger.info(f"Priming session for {h_set['name']}...")
                resp = session.get("https://finance.yahoo.com", timeout=10)
                logger.info(f"Priming status: {resp.status_code}. Cookies: {session.cookies.get_dict()}")
            except Exception as e:
                logger.warning(f"Priming failed for {h_set['name']}: {e}")

            # Explicitly force query1 for this test (often less throttled)
            yq_utils.BASE_URL = "https://query1.finance.yahoo.com"
            
            for ticker_symbol in tickers_to_test:
                # Random jitter to avoid burst detection
                time.sleep(random.uniform(2.0, 5.0))
                
                try:
                    logger.info(f"Testing {ticker_symbol} with {h_set['name']} (YahooQuery on Query1)...")
                    t = Ticker(ticker_symbol, session=session)
                    price = t.price
                    
                    if isinstance(price, dict) and ticker_symbol in price:
                        details = price[ticker_symbol]
                        market_price = details.get('regularMarketPrice') or details.get('currentPrice')
                        if market_price:
                            logger.info(f"SUCCESS: {ticker_symbol} = {market_price} (YahooQuery)")
                        else:
                            logger.warning(f"FAILURE: {ticker_symbol} no price field. Result: {details}")
                    else:
                        # Log more details on failure
                        logger.warning(f"FAILURE: {ticker_symbol} returned no price. Full body: {price}")
                        
                        # Fallback: Try a direct requests.get to the quote endpoint
                        raw_url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker_symbol}"
                        raw_resp = session.get(raw_url, timeout=10)
                        logger.info(f"DIRECT GET {ticker_symbol} Status: {raw_resp.status_code}")
                        if raw_resp.status_code == 200:
                            logger.info(f"DIRECT GET SUCCESS: {raw_resp.text[:200]}...")
                        else:
                            logger.warning(f"DIRECT GET FAILED: {raw_resp.status_code} - {raw_resp.text[:100]}")

                except Exception as e:
                    logger.error(f"ERROR: {ticker_symbol} failed with {h_set['name']}: {e}")

                # Also test yfinance (which hits query2 by default)
                try:
                    logger.info(f"Testing {ticker_symbol} with {h_set['name']} (yfinance on Query2)...")
                    ticker_yf = yf.Ticker(ticker_symbol, session=session)
                    info = ticker_yf.fast_info
                    
                    # Log common price keys to see exactly what we're getting
                    market_price = info.get('lastPrice') or info.get('last_price') or info.get('regularMarketPrice')
                    
                    if market_price:
                        logger.info(f"SUCCESS: {ticker_symbol} = {market_price} (yfinance)")
                    else:
                        logger.warning(f"FAILURE: {ticker_symbol} yfinance no price found. Available info: {list(info.keys())}")
                except Exception as e:
                    logger.warning(f"yfinance failed for {ticker_symbol}: {e}")
                    
            logger.info(f"--- Finished Header Set: {h_set['name']} ---")
        logger.info("### YAHOO HEADER TEST LOOP COMPLETE ###")

    threading.Thread(target=test_loop, daemon=True).start()
    return {"msg": "Yahoo header test started in background. Check logs."}
