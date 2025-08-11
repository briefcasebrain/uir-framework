"""Request router and orchestration service"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import structlog

from .models import (
    SearchRequest,
    VectorSearchRequest,
    HybridSearchRequest,
    SearchResponse,
    SearchResult,
    ResponseMetadata,
    Provider,
    ProviderType
)
from .core.adapter import ProviderFactory
from .providers.manager import ProviderManager
from .query_processor import QueryProcessor
from .aggregator import ResultAggregator
from .cache import CacheManager

logger = structlog.get_logger()


class RouterService:
    """Main router service for request orchestration"""
    
    def __init__(
        self,
        provider_manager: ProviderManager,
        query_processor: QueryProcessor,
        aggregator: ResultAggregator,
        cache_manager: Optional[CacheManager] = None
    ):
        self.provider_manager = provider_manager
        self.query_processor = query_processor
        self.aggregator = aggregator
        self.cache_manager = cache_manager
        self.logger = logger.bind(service="router")
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Handle standard search request"""
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Check cache if enabled
            if self.cache_manager and request.options and request.options.cache:
                cached_result = await self.cache_manager.get(request)
                if cached_result:
                    self.logger.info("Cache hit", request_id=request_id)
                    return cached_result
            
            # Process query
            processed_query = await self.query_processor.process(request.query)
            
            # Select providers
            providers = self._normalize_providers(request.provider)
            available_providers = await self.provider_manager.get_available_providers(providers)
            
            if not available_providers:
                # Try fallback providers
                if request.options and request.options.fallback_providers:
                    available_providers = await self.provider_manager.get_available_providers(
                        request.options.fallback_providers
                    )
            
            if not available_providers:
                return self._error_response(
                    request_id,
                    "No available providers",
                    start_time
                )
            
            # Execute parallel searches
            search_tasks = []
            for provider_name in available_providers:
                adapter = await self.provider_manager.get_adapter(provider_name)
                if adapter:
                    search_tasks.append(
                        self._execute_provider_search(
                            adapter,
                            processed_query.corrected or request.query,
                            request.options
                        )
                    )
            
            # Gather results with timeout
            timeout = (request.options.timeout_ms if request.options else 5000) / 1000
            results = await asyncio.gather(
                *search_tasks,
                return_exceptions=True
            )
            
            # Filter out errors and flatten results
            all_results = []
            failed_providers = []
            successful_providers = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        "Provider search failed",
                        provider=available_providers[i],
                        error=str(result)
                    )
                    failed_providers.append(available_providers[i])
                else:
                    all_results.extend(result)
                    successful_providers.append(available_providers[i])
            
            # Aggregate and rank results
            if request.options and request.options.rerank:
                final_results = await self.aggregator.rerank(
                    all_results,
                    processed_query.corrected or request.query
                )
            else:
                final_results = self.aggregator.aggregate(
                    all_results,
                    deduplicate=request.options.deduplicate if request.options else True
                )
            
            # Apply filters
            if request.options and request.options.min_score:
                final_results = [
                    r for r in final_results 
                    if r.score >= request.options.min_score
                ]
            
            # Limit results
            limit = request.options.limit if request.options else 10
            final_results = final_results[:limit]
            
            # Build response
            response = SearchResponse(
                status="success" if not failed_providers else "partial",
                request_id=request_id,
                results=final_results,
                metadata=ResponseMetadata(
                    query_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    providers_used=successful_providers,
                    providers_failed=failed_providers if failed_providers else None,
                    cache_hit=False,
                    spell_corrected=processed_query.corrected is not None,
                    filters_applied=processed_query.filters if processed_query.filters else None
                ),
                provider_used=successful_providers[0] if len(successful_providers) == 1 else None,
                query_id=request_id
            )
            
            # Store in cache
            if self.cache_manager and request.options and request.options.cache:
                await self.cache_manager.set(request, response)
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Search request failed",
                request_id=request_id,
                error=str(e)
            )
            return self._error_response(request_id, str(e), start_time)
    
    async def vector_search(self, request: VectorSearchRequest) -> SearchResponse:
        """Handle vector search request"""
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Get vector (generate from text if needed)
            vector = request.vector
            if not vector and request.text:
                vector = await self.query_processor.generate_embedding(request.text)
            
            if not vector:
                return self._error_response(
                    request_id,
                    "No vector or text provided",
                    start_time
                )
            
            # Select providers
            providers = self._normalize_providers(request.provider)
            available_providers = await self.provider_manager.get_available_providers(
                providers,
                provider_type=ProviderType.VECTOR_DB
            )
            
            # Execute parallel vector searches
            search_tasks = []
            for provider_name in available_providers:
                adapter = await self.provider_manager.get_adapter(provider_name)
                if adapter:
                    search_tasks.append(
                        adapter.vector_search(
                            vector=vector,
                            options={
                                "index": request.index,
                                "namespace": request.namespace,
                                **(request.options.model_dump() if request.options else {})
                            }
                        )
                    )
            
            # Gather results
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results
            all_results = []
            failed_providers = []
            successful_providers = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_providers.append(available_providers[i])
                else:
                    all_results.extend(result)
                    successful_providers.append(available_providers[i])
            
            # Aggregate results
            final_results = self.aggregator.aggregate(all_results)
            
            return SearchResponse(
                status="success" if not failed_providers else "partial",
                request_id=request_id,
                results=final_results,
                metadata=ResponseMetadata(
                    query_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    providers_used=successful_providers,
                    providers_failed=failed_providers if failed_providers else None,
                    cache_hit=False
                )
            )
            
        except Exception as e:
            self.logger.error(
                "Vector search failed",
                request_id=request_id,
                error=str(e)
            )
            return self._error_response(request_id, str(e), start_time)
    
    async def hybrid_search(self, request: HybridSearchRequest) -> SearchResponse:
        """Handle hybrid search combining multiple strategies"""
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Execute each strategy in parallel
            strategy_tasks = []
            strategy_weights = []
            
            for strategy in request.strategies:
                adapter = await self.provider_manager.get_adapter(strategy.provider)
                if adapter:
                    if strategy.type == "keyword":
                        strategy_tasks.append(
                            adapter.search(
                                query=strategy.query or "",
                                options=strategy.options
                            )
                        )
                    elif strategy.type == "vector":
                        vector = strategy.vector
                        if not vector and strategy.text:
                            vector = await self.query_processor.generate_embedding(strategy.text)
                        if vector:
                            strategy_tasks.append(
                                adapter.vector_search(
                                    vector=vector,
                                    options=strategy.options
                                )
                            )
                    
                    strategy_weights.append(strategy.weight)
            
            # Execute all strategies
            results = await asyncio.gather(*strategy_tasks, return_exceptions=True)
            
            # Combine results using fusion method
            all_results = []
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    # Apply weight to scores
                    weight = strategy_weights[i]
                    for r in result:
                        r.score *= weight
                    all_results.append(result)
            
            # Fuse results based on method
            if request.fusion_method == "reciprocal_rank":
                final_results = self.aggregator.reciprocal_rank_fusion(all_results)
            elif request.fusion_method == "weighted_sum":
                final_results = self.aggregator.weighted_sum_fusion(all_results)
            else:
                final_results = self.aggregator.max_score_fusion(all_results)
            
            return SearchResponse(
                status="success",
                request_id=request_id,
                results=final_results,
                metadata=ResponseMetadata(
                    query_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    providers_used=[s.provider for s in request.strategies],
                    cache_hit=False
                )
            )
            
        except Exception as e:
            self.logger.error(
                "Hybrid search failed",
                request_id=request_id,
                error=str(e)
            )
            return self._error_response(request_id, str(e), start_time)
    
    async def _execute_provider_search(
        self,
        adapter,
        query: str,
        options: Optional[Any]
    ) -> List[SearchResult]:
        """Execute search on a single provider"""
        try:
            return await adapter.search(
                query=query,
                options=options.model_dump() if options else None
            )
        except Exception as e:
            self.logger.error(
                "Provider search failed",
                provider=adapter.name,
                error=str(e)
            )
            raise
    
    def _normalize_providers(
        self,
        providers: Union[str, List[str]]
    ) -> List[str]:
        """Normalize provider input to list"""
        if isinstance(providers, str):
            return [providers]
        return providers
    
    def _error_response(
        self,
        request_id: str,
        error_message: str,
        start_time: datetime
    ) -> SearchResponse:
        """Create error response"""
        return SearchResponse(
            status="error",
            request_id=request_id,
            results=[],
            metadata=ResponseMetadata(
                query_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                providers_used=[],
                cache_hit=False
            ),
            errors=[{"message": error_message}]
        )