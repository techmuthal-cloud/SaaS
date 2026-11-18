import time
import uuid
import threading
import ipaddress
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
from app.core.config import settings

class InMemoryRateLimiter:
    """
    Thread-safe sliding-window in-memory rate limiter.
    Used for local development and offline test suites.
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

LUA_SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local cutoff = tonumber(ARGV[2])
local max_requests = tonumber(ARGV[3])
local window = tonumber(ARGV[4])
local member = ARGV[5]

redis.call('ZREMRANGEBYSCORE', key, 0, cutoff)
local count = redis.call('ZCARD', key)
if count >= max_requests then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 1
    if oldest and #oldest > 1 then
        retry_after = math.max(1, math.ceil(window - (now - tonumber(oldest[2]))))
    end
    return retry_after
else
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, window + 5)
    return 0
end
"""

class RedisRateLimiter:
    """
    Production-grade distributed rate limiter using atomic Redis Lua scripts.
    Guarantees no race conditions, prevents timestamp collisions, and enforces fail-closed behavior.
    """
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client = None
        self._script = None
        try:
            import redis
            self._client = redis.Redis.from_url(redis_url, decode_responses=True)
            self._script = self._client.register_script(LUA_SLIDING_WINDOW_SCRIPT)
        except Exception:
            self._client = None

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> Optional[int]:
        if not self._client or not self._script:
            if settings.ENVIRONMENT == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Security Protection Error: Distributed rate limiting cluster is unreachable (failing closed)."
                )
            return None

        now = time.time()
        cutoff = now - window_seconds
        redis_key = f"rate_limit:{key}"
        member = f"{now}:{uuid.uuid4().hex[:8]}"

        try:
            res = self._script(
                keys=[redis_key],
                args=[now, cutoff, max_requests, window_seconds, member]
            )
            retry_after = int(res)
            return retry_after if retry_after > 0 else None
        except Exception:
            if settings.ENVIRONMENT == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Security Protection Error: Rate limiter execution failed (failing closed)."
                )
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
    direct_ip = request.client.host if request.client else "127.0.0.1"
    
    if is_trusted_proxy(direct_ip):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
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
