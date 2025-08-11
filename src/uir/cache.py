"""Caching layer for UIR framework"""

import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
try:
    import redis.asyncio as redis
except ImportError:
    redis = None
    
from .mocks.external_apis import MockRedisAPI
import structlog

from .models import SearchRequest, SearchResponse, VectorSearchRequest

logger = structlog.get_logger()


class CacheManager:
    """Manages caching for search results"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
        max_cache_size: int = 10000
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Any] = {}
        self.logger = logger.bind(component="cache")
    
    async def initialize(self):
        """Initialize cache connections"""
        try:
            if redis:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
                self.logger.info("Redis cache initialized")
            else:
                # Use mock Redis if redis module not available
                self.redis_client = MockRedisAPI()
                await self.redis_client.ping()
                self.logger.info("Mock Redis cache initialized")
        except Exception as e:
            self.logger.warning(f"Redis connection failed, using mock Redis: {e}")
            self.redis_client = MockRedisAPI()
    
    async def get(
        self,
        request: Union[SearchRequest, VectorSearchRequest]
    ) -> Optional[SearchResponse]:
        """Get cached response for request"""
        cache_key = self._generate_cache_key(request)
        
        # Check if caching is enabled
        if request.options and request.options.cache and not request.options.cache.enabled:
            return None
        
        # Try Redis first
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.logger.debug(f"Redis cache hit: {cache_key}")
                    return self._deserialize_response(cached_data)
            except Exception as e:
                self.logger.error(f"Redis get error: {e}")
        
        # Fall back to local cache
        if cache_key in self.local_cache:
            entry = self.local_cache[cache_key]
            if entry["expires_at"] > datetime.now():
                self.logger.debug(f"Local cache hit: {cache_key}")
                return entry["data"]
            else:
                # Remove expired entry
                del self.local_cache[cache_key]
        
        return None
    
    async def set(
        self,
        request: Union[SearchRequest, VectorSearchRequest],
        response: SearchResponse
    ):
        """Cache search response"""
        # Check if caching is enabled
        if request.options and request.options.cache and not request.options.cache.enabled:
            return
        
        cache_key = self._generate_cache_key(request)
        ttl = self.default_ttl
        
        if request.options and request.options.cache and request.options.cache.ttl_seconds:
            ttl = request.options.cache.ttl_seconds
        
        # Serialize response
        serialized = self._serialize_response(response)
        
        # Store in Redis
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key,
                    ttl,
                    serialized
                )
                self.logger.debug(f"Cached in Redis: {cache_key}")
            except Exception as e:
                self.logger.error(f"Redis set error: {e}")
        
        # Store in local cache
        self.local_cache[cache_key] = {
            "data": response,
            "expires_at": datetime.now() + timedelta(seconds=ttl)
        }
        
        # Evict old entries if cache is too large
        if len(self.local_cache) > self.max_cache_size:
            self._evict_local_cache()
    
    async def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries"""
        if pattern:
            # Invalidate by pattern
            if self.redis_client:
                try:
                    keys = await self.redis_client.keys(f"uir:*{pattern}*")
                    if keys:
                        await self.redis_client.delete(*keys)
                except Exception as e:
                    self.logger.error(f"Redis invalidation error: {e}")
            
            # Invalidate local cache
            keys_to_remove = [
                k for k in self.local_cache.keys()
                if pattern in k
            ]
            for key in keys_to_remove:
                del self.local_cache[key]
        else:
            # Clear all cache
            if self.redis_client:
                try:
                    await self.redis_client.flushdb()
                except Exception as e:
                    self.logger.error(f"Redis flush error: {e}")
            
            self.local_cache.clear()
    
    def _generate_cache_key(
        self,
        request: Union[SearchRequest, VectorSearchRequest]
    ) -> str:
        """Generate cache key for request"""
        # Use custom key if provided
        if request.options and request.options.cache and request.options.cache.key:
            return f"uir:custom:{request.options.cache.key}"
        
        # Generate key from request parameters
        key_parts = []
        
        # Add provider(s)
        if isinstance(request.provider, list):
            key_parts.append(",".join(sorted(request.provider)))
        else:
            key_parts.append(request.provider)
        
        # Add query or vector hash
        if isinstance(request, SearchRequest):
            key_parts.append(hashlib.md5(request.query.encode()).hexdigest())
        elif isinstance(request, VectorSearchRequest):
            if request.text:
                key_parts.append(hashlib.md5(request.text.encode()).hexdigest())
            elif request.vector:
                vector_str = ",".join(map(str, request.vector[:10]))  # Use first 10 dims
                key_parts.append(hashlib.md5(vector_str.encode()).hexdigest())
        
        # Add options hash
        if request.options:
            options_str = json.dumps(
                request.options.model_dump(),
                sort_keys=True,
                default=str
            )
            key_parts.append(hashlib.md5(options_str.encode()).hexdigest()[:8])
        
        return f"uir:v1:{':'.join(key_parts)}"
    
    def _serialize_response(self, response: SearchResponse) -> str:
        """Serialize response for caching"""
        return json.dumps(
            response.model_dump(),
            default=str
        )
    
    def _deserialize_response(self, data: str) -> SearchResponse:
        """Deserialize cached response"""
        return SearchResponse(**json.loads(data))
    
    def _evict_local_cache(self):
        """Evict oldest entries from local cache"""
        # Remove expired entries first
        now = datetime.now()
        expired_keys = [
            k for k, v in self.local_cache.items()
            if v["expires_at"] <= now
        ]
        for key in expired_keys:
            del self.local_cache[key]
        
        # If still too large, remove oldest entries
        if len(self.local_cache) > self.max_cache_size:
            # Sort by expiration time and remove oldest
            sorted_items = sorted(
                self.local_cache.items(),
                key=lambda x: x[1]["expires_at"]
            )
            
            # Remove 20% of oldest entries
            num_to_remove = len(self.local_cache) // 5
            for key, _ in sorted_items[:num_to_remove]:
                del self.local_cache[key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "local_cache_size": len(self.local_cache),
            "local_cache_keys": list(self.local_cache.keys())[:10],  # Sample
        }
        
        if self.redis_client:
            try:
                info = await self.redis_client.info("stats")
                stats["redis_hits"] = info.get("keyspace_hits", 0)
                stats["redis_misses"] = info.get("keyspace_misses", 0)
                stats["redis_hit_rate"] = (
                    info.get("keyspace_hits", 0) /
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                )
            except Exception as e:
                self.logger.error(f"Failed to get Redis stats: {e}")
        
        return stats
    
    async def close(self):
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()