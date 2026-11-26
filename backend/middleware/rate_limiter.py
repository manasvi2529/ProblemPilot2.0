"""
Problem2Project AI — Security Middleware: Rate Limiting & Request Size Governance.
Protects backend APIs from brute-force authentication, scraping, and DOS payload exhaustion.
"""
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Max body payload limit: 10 Megabytes
MAX_BODY_SIZE_BYTES = 10 * 1024 * 1024


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter keyed by IP and user token.
    Enforces distinct thresholds for auth endpoints, compute endpoints, and standard API routes.
    """

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        # ip/user_key -> list of timestamp floats
        self._history: Dict[str, List[float]] = defaultdict(list)
        # Periodic cleanup of old timestamps
        self._last_clean = time.time()

    def _clean_old_history(self, now: float):
        """Purge entries older than 2 minutes to keep memory bounded."""
        if now - self._last_clean < 60.0:
            return
        cutoff = now - 120.0
        keys_to_del = []
        for key, timestamps in list(self._history.items()):
            valid = [ts for ts in timestamps if ts > cutoff]
            if valid:
                self._history[key] = valid
            else:
                keys_to_del.append(key)
        for k in keys_to_del:
            self._history.pop(k, None)
        self._last_clean = now

    def _get_rate_limit_rule(self, path: str, method: str) -> Tuple[int, int]:
        """
        Return (max_requests, window_seconds) based on target endpoint sensitivity.
        - Auth login/register: 15 req / 60s (strict brute-force defense)
        - Heavy compute (research session / build / AI): 40 req / 60s
        - Default API: 150 req / 60s
        """
        if path.startswith("/api/auth/login") or path.startswith("/api/auth/register"):
            return 15, 60
        elif "/research/sessions" in path or "/build" in path or "/diagnose" in path:
            return 40, 60
        return 150, 60

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        # 1. Enforce payload size limit
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > MAX_BODY_SIZE_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request body size exceeds maximum limit of {MAX_BODY_SIZE_BYTES // (1024*1024)}MB.",
                            "error": "payload_too_large",
                            "message": f"Request body size exceeds maximum limit of {MAX_BODY_SIZE_BYTES // (1024*1024)}MB.",
                        },
                    )
            except ValueError:
                pass

        path = request.url.path
        # Exclude static assets and health probes from rate limits
        if (
            path.startswith("/assets")
            or path.startswith("/css")
            or path.startswith("/js")
            or path in ("/api/health", "/api/v1/health")
        ):
            return await call_next(request)

        # 2. Derive rate limiting bucket key
        auth_header = request.headers.get("Authorization", "")
        client_ip = request.client.host if request.client else "127.0.0.1"

        bucket_key = f"{client_ip}:{path.split('/')[2] if len(path.split('/')) > 2 else 'root'}"
        if auth_header.startswith("Bearer "):
            # Key by token substring for authenticated requests
            token_snippet = auth_header.split(" ", 1)[1][:16]
            bucket_key = f"usr:{token_snippet}:{path.split('/')[2] if len(path.split('/')) > 2 else 'root'}"

        now = time.time()
        self._clean_old_history(now)

        max_requests, window_seconds = self._get_rate_limit_rule(path, request.method)
        window_start = now - window_seconds

        timestamps = [ts for ts in self._history[bucket_key] if ts > window_start]
        self._history[bucket_key] = timestamps

        if len(timestamps) >= max_requests:
            oldest_in_window = timestamps[0]
            retry_after = max(1, int(window_seconds - (now - oldest_in_window)))
            logger.warning(f"Rate limit exceeded for key {bucket_key} on {path} ({len(timestamps)}/{max_requests})")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "limit": max_requests,
                    "window_seconds": window_seconds,
                    "retry_after": retry_after,
                    "message": f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s allowed. Try again in {retry_after}s.",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self._history[bucket_key].append(now)
        remaining = max_requests - len(self._history[bucket_key])

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response
