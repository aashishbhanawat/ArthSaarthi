
from datetime import date, timedelta
from typing import Optional

import yfinance as yf
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.cache.base import CacheClient
from app.cache.factory import get_cache_client

router = APIRouter()


@router.get("")
async def get_fx_rate(
    to: str,
    date: date,
    source: str = "USD",
    cache: Optional[CacheClient] = Depends(get_cache_client),
):

    cache_key = f"fx-rate-{source}-{to}-{date}"
    if cache:
        cached_rate = cache.get(cache_key)
        if cached_rate:
            return JSONResponse(content={"rate": cached_rate})

    ticker_str = f"{to}=X"
    if source != "USD":
        ticker_str = f"{source}{to}=X"

    ticker = yf.Ticker(ticker_str)
    start_date = date - timedelta(days=1)
    end_date = date + timedelta(days=1)

    hist = ticker.history(start=start_date, end=end_date)

    if not hist.empty:
        rate = hist["Close"].iloc[0]
        if cache:
            cache.set(cache_key, rate, timeout=60 * 60 * 24)  # Cache for 24 hours
        return JSONResponse(content={"rate": rate})
    else:
        return JSONResponse(content={"error": "Rate not found"}, status_code=404)
