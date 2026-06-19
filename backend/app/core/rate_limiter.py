"""In-memory sliding window rate limiter.

Tracks request counts per key (e.g. IP+email) with a sliding window.
Suitable for single-instance deployments. Replace with Redis for multi-instance.
"""

import time
from collections import defaultdict
from fastapi import HTTPException, Request

_LOGIN_WINDOW_SECONDS = 60
_LOGIN_MAX_ATTEMPTS = 5


class RateLimiter:
    """Sliding window rate limiter using in-memory storage.

    Thread-safe for single-process ASGI (dict operations are atomic in CPython).
    """

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_attempts: int = 5, window_seconds: int = 60) -> bool:
        """Check if a key has exceeded the rate limit.

        Args:
            key: Unique identifier for the rate limit bucket (e.g. "ip:email").
            max_attempts: Maximum allowed attempts in the window.
            window_seconds: Time window in seconds.

        Returns:
            True if the request is allowed, False if rate limited.
        """
        now = time.time()
        window_start = now - window_seconds

        # Prune old entries
        self._buckets[key] = [t for t in self._buckets[key] if t > window_start]

        if len(self._buckets[key]) >= max_attempts:
            return False

        self._buckets[key].append(now)
        return True

    def get_retry_after(self, key: str, window_seconds: int = 60) -> int:
        """Get seconds until the rate limit resets for a key."""
        if not self._buckets.get(key):
            return 0
        oldest = min(self._buckets[key])
        retry_after = int(window_seconds - (time.time() - oldest))
        return max(retry_after, 0)


# Singleton instance
_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Return the singleton RateLimiter instance."""
    return _limiter


async def rate_limit_login(request: Request) -> None:
    """FastAPI dependency: rate limit login by IP.

    Uses client IP only (body-based key would conflict with endpoint body parsing).
    Email-level granularity can be added in the service layer.

    Raises:
        HTTPException 429 if rate limit exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"

    limiter = get_rate_limiter()
    if not limiter.check(client_ip, max_attempts=10, window_seconds=_LOGIN_WINDOW_SECONDS):
        retry_after = limiter.get_retry_after(client_ip, window_seconds=_LOGIN_WINDOW_SECONDS)
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(retry_after)},
        )
