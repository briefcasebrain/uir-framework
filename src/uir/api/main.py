"""FastAPI application for UIR framework"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import os
import structlog

from ..models import (
    SearchRequest,
    SearchResponse,
    VectorSearchRequest,
    HybridSearchRequest,
    QueryAnalysis
)
from ..router import RouterService
from ..query_processor import QueryProcessor
from ..aggregator import ResultAggregator
from ..cache import CacheManager
from ..auth import AuthManager, RateLimitManager
from ..providers.manager import ProviderManager
from ..providers import GoogleAdapter, PineconeAdapter, ElasticsearchAdapter
from ..core.adapter import ProviderFactory
from ..models import ProviderConfig, ProviderType

# Configure logging
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Universal Information Retrieval API",
    description="Unified interface for multiple information retrieval providers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
auth_manager = AuthManager()
rate_limiter = RateLimitManager()
provider_manager = ProviderManager()
query_processor = QueryProcessor()
aggregator = ResultAggregator()
cache_manager = None
router_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global cache_manager, router_service
    
    # Initialize cache
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache_manager = CacheManager(redis_url=redis_url)
    await cache_manager.initialize()
    
    # Register provider adapters
    ProviderFactory.register("google", GoogleAdapter)
    ProviderFactory.register("pinecone", PineconeAdapter)
    ProviderFactory.register("elasticsearch", ElasticsearchAdapter)
    
    # Initialize provider manager with sample configs
    # In production, load from database or config file
    sample_configs = {
        "google": ProviderConfig(
            name="google",
            type=ProviderType.SEARCH_ENGINE,
            auth_method="api_key",
            credentials={"api_key": "test-google-key", "cx": "test-search-engine"},
            endpoints={"search": "https://www.googleapis.com/customsearch/v1"},
            rate_limits={"default": 100},
            retry_policy={"max_attempts": 3},
            timeout_ms=5000,
            circuit_breaker_config={"failure_threshold": 5, "recovery_timeout": 60}
        ),
        "pinecone": ProviderConfig(
            name="pinecone",
            type=ProviderType.VECTOR_DB,
            auth_method="api_key",
            credentials={"api_key": "test-pinecone-key", "environment": "us-west1-gcp", "index_name": "test-index"},
            endpoints={"query": "https://test-index.svc.us-west1-gcp.pinecone.io"},
            rate_limits={"default": 100},
            retry_policy={"max_attempts": 3},
            timeout_ms=5000,
            circuit_breaker_config={"failure_threshold": 5, "recovery_timeout": 60}
        ),
        "elasticsearch": ProviderConfig(
            name="elasticsearch",
            type=ProviderType.DOCUMENT_STORE,
            auth_method="basic",
            credentials={"host": "localhost", "port": 9200, "use_ssl": False},
            endpoints={"search": "http://localhost:9200"},
            rate_limits={"default": 1000},
            retry_policy={"max_attempts": 3},
            timeout_ms=5000,
            circuit_breaker_config={"failure_threshold": 5, "recovery_timeout": 60}
        )
    }
    
    await provider_manager.initialize(sample_configs)
    
    # Initialize router service
    router_service = RouterService(
        provider_manager=provider_manager,
        query_processor=query_processor,
        aggregator=aggregator,
        cache_manager=cache_manager
    )
    
    logger.info("UIR API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if cache_manager:
        await cache_manager.close()
    if provider_manager:
        await provider_manager.shutdown()
    
    logger.info("UIR API shut down")


async def verify_api_key(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify API key from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    api_key = authorization[7:]  # Remove "Bearer " prefix
    key_data = auth_manager.validate_api_key(api_key)
    
    if not key_data:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check rate limit
    limit = key_data.get("rate_limit", 1000)
    if not rate_limiter.check_rate_limit(api_key, limit):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return key_data


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Universal Information Retrieval API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cache": "connected" if cache_manager else "disconnected",
        "providers": provider_manager.get_provider_stats()
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Check if essential services are ready
    ready = router_service is not None
    return {"ready": ready}


@app.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    key_data: Dict = Depends(verify_api_key)
):
    """Execute standard text search"""
    try:
        # Check permission
        if not auth_manager.check_permission(key_data, "search"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        response = await router_service.search(request)
        return response
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vector/search", response_model=SearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    key_data: Dict = Depends(verify_api_key)
):
    """Execute vector similarity search"""
    try:
        # Check permission
        if not auth_manager.check_permission(key_data, "vector_search"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        response = await router_service.vector_search(request)
        return response
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/hybrid/search", response_model=SearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    key_data: Dict = Depends(verify_api_key)
):
    """Execute hybrid search combining multiple strategies"""
    try:
        # Check permission
        if not auth_manager.check_permission(key_data, "hybrid_search"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        response = await router_service.hybrid_search(request)
        return response
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/analyze", response_model=QueryAnalysis)
async def analyze_query(
    query_request: Dict[str, str],
    key_data: Dict = Depends(verify_api_key)
):
    """Analyze and enhance query"""
    try:
        query = query_request.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        processed = await query_processor.process(query)
        
        return QueryAnalysis(
            original_query=query,
            corrected_query=processed.corrected,
            expanded_query=processed.expanded,
            entities=processed.entities,
            intent=processed.intent,
            suggested_filters=processed.filters,
            keywords=processed.keywords
        )
    except Exception as e:
        logger.error(f"Query analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/providers")
async def get_providers(key_data: Dict = Depends(verify_api_key)):
    """Get available providers and their capabilities"""
    return {
        "providers": provider_manager.get_provider_stats()
    }


@app.get("/usage")
async def get_usage(
    period: Optional[str] = None,
    key_data: Dict = Depends(verify_api_key)
):
    """Get usage statistics"""
    # In production, would query from database
    return {
        "period": period or "current",
        "user_id": key_data.get("user_id"),
        "total_requests": key_data.get("usage_count", 0),
        "rate_limit": key_data.get("rate_limit", 1000)
    }


@app.post("/rag/retrieve")
async def rag_retrieve(
    request: Dict[str, Any],
    key_data: Dict = Depends(verify_api_key)
):
    """Retrieve context for RAG pipelines"""
    try:
        # Check permission
        if not auth_manager.check_permission(key_data, "rag"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Execute search across providers
        search_request = SearchRequest(
            provider=request.get("providers", ["elasticsearch"]),
            query=request.get("query"),
            options=request.get("options")
        )
        
        response = await router_service.search(search_request)
        
        # Format for RAG
        chunks = []
        for result in response.results[:request.get("options", {}).get("num_chunks", 5)]:
            chunks.append({
                "text": result.content or result.snippet,
                "source": result.url or result.id,
                "score": result.score,
                "metadata": result.metadata
            })
        
        return {
            "status": "success",
            "context": "\n\n".join([c["text"] for c in chunks if c["text"]]),
            "chunks": chunks,
            "metadata": {
                "providers_queried": response.metadata.providers_used,
                "query_time_ms": response.metadata.query_time_ms
            }
        }
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )


def main():
    """Entry point for running the UIR API server."""
    import uvicorn
    import os
    
    host = os.getenv("UIR_API_HOST", "0.0.0.0")
    port = int(os.getenv("UIR_API_PORT", "8000"))
    workers = int(os.getenv("UIR_WORKERS", "1"))
    
    uvicorn.run(
        "uir.api.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
        reload=False
    )


if __name__ == "__main__":
    main()