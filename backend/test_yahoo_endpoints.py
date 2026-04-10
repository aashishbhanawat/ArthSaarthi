import requests
from yahooquery import Ticker
import yahooquery.utils as yq_utils
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_yq")

def test_endpoint(base_url, ticker_symbol):
    logger.info(f"Testing {ticker_symbol} with BASE_URL: {base_url}")
    yq_utils.BASE_URL = base_url
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    })
    
    try:
        t = Ticker(ticker_symbol, session=session)
        price = t.price
        if isinstance(price, dict) and ticker_symbol in price:
            logger.info(f"SUCCESS: {ticker_symbol} price data received.")
            # print(price[ticker_symbol])
        else:
            logger.warning(f"FAILURE: Received: {price}")
    except Exception as e:
        logger.error(f"ERROR: {e}")

if __name__ == "__main__":
    ticker = "NTPC.NS"
    test_endpoint("https://query1.finance.yahoo.com", ticker)
    test_endpoint("https://query2.finance.yahoo.com", ticker)
