import logging
import time
from typing import Any, Dict, Optional

from app.cache.base import CacheClient

logger = logging.getLogger(__name__)


class RateLimitExceededException(Exception):
    """Raised when an external financial data provider exceeds its configured rate limit."""

    def __init__(self, provider_name: str, limit: int, window_seconds: int, scope: str = "global"):
        self.provider_name = provider_name
        self.limit = limit
        self.window_seconds = window_seconds
        self.scope = scope
        super().__init__(
            f"Rate limit ({scope}) exceeded for provider '{provider_name}': {limit} calls per {window_seconds}s"
        )


# Default provider rate limit definitions: (max_global_calls, window_seconds, max_user_calls)
DEFAULT_PROVIDER_LIMITS: Dict[str, tuple[int, int, int]] = {
    "zerodha": (10, 1, 3),        # Global: 10/s, Per-User: 3/s
    "icici_breeze": (500, 60, 100), # Global: 500/min, Per-User: 100/min
    "upstox": (50, 1, 10),        # Global: 50/s, Per-User: 10/s
    "yfinance": (10, 1, 2),        # Global: 10/s, Per-User: 2/s
    "amfi": (20, 1, 5),           # Global: 20/s, Per-User: 5/s
    "nse": (10, 1, 2),            # Global: 10/s, Per-User: 2/s
}


class ProviderRateLimiter:
    """
    Sliding-window rate limiter supporting both shared global provider rate limits
    and individual per-user rate limit quotas.
    """

    def __init__(self, cache_client: Optional[CacheClient]):
        self.cache = cache_client
        self._local_global_counts: Dict[str, tuple[int, float]] = {}
        self._local_user_counts: Dict[str, tuple[int, float]] = {}

    def check_and_increment(
        self,
        provider_name: str,
        user_id: Optional[str] = None,
        custom_limit: Optional[int] = None,
        custom_window: Optional[int] = None,
        custom_user_limit: Optional[int] = None,
    ) -> bool:
        """
        Checks if a call to provider_name is within both shared global and user-specific limits.
        If limit is not exceeded, increments call counters and returns True.
        If any limit is exceeded, raises RateLimitExceededException.
        """
        provider_key = provider_name.lower()
        global_limit, window_seconds, user_limit = DEFAULT_PROVIDER_LIMITS.get(
            provider_key, (10, 1, 3)
        )

        if custom_limit is not None:
            global_limit = custom_limit
        if custom_window is not None:
            window_seconds = custom_window
        if custom_user_limit is not None:
            user_limit = custom_user_limit

        now = time.time()
        window_bucket = int(now // window_seconds)

        # 1. Per-User Limit Check (if user_id provided)
        if user_id:
            user_cache_key = f"ratelimit:user:{user_id}:{provider_key}:{window_seconds}s:{window_bucket}"
            if self.cache:
                try:
                    u_count = self.cache.incr(user_cache_key, expire=window_seconds * 2)
                    if u_count > user_limit:
                        logger.warning(
                            f"Per-user rate limit exceeded for user '{user_id}' on provider '{provider_name}': {u_count}/{user_limit}"
                        )
                        raise RateLimitExceededException(provider_name, user_limit, window_seconds, scope="per-user")
                except RateLimitExceededException:
                    raise
                except Exception as e:
                    logger.error(f"Error accessing user rate limit cache: {e}")
            else:
                user_local_key = f"{user_id}:{provider_key}"
                prev_u_count, prev_u_time = self._local_user_counts.get(user_local_key, (0, now))
                if now - prev_u_time >= window_seconds:
                    self._local_user_counts[user_local_key] = (1, now)
                elif prev_u_count >= user_limit:
                    raise RateLimitExceededException(provider_name, user_limit, window_seconds, scope="per-user")
                else:
                    self._local_user_counts[user_local_key] = (prev_u_count + 1, prev_u_time)

        # 2. Shared Global Limit Check
        global_cache_key = f"ratelimit:global:{provider_key}:{window_seconds}s:{window_bucket}"
        if self.cache:
            try:
                g_count = self.cache.incr(global_cache_key, expire=window_seconds * 2)
                if g_count > global_limit:
                    logger.warning(
                        f"Global shared rate limit exceeded for provider '{provider_name}': {g_count}/{global_limit}"
                    )
                    raise RateLimitExceededException(provider_name, global_limit, window_seconds, scope="global")
                return True
            except RateLimitExceededException:
                raise
            except Exception as e:
                logger.error(f"Error accessing global rate limit cache: {e}")

        # Local fallback for global limit
        prev_g_count, prev_g_time = self._local_global_counts.get(provider_key, (0, now))
        if now - prev_g_time >= window_seconds:
            self._local_global_counts[provider_key] = (1, now)
            return True
        elif prev_g_count >= global_limit:
            raise RateLimitExceededException(provider_name, global_limit, window_seconds, scope="global")
        else:
            self._local_global_counts[provider_key] = (prev_g_count + 1, prev_g_time)
            return True

    def get_provider_usage(self, provider_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns current global and optional per-user call usage metrics.
        """
        provider_key = provider_name.lower()
        global_limit, window_seconds, user_limit = DEFAULT_PROVIDER_LIMITS.get(
            provider_key, (10, 1, 3)
        )
        now = time.time()
        window_bucket = int(now // window_seconds)

        global_cache_key = f"ratelimit:global:{provider_key}:{window_seconds}s:{window_bucket}"
        global_count = 0
        if self.cache:
            val = self.cache.get(global_cache_key)
            if val is not None:
                try:
                    global_count = int(val)
                except ValueError:
                    global_count = 0
        else:
            global_count, _ = self._local_global_counts.get(provider_key, (0, now))

        user_count = None
        if user_id:
            user_cache_key = f"ratelimit:user:{user_id}:{provider_key}:{window_seconds}s:{window_bucket}"
            if self.cache:
                val_u = self.cache.get(user_cache_key)
                if val_u is not None:
                    try:
                        user_count = int(val_u)
                    except ValueError:
                        user_count = 0
            else:
                user_local_key = f"{user_id}:{provider_key}"
                u_cnt, _ = self._local_user_counts.get(user_local_key, (0, now))
                user_count = u_cnt

        res = {
            "provider": provider_name,
            "current_calls": global_count,
            "max_limit": global_limit,
            "window_seconds": window_seconds,
            "user_limit": user_limit,
        }
        if user_count is not None:
            res["user_current_calls"] = user_count

        return res
