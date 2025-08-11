"""Pytest configuration and shared fixtures"""

import pytest
import asyncio
from typing import Dict, List, Any
from datetime import datetime
import json

from src.uir.models import (
    SearchResult,
    SearchResponse,
    ResponseMetadata,
    ProviderConfig,
    ProviderType,
    SearchOptions,
    CacheOptions
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        SearchResult(
            id="1",
            title="Machine Learning Introduction",
            content="An introduction to machine learning concepts",
            url="https://example.com/ml-intro",
            score=0.95,
            provider="google",
            metadata={"author": "John Doe"}
        ),
        SearchResult(
            id="2",
            title="Deep Learning Fundamentals",
            content="Understanding deep neural networks",
            url="https://example.com/deep-learning",
            score=0.92,
            provider="google",
            metadata={"author": "Jane Smith"}
        ),
        SearchResult(
            id="3",
            title="Machine Learning Tutorial",
            content="Step by step ML tutorial",
            url="https://example.com/ml-tutorial",
            score=0.88,
            provider="bing",
            metadata={"type": "tutorial"}
        )
    ]


@pytest.fixture
def sample_vector_results():
    """Sample vector search results"""
    return [
        SearchResult(
            id="vec1",
            title="Transformer Architecture",
            content="Understanding attention mechanisms",
            score=0.98,
            provider="pinecone",
            vector=[0.1, 0.2, 0.3],
            metadata={"index": "papers"}
        ),
        SearchResult(
            id="vec2",
            title="BERT Model",
            content="Bidirectional transformers explained",
            score=0.94,
            provider="pinecone",
            vector=[0.2, 0.3, 0.4],
            metadata={"index": "papers"}
        )
    ]


@pytest.fixture
def sample_search_response():
    """Sample search response"""
    return SearchResponse(
        status="success",
        request_id="test-123",
        results=[
            SearchResult(
                id="1",
                title="Test Result",
                score=0.9,
                provider="google"
            )
        ],
        metadata=ResponseMetadata(
            query_time_ms=150,
            providers_used=["google"],
            cache_hit=False
        )
    )


@pytest.fixture
def provider_config():
    """Sample provider configuration"""
    return ProviderConfig(
        name="test_provider",
        type=ProviderType.SEARCH_ENGINE,
        auth_method="api_key",
        credentials={"api_key": "test-key"},
        endpoints={"search": "https://api.test.com/search"},
        rate_limits={"default": 100},
        retry_policy={"max_attempts": 3},
        timeout_ms=5000,
        circuit_breaker_config={
            "failure_threshold": 5,
            "recovery_timeout": 60
        }
    )


@pytest.fixture
def google_config():
    """Google provider configuration"""
    return ProviderConfig(
        name="google",
        type=ProviderType.SEARCH_ENGINE,
        auth_method="api_key",
        credentials={
            "api_key": "test-google-key",
            "cx": "test-search-engine-id"
        },
        endpoints={"search": "https://www.googleapis.com/customsearch/v1"},
        rate_limits={"default": 100},
        retry_policy={"max_attempts": 3},
        timeout_ms=5000
    )


@pytest.fixture
def pinecone_config():
    """Pinecone provider configuration"""
    return ProviderConfig(
        name="pinecone",
        type=ProviderType.VECTOR_DB,
        auth_method="api_key",
        credentials={
            "api_key": "test-pinecone-key",
            "environment": "us-west1-gcp",
            "index_name": "test-index"
        },
        endpoints={"query": "https://test-index.svc.us-west1-gcp.pinecone.io"},
        rate_limits={"default": 100},
        retry_policy={"max_attempts": 3},
        timeout_ms=5000
    )


@pytest.fixture
def elasticsearch_config():
    """Elasticsearch provider configuration"""
    return ProviderConfig(
        name="elasticsearch",
        type=ProviderType.DOCUMENT_STORE,
        auth_method="basic",
        credentials={
            "host": "localhost",
            "port": 9200,
            "username": "elastic",
            "password": "test-password",
            "use_ssl": False
        },
        endpoints={"search": "http://localhost:9200"},
        rate_limits={"default": 1000},
        retry_policy={"max_attempts": 3},
        timeout_ms=5000
    )


@pytest.fixture
def mock_api_key_data():
    """Mock API key data"""
    return {
        "user_id": "test-user",
        "permissions": ["search", "vector_search", "hybrid_search"],
        "rate_limit": 1000,
        "created_at": datetime.now()
    }


@pytest.fixture
def search_options():
    """Sample search options"""
    return SearchOptions(
        limit=10,
        offset=0,
        filters={"category": "technology"},
        rerank=True,
        cache=CacheOptions(enabled=True, ttl_seconds=3600)
    )


class MockHttpResponse:
    """Mock HTTP response for testing"""
    
    def __init__(self, json_data=None, status_code=200, text=""):
        self._json_data = json_data
        self.status_code = status_code
        self.text = text
    
    def json(self):
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class MockAsyncClient:
    """Mock async HTTP client"""
    
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.requests = []
    
    async def request(self, method, url, **kwargs):
        self.requests.append({
            "method": method,
            "url": url,
            **kwargs
        })
        
        # Return mock response based on URL
        for pattern, response in self.responses.items():
            if pattern in url:
                return MockHttpResponse(response)
        
        return MockHttpResponse({"results": []})
    
    async def get(self, url, **kwargs):
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url, **kwargs):
        return await self.request("POST", url, **kwargs)
    
    async def aclose(self):
        pass


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client"""
    return MockAsyncClient()


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def setex(self, key, ttl, value):
            self.data[key] = value
        
        async def delete(self, *keys):
            for key in keys:
                self.data.pop(key, None)
        
        async def keys(self, pattern):
            return [k for k in self.data.keys() if pattern.replace("*", "") in k]
        
        async def flushdb(self):
            self.data.clear()
        
        async def ping(self):
            return True
        
        async def info(self, section):
            return {
                "keyspace_hits": 100,
                "keyspace_misses": 20
            }
        
        async def close(self):
            pass
    
    return MockRedis()


@pytest.fixture
def sample_documents():
    """Sample documents for indexing"""
    return [
        {
            "id": "doc1",
            "title": "Introduction to AI",
            "content": "Artificial intelligence is transforming the world",
            "vector": [0.1, 0.2, 0.3],
            "metadata": {"category": "AI", "date": "2024-01-01"}
        },
        {
            "id": "doc2",
            "title": "Machine Learning Basics",
            "content": "Understanding supervised and unsupervised learning",
            "vector": [0.2, 0.3, 0.4],
            "metadata": {"category": "ML", "date": "2024-01-02"}
        }
    ]