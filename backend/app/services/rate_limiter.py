import time
import logging
from collections import defaultdict

import redis
from app.core.config import settings

logger = logging.getLogger("careerpilot.ratelimit")

_redis_client: "redis.Redis | None" = None
_redis_available = True

# In-memory fallback store, used only if Redis is unreachable.
_memory_log: dict[str, list[float]] = defaultdict(list)


def _get_redis() -> "redis.Redis | None":
    global _redis_client, _redis_available
    if not _redis_available:
        return None
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
            _redis_client.ping()
        except Exception:
            logger.warning("Redis unavailable, falling back to in-memory rate limiting")
            _redis_available = False
            return None
    return _redis_client


def is_rate_limited(key: str, limit: int, window_seconds: int = 60) -> bool:
    """Sliding-window rate limit check. Tries Redis first (works correctly
    across multiple API instances); falls back to a per-process in-memory
    window if Redis can't be reached, so the app still works locally
    without Redis running."""
    client = _get_redis()

    if client is not None:
        try:
            now = time.time()
            redis_key = f"ratelimit:{key}"
            pipe = client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, now - window_seconds)
            pipe.zadd(redis_key, {str(now): now})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, window_seconds)
            _, _, count, _ = pipe.execute()
            return count > limit
        except Exception:
            logger.warning("Redis rate-limit check failed, falling back to in-memory")

    # In-memory fallback
    now = time.time()
    log = _memory_log[key]
    _memory_log[key] = [t for t in log if now - t < window_seconds]
    _memory_log[key].append(now)
    return len(_memory_log[key]) > limit
