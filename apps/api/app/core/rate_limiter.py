import time
import threading
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
from app.core.config import settings

class InMemoryRateLimiter:
    """
    Thread-safe sliding-window in-memory rate limiter.
    Note: Process-local. For distributed deployments across multiple containers,
    a shared Redis-backed rate limiter is recommended.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._records: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> Optional[int]:
        """
        Checks if key exceeds max_requests within window_seconds.
        Returns retry_after seconds if limited, None if allowed.
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Filter timestamps within window
            valid_timestamps = [ts for ts in self._records[key] if ts > cutoff]
            self._records[key] = valid_timestamps

            if len(valid_timestamps) >= max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(window_seconds - (now - earliest)))
                return retry_after

            self._records[key].append(now)
            return None

    def reset(self):
        with self._lock:
            self._records.clear()

limiter = InMemoryRateLimiter()

def get_client_ip(request: Request) -> str:
    # Use client host or forwarded header
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def rate_limit_login(request: Request):
    ip = get_client_ip(request)
    key = f"login:{ip}"
    retry_after = limiter.is_rate_limited(key, settings.RATE_LIMIT_LOGIN_PER_MINUTE, window_seconds=60)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please wait {retry_after} seconds before retrying.",
            headers={"Retry-After": str(retry_after)}
        )

def rate_limit_register(request: Request):
    ip = get_client_ip(request)
    key = f"register:{ip}"
    retry_after = limiter.is_rate_limited(key, settings.RATE_LIMIT_REGISTER_PER_MINUTE, window_seconds=60)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many registration attempts. Please wait {retry_after} seconds before retrying.",
            headers={"Retry-After": str(retry_after)}
        )

def rate_limit_upload(request: Request):
    ip = get_client_ip(request)
    key = f"upload:{ip}"
    retry_after = limiter.is_rate_limited(key, settings.RATE_LIMIT_UPLOAD_PER_MINUTE, window_seconds=60)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Upload rate limit reached. Please wait {retry_after} seconds before uploading more files.",
            headers={"Retry-After": str(retry_after)}
        )
