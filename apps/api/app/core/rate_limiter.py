import time
import threading
import ipaddress
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
from app.core.config import settings

class InMemoryRateLimiter:
    """
    Thread-safe sliding-window in-memory rate limiter.
    Used for local development and test suites.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._records: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> Optional[int]:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
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

class RedisRateLimiter:
    """
    Distributed sliding-window rate limiter using Redis sorted sets.
    """
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client = None
        try:
            import redis
            self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        except Exception:
            self._client = None

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> Optional[int]:
        if not self._client:
            return None
        now = time.time()
        cutoff = now - window_seconds
        redis_key = f"rate_limit:{key}"

        try:
            pipe = self._client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, cutoff)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, window_seconds + 5)
            results = pipe.execute()

            request_count = results[1]
            if request_count >= max_requests:
                # Exceeded
                return max(1, int(window_seconds))
            return None
        except Exception:
            return None

    def reset(self):
        if self._client:
            try:
                keys = self._client.keys("rate_limit:*")
                if keys:
                    self._client.delete(*keys)
            except Exception:
                pass

def get_limiter():
    if settings.REDIS_URL:
        try:
            rl = RedisRateLimiter(settings.REDIS_URL)
            if rl._client:
                return rl
        except Exception:
            pass
    return InMemoryRateLimiter()

limiter = get_limiter()

def is_trusted_proxy(ip_str: str) -> bool:
    """
    Verifies if client IP address belongs to configured trusted proxy networks.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        for net_str in settings.TRUSTED_PROXIES:
            if "/" in net_str:
                if ip in ipaddress.ip_network(net_str, strict=False):
                    return True
            else:
                if ip == ipaddress.ip_address(net_str):
                    return True
    except ValueError:
        pass
    return False

def get_client_ip(request: Request) -> str:
    """
    Extracts client IP address safely:
    Only trusts X-Forwarded-For if request comes directly from a verified TRUSTED_PROXY.
    Otherwise strictly returns request.client.host.
    """
    direct_ip = request.client.host if request.client else "127.0.0.1"
    
    if is_trusted_proxy(direct_ip):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # First IP in X-Forwarded-For is original client
            candidate = forwarded.split(",")[0].strip()
            return candidate
            
    return direct_ip

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
