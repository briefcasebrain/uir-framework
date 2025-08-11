"""Rate limiter implementation"""

import asyncio
import time
from typing import Dict, Optional
from collections import deque
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate_limits: Dict[str, int]):
        """
        Initialize rate limiter
        
        Args:
            rate_limits: Dict of operation -> requests per second
        """
        self.rate_limits = rate_limits
        self.buckets: Dict[str, TokenBucket] = {}
        
        for operation, limit in rate_limits.items():
            self.buckets[operation] = TokenBucket(
                capacity=limit,
                refill_rate=limit
            )
    
    async def acquire(self, operation: str = "default", tokens: int = 1):
        """Acquire tokens for an operation"""
        bucket = self.buckets.get(operation, self.buckets.get("default"))
        if bucket:
            await bucket.acquire(tokens)
    
    def try_acquire(self, operation: str = "default", tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking"""
        bucket = self.buckets.get(operation, self.buckets.get("default"))
        if bucket:
            return bucket.try_acquire(tokens)
        return True


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: int):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = None
    
    async def acquire(self, tokens: int = 1):
        """Acquire tokens, blocking if necessary"""
        if self._lock is None:
            self._lock = asyncio.Lock()
            
        while True:
            async with self._lock:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
            
            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.refill_rate
            await asyncio.sleep(wait_time)
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking"""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for more precise control"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request"""
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the window
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()
            
            # Check if we can make a request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return
            
            # Calculate wait time
            oldest = self.requests[0]
            wait_time = (oldest + self.window_seconds) - now
            
        await asyncio.sleep(wait_time)
        await self.acquire()  # Retry
    
    def try_acquire(self) -> bool:
        """Try to acquire without blocking"""
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        # Check if we can make a request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False