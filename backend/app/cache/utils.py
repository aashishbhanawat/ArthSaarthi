import functools
import inspect
import json
import logging
import uuid
from typing import Any, Callable, List, Optional, Type

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud
from app.cache.factory import get_cache_client

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
                    return response_model.model_validate_json(cached_result)
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

    # Invalidate dashboard summary for the user
    dashboard_key = f"analytics:dashboard_summary:{user_id}"
    cache.delete(dashboard_key)
    logger.info(f"Invalidated cache for key: {dashboard_key}")

    # Invalidate portfolio-level analytics and holdings summary
    keys_to_delete = [
        f"analytics:portfolio_holdings_and_summary:{portfolio_id}",
        f"analytics:portfolio_analytics:{portfolio_id}",
    ]

    # Invalidate all asset-level analytics for this portfolio
    portfolio_assets = crud.asset.get_multi_by_portfolio(db, portfolio_id=portfolio_id)
    for asset in portfolio_assets:
        keys_to_delete.append(f"analytics:asset_analytics:{asset.id}")

    for key in keys_to_delete:
        cache.delete(key)
        logger.info(f"Invalidated cache for key: {key}")
