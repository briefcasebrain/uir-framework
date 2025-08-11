"""Base provider adapter implementation"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from ..models import (
    ProviderConfig,
    SearchResult,
    SearchResponse,
    ResponseMetadata,
    ProviderHealth
)
from .circuit_breaker import CircuitBreaker
from .rate_limiter import RateLimiter

logger = structlog.get_logger()


class ProviderAdapter(ABC):
    """Base class for all provider adapters"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        self.type = config.type
        self.client = httpx.AsyncClient(timeout=config.timeout_ms / 1000)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_config.get("failure_threshold", 5),
            recovery_timeout=config.circuit_breaker_config.get("recovery_timeout", 60),
            expected_exception=Exception
        ) if config.circuit_breaker_config else None
        self.rate_limiter = RateLimiter(
            rate_limits=config.rate_limits
        ) if config.rate_limits else None
        self.logger = logger.bind(provider=self.name)
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Execute standard text search"""
        pass
    
    @abstractmethod
    async def vector_search(
        self,
        vector: List[float],
        options: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Execute vector similarity search"""
        pass
    
    @abstractmethod
    async def index(
        self,
        documents: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Index documents into the provider"""
        pass
    
    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Check provider health status"""
        pass
    
    @abstractmethod
    def transform_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform UIR request format to provider-specific format"""
        pass
    
    @abstractmethod
    def transform_response(self, response: Dict[str, Any]) -> List[SearchResult]:
        """Transform provider response to UIR format"""
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _execute_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute HTTP request with retry logic"""
        try:
            # Apply rate limiting if configured
            if self.rate_limiter:
                await self.rate_limiter.acquire()
            
            # Apply circuit breaker if configured
            if self.circuit_breaker:
                return await self.circuit_breaker.call(
                    self._make_request,
                    method,
                    endpoint,
                    **kwargs
                )
            else:
                return await self._make_request(method, endpoint, **kwargs)
                
        except Exception as e:
            self.logger.error(
                "Request failed",
                method=method,
                endpoint=endpoint,
                error=str(e)
            )
            raise
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to provider"""
        response = await self.client.request(
            method=method,
            url=endpoint,
            **kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def normalize_score(self, score: float, min_val: float = 0, max_val: float = 1) -> float:
        """Normalize score to 0-1 range"""
        if max_val == min_val:
            return 0.5
        return (score - min_val) / (max_val - min_val)
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()


class ProviderFactory:
    """Factory for creating provider adapters"""
    
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: type):
        """Register a provider adapter"""
        cls._providers[name] = adapter_class
    
    @classmethod
    def create(cls, config: ProviderConfig) -> ProviderAdapter:
        """Create a provider adapter instance"""
        adapter_class = cls._providers.get(config.name)
        if not adapter_class:
            raise ValueError(f"Unknown provider: {config.name}")
        return adapter_class(config)