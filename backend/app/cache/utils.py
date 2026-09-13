import functools
import inspect
import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Type

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud
from app.cache.factory import get_cache_client
from app.utils.pydantic_compat import model_validate_json

logger = logging.getLogger(__name__)


def cache_analytics_data(
    prefix: str,
    arg_names: List[str],
    ttl: int = 900,
    response_model: Optional[Type[BaseModel]] = None,
):
    """    A flexible decorator to cache the results of analytics functions.

    It generates a cache key from a prefix and the values of specified arguments.
    The result is stored as JSON with a given TTL.

    :param prefix: The static part of the cache key (e.g., 'analytics:portfolio').
    :param arg_names: A list of argument names from the decorated function
                      to use in the cache key.
    :param ttl: The time-to-live for the cache entry in seconds.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache_client()
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            key_parts = [prefix]
            try:
                for name in arg_names:
                    key_parts.append(str(bound_args.arguments[name]))
            except KeyError as e:
                logger.error(
                    f"Argument '{e.args[0]}' not found for caching in function "
                    f"'{func.__name__}'. Caching skipped."
                )
                return func(*args, **kwargs)

            cache_key = ":".join(key_parts)

            # 1. Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                if response_model:
                    return model_validate_json(response_model, cached_result)
                return json.loads(cached_result)

            logger.debug(f"Cache MISS for key: {cache_key}")

            # 2. If miss, execute the function
            result = func(*args, **kwargs)

            # 3. Set the result in the cache
            # Use jsonable_encoder to handle complex types like Pydantic models
            json_result = json.dumps(jsonable_encoder(result))
            cache.set(key=cache_key, value=json_result, expire=ttl)

            return result

        return wrapper

    return decorator


def invalidate_caches_for_portfolio(db: Session, portfolio_id: uuid.UUID):
    """
    Invalidates all cache entries associated with a specific portfolio.

    This function should be called after any data modification (C/U/D)
    that affects a portfolio's analytics.
    """
    cache = get_cache_client()
    portfolio = crud.portfolio.get(db, id=portfolio_id)

    if not portfolio:
        logger.warning(
            "Attempted to invalidate cache for non-existent portfolio_id: %s",
            portfolio_id,
        )
        return

    user_id = portfolio.user_id

    # Invalidate dashboard summary and all range-specific history keys for the user
    # The history cache key format is: analytics:dashboard_history:{user_id}:{range_str}
    keys_to_delete = [f"analytics:dashboard_summary:{user_id}"]
    for range_str in ["7d", "30d", "1y", "all"]:
        keys_to_delete.append(f"analytics:dashboard_history:{user_id}:{range_str}")

    # Delete all DB snapshots for this portfolio to force live recalculation
    try:
        from sqlalchemy import delete

        from app.models.portfolio_snapshot import DailyPortfolioSnapshot
        stmt = delete(DailyPortfolioSnapshot).where(
            DailyPortfolioSnapshot.portfolio_id == portfolio_id
        )
        db.execute(stmt)
        db.commit()
        logger.info(
            f"Deleted all stale DailyPortfolioSnapshots for portfolio {portfolio_id}"
        )
    except Exception as e:
        logger.error(
            f"Failed to delete stale snapshots for portfolio {portfolio_id}: {e}"
        )

    # Invalidate portfolio-level analytics and holdings summary
    keys_to_delete.extend(
        [
            f"analytics:portfolio_holdings_and_summary:{portfolio_id}",
            f"analytics:portfolio_analytics:{portfolio_id}",
            f"analytics:all_portfolios_holdings_and_summary:{user_id}",
        ]
    )

    # Invalidate all asset-level analytics for this portfolio
    portfolio_assets = crud.asset.get_multi_by_portfolio(db, portfolio_id=portfolio_id)
    for asset in portfolio_assets:
        keys_to_delete.append(f"analytics:asset_analytics:{asset.id}")

    if cache:
        cache.delete_multi(keys_to_delete)
        logger.info(
            "Invalidated %d cache entries for portfolio %s",
            len(keys_to_delete),
            portfolio_id,
        )


def get_market_aware_ttl(asset_type: str, now_dt: Optional[Any] = None) -> int:
    """
    Returns an optimal Cache TTL based on asset type and market session hours.
    - Active Market Hours (Mon-Fri 09:15 - 15:30 IST): 15 mins (900s)
    - Off-Market Hours / Weekends: 12 hours (43,200s)
    - Mutual Funds: 24 hours (86,400s)
    - FX Rates: 6 hours (21,600s)
    """
    import datetime
    from datetime import timezone

    asset_upper = (asset_type or "").upper().replace("_", " ")

    if asset_upper == "MUTUAL FUND":
        return 86400  # 24 hours

    if asset_upper in ("FX", "FOREX", "CURRENCY"):
        return 21600  # 6 hours

    # Determine IST time (UTC+5:30)
    if now_dt is None:
        now_utc = datetime.datetime.now(timezone.utc)
    elif now_dt.tzinfo is None:
        now_utc = now_dt.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_dt

    ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now_ist = now_utc.astimezone(ist_offset)

    # Weekday check (0 = Mon, 4 = Fri)
    is_weekday = now_ist.weekday() < 5
    market_open = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)

    if is_weekday and market_open <= now_ist <= market_close:
        return 900  # 15 minutes during trading hours
    else:
        return 43200  # 12 hours outside trading hours


# Global in-memory cache hit/miss stats tracking
_CACHE_STATS = {"hits": 0, "misses": 0}


def record_cache_access(hit: bool) -> None:
    """Records a cache hit or miss for diagnostic metrics."""
    if hit:
        _CACHE_STATS["hits"] += 1
    else:
        _CACHE_STATS["misses"] += 1


def get_cache_performance_stats() -> Dict[str, Any]:
    """Returns aggregated cache hit/miss ratios and count metrics."""
    hits = _CACHE_STATS["hits"]
    misses = _CACHE_STATS["misses"]
    total = hits + misses
    hit_ratio = round((hits / total) * 100, 2) if total > 0 else 0.0

    return {
        "hits": hits,
        "misses": misses,
        "total_requests": total,
        "hit_ratio_percent": hit_ratio,
    }

