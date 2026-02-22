import time
import hashlib
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


TIER_LIMITS = {
    "free": {"per_day": 100, "per_min": 10},
    "pro": {"per_day": 10_000, "per_min": 100},
    "enterprise": {"per_day": 0, "per_min": 1000},  # 0 = unlimited daily
}

# In-memory sliding window: {key: [(timestamp, ...),]}
_day_windows = defaultdict(list)
_min_windows = defaultdict(list)


def _cleanup(window: list, cutoff: float):
    while window and window[0] < cutoff:
        window.pop(0)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Only rate-limit /api/v1/data/ endpoints authenticated via API key
        if not request.url.path.startswith("/api/v1/data/"):
            return await call_next(request)

        api_key = request.headers.get("x-api-key", "")
        if not api_key:
            return await call_next(request)

        # Tier is set by the get_api_key dependency before reaching here,
        # but middleware runs first. We do a lightweight hash-based check.
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        tier = request.state.__dict__.get("api_tier", "free") if hasattr(request, "state") else "free"

        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        now = time.time()

        # Per-minute check
        min_key = f"{key_hash}:min"
        _cleanup(_min_windows[min_key], now - 60)
        if len(_min_windows[min_key]) >= limits["per_min"]:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Upgrade your plan for higher limits."},
                headers={"Retry-After": "60"},
            )

        # Per-day check
        if limits["per_day"] > 0:
            day_key = f"{key_hash}:day"
            _cleanup(_day_windows[day_key], now - 86400)
            if len(_day_windows[day_key]) >= limits["per_day"]:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Daily rate limit exceeded. Upgrade your plan for higher limits."},
                    headers={"Retry-After": "3600"},
                )
            _day_windows[day_key].append(now)

        _min_windows[min_key].append(now)

        response = await call_next(request)
        return response
