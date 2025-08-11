"""Python SDK client for UIR framework"""

import os
from typing import Dict, List, Any, Optional, Union
import httpx
import asyncio
from dataclasses import dataclass

from .models import (
    SearchRequest,
    SearchResponse,
    VectorSearchRequest,
    HybridSearchRequest,
    HybridStrategy,
    SearchOptions,
    SearchResult,
    QueryAnalysis,
    IndexRequest,
    Provider
)


@dataclass
class UIRConfig:
    """Configuration for UIR client"""
    api_key: Optional[str] = None
    base_url: str = "http://localhost:8000"
    timeout: int = 30
    provider_keys: Optional[Dict[str, Any]] = None
    default_provider: Optional[str] = None


class UIR:
    """Universal Information Retrieval client"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider_keys: Optional[Dict[str, Any]] = None,
        config: Optional[UIRConfig] = None
    ):
        """
        Initialize UIR client
        
        Args:
            api_key: Master API key for UIR service
            base_url: Base URL for UIR API
            provider_keys: Provider-specific API keys
            config: Complete configuration object
        """
        if config:
            self.config = config
        else:
            self.config = UIRConfig(
                api_key=api_key or os.getenv("UIR_API_KEY"),
                base_url=base_url or os.getenv("UIR_BASE_URL", "http://localhost:8000"),
                provider_keys=provider_keys or {}
            )
        
        self.client = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers=self._get_headers()
        )
        
        self.async_client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers=self._get_headers()
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "UIR-Python-SDK/1.0.0"
        }
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        return headers
    
    def search(
        self,
        provider: Union[str, List[str]],
        query: str,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = False,
        cache: bool = True,
        **kwargs
    ) -> SearchResponse:
        """
        Perform standard text search
        
        Args:
            provider: Provider name(s) to use
            query: Search query
            limit: Maximum number of results
            offset: Result offset for pagination
            filters: Search filters
            rerank: Whether to rerank results
            cache: Whether to use caching
            **kwargs: Additional options
        
        Returns:
            SearchResponse with results
        """
        request = SearchRequest(
            provider=provider,
            query=query,
            options=SearchOptions(
                limit=limit,
                offset=offset,
                filters=filters,
                rerank=rerank,
                cache={"enabled": cache},
                **kwargs
            )
        )
        
        response = self.client.post(
            "/search",
            json=request.model_dump()
        )
        response.raise_for_status()
        
        return SearchResponse(**response.json())
    
    async def search_async(
        self,
        provider: Union[str, List[str]],
        query: str,
        **kwargs
    ) -> SearchResponse:
        """Async version of search"""
        request = SearchRequest(
            provider=provider,
            query=query,
            options=SearchOptions(**kwargs) if kwargs else None
        )
        
        response = await self.async_client.post(
            "/search",
            json=request.model_dump()
        )
        response.raise_for_status()
        
        return SearchResponse(**response.json())
    
    def vector_search(
        self,
        provider: Union[str, List[str]],
        vector: Optional[List[float]] = None,
        text: Optional[str] = None,
        index: Optional[str] = None,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SearchResponse:
        """
        Perform vector similarity search
        
        Args:
            provider: Vector database provider(s)
            vector: Query vector
            text: Text to convert to vector
            index: Index/collection name
            top_k: Number of results
            filters: Metadata filters
            **kwargs: Additional options
        
        Returns:
            SearchResponse with results
        """
        request = VectorSearchRequest(
            provider=provider,
            vector=vector,
            text=text,
            index=index,
            options=SearchOptions(
                limit=top_k,
                filters=filters,
                **kwargs
            )
        )
        
        response = self.client.post(
            "/vector/search",
            json=request.model_dump()
        )
        response.raise_for_status()
        
        return SearchResponse(**response.json())
    
    def hybrid_search(
        self,
        strategies: List[Dict[str, Any]],
        fusion_method: str = "reciprocal_rank",
        limit: int = 10,
        **kwargs
    ) -> SearchResponse:
        """
        Perform hybrid search combining multiple strategies
        
        Args:
            strategies: List of search strategies
            fusion_method: Method to combine results
            limit: Maximum results
            **kwargs: Additional options
        
        Returns:
            SearchResponse with fused results
        """
        # Convert strategy dicts to HybridStrategy objects
        strategy_objects = []
        for s in strategies:
            strategy_objects.append(HybridStrategy(**s))
        
        request = HybridSearchRequest(
            strategies=strategy_objects,
            fusion_method=fusion_method,
            options=SearchOptions(limit=limit, **kwargs) if kwargs else None
        )
        
        response = self.client.post(
            "/hybrid/search",
            json=request.model_dump()
        )
        response.raise_for_status()
        
        return SearchResponse(**response.json())
    
    def rag_retrieve(
        self,
        query: str,
        providers: List[str],
        num_chunks: int = 5,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Retrieve context for RAG pipelines
        
        Args:
            query: User query
            providers: Providers to search
            num_chunks: Number of chunks to retrieve
            max_tokens: Maximum tokens in context
            **kwargs: Additional options
        
        Returns:
            Context and chunks for RAG
        """
        response = self.client.post(
            "/rag/retrieve",
            json={
                "query": query,
                "providers": providers,
                "options": {
                    "num_chunks": num_chunks,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            }
        )
        response.raise_for_status()
        
        return response.json()
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze and enhance query
        
        Args:
            query: Query to analyze
        
        Returns:
            QueryAnalysis with enhancements
        """
        response = self.client.post(
            "/query/analyze",
            json={"query": query}
        )
        response.raise_for_status()
        
        return QueryAnalysis(**response.json())
    
    def index_documents(
        self,
        provider: str,
        documents: List[Dict[str, Any]],
        index_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Index documents into a provider
        
        Args:
            provider: Provider to index into
            documents: Documents to index
            index_name: Target index/collection
            **kwargs: Additional options
        
        Returns:
            Indexing result
        """
        request = IndexRequest(
            provider=provider,
            documents=documents,
            index_name=index_name,
            options=kwargs if kwargs else None
        )
        
        response = self.client.post(
            "/documents/index",
            json=request.model_dump()
        )
        response.raise_for_status()
        
        return response.json()
    
    def batch_search(
        self,
        queries: List[Dict[str, Any]],
        parallel: bool = True,
        **kwargs
    ) -> List[SearchResponse]:
        """
        Perform multiple searches in batch
        
        Args:
            queries: List of search queries
            parallel: Execute in parallel
            **kwargs: Additional options
        
        Returns:
            List of SearchResponse objects
        """
        response = self.client.post(
            "/batch/search",
            json={
                "queries": queries,
                "options": {
                    "parallel": parallel,
                    **kwargs
                }
            }
        )
        response.raise_for_status()
        
        results = response.json()["results"]
        return [SearchResponse(**r) for r in results]
    
    def search_stream(
        self,
        provider: Union[str, List[str]],
        query: str,
        **kwargs
    ):
        """
        Stream search results
        
        Args:
            provider: Provider(s) to use
            query: Search query
            **kwargs: Additional options
        
        Yields:
            SearchResult objects as they arrive
        """
        request = SearchRequest(
            provider=provider,
            query=query,
            options=SearchOptions(**kwargs) if kwargs else None
        )
        
        with self.client.stream(
            "POST",
            "/search/stream",
            json=request.model_dump()
        ) as response:
            for line in response.iter_lines():
                if line:
                    yield SearchResult(**response.json())
    
    def get_providers(self) -> Dict[str, Any]:
        """Get available providers and their capabilities"""
        response = self.client.get("/providers")
        response.raise_for_status()
        return response.json()
    
    def get_usage(self, period: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics
        
        Args:
            period: Time period (e.g., "2024-01")
        
        Returns:
            Usage statistics
        """
        params = {"period": period} if period else {}
        response = self.client.get("/usage", params=params)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        response = self.client.get("/health")
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close client connections"""
        self.client.close()
        if hasattr(self, "async_client"):
            asyncio.run(self.async_client.aclose())
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.async_client.aclose()