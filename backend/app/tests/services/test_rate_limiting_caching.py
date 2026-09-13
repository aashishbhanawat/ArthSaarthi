import datetime

import pytest

from app.cache.utils import (
    get_cache_performance_stats,
    get_market_aware_ttl,
    record_cache_access,
)
from app.services.rate_limiter import ProviderRateLimiter, RateLimitExceededException
from app.services.request_batcher import BatchQuoteFetcher


def test_market_aware_ttl_mutual_fund():
    assert get_market_aware_ttl("MUTUAL_FUND") == 86400
    assert get_market_aware_ttl("Mutual Fund") == 86400


def test_market_aware_ttl_currency_fx():
    assert get_market_aware_ttl("FX") == 21600
    assert get_market_aware_ttl("Currency") == 21600


def test_market_aware_ttl_stock_trading_hours():
    # Wednesday 11:30 AM IST (UTC: Wed 06:00 AM)
    dt_trading = datetime.datetime(2026, 9, 16, 6, 0, tzinfo=datetime.timezone.utc)
    ttl = get_market_aware_ttl("Stock", now_dt=dt_trading)
    assert ttl == 900  # 15 minutes during active trading


def test_market_aware_ttl_stock_off_hours():
    # Saturday 11:30 AM IST (UTC: Sat 06:00 AM)
    dt_weekend = datetime.datetime(2026, 9, 19, 6, 0, tzinfo=datetime.timezone.utc)
    ttl = get_market_aware_ttl("Stock", now_dt=dt_weekend)
    assert ttl == 43200  # 12 hours outside trading hours


def test_batch_quote_fetcher_partition():
    fetcher = BatchQuoteFetcher(max_batch_size=5)
    items = list(range(12))
    chunks = fetcher.partition(items)

    assert len(chunks) == 3
    assert chunks[0] == [0, 1, 2, 3, 4]
    assert chunks[1] == [5, 6, 7, 8, 9]
    assert chunks[2] == [10, 11]


def test_batch_quote_fetcher_execute():
    fetcher = BatchQuoteFetcher(max_batch_size=2)
    items = [{"ticker": "A"}, {"ticker": "B"}, {"ticker": "C"}]

    def mock_fetch(batch):
        return {item["ticker"]: 100.0 for item in batch}

    results = fetcher.execute_batch_fetch(items, mock_fetch)
    assert len(results) == 3
    assert results["A"] == 100.0
    assert results["B"] == 100.0
    assert results["C"] == 100.0


def test_provider_rate_limiter_global_and_per_user():
    limiter = ProviderRateLimiter(cache_client=None)

    # Zerodha default: Global 10/s, Per-user 3/s
    user_id = "user_123"

    # User 123 makes 3 calls
    assert limiter.check_and_increment("zerodha", user_id=user_id) is True
    assert limiter.check_and_increment("zerodha", user_id=user_id) is True
    assert limiter.check_and_increment("zerodha", user_id=user_id) is True

    # User 123 4th call fails per-user limit
    with pytest.raises(RateLimitExceededException) as exc_info:
        limiter.check_and_increment("zerodha", user_id=user_id)

    assert exc_info.value.scope == "per-user"
    assert "per-user" in str(exc_info.value)

    # User 456 can still make calls under global limit
    user_456 = "user_456"
    assert limiter.check_and_increment("zerodha", user_id=user_456) is True


def test_cache_performance_stats_tracking():
    record_cache_access(hit=True)
    record_cache_access(hit=True)
    record_cache_access(hit=False)

    stats = get_cache_performance_stats()
    assert stats["hits"] >= 2
    assert stats["misses"] >= 1
    assert stats["total_requests"] >= 3
    assert stats["hit_ratio_percent"] > 0
