import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_admin_user
from app.cache.factory import get_cache_client
from app.cache.utils import get_cache_performance_stats
from app.models.user import User
from app.services.rate_limiter import ProviderRateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
def get_cache_diagnostics(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Fetch system cache performance metrics and provider rate limit consumption.
    Requires admin privileges.
    """
    cache_client = get_cache_client()
    rate_limiter = ProviderRateLimiter(cache_client)

    stats = get_cache_performance_stats()

    providers = ["zerodha", "icici_breeze", "upstox", "yfinance", "amfi", "nse"]
    rate_limit_usage = {}
    for provider in providers:
        rate_limit_usage[provider] = rate_limiter.get_provider_usage(provider)

    cache_type = "disabled"
    if cache_client:
        cache_type = cache_client.__class__.__name__

    return {
        "status": "online",
        "cache_type": cache_type,
        "performance": stats,
        "rate_limits": rate_limit_usage,
    }


@router.post("/clear", response_model=Dict[str, Any])
def clear_application_cache(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Flush or clear application cache entries.
    Requires admin privileges.
    """
    cache_client = get_cache_client()
    if not cache_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caching is disabled or not configured",
        )

    try:
        # Invalidate common cache namespaces
        cache_client.delete_multi(["analytics:*", "ratelimit:*", "financial_data:*"])
        logger.info(f"Admin {current_user.email} triggered cache clear")
        return {"message": "Application cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )
