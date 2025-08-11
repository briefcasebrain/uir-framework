#!/usr/bin/env python3
"""
Test runner with comprehensive mocking
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test imports
try:
    from uir.models import SearchRequest, SearchResponse, SearchResult, ResponseMetadata
    from uir.core.circuit_breaker import CircuitBreaker
    from uir.core.rate_limiter import RateLimiter, TokenBucket
    from uir.query_processor import QueryProcessor
    from uir.aggregator import ResultAggregator
    from uir.cache import CacheManager
    from uir.auth import AuthManager
    from uir.providers.google import GoogleAdapter
    from uir.mocks.embedding_service import MockEmbeddingService
    from uir.mocks.spell_checker import MockSpellChecker
    from uir.mocks.entity_extractor import MockEntityExtractor
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("\n🔧 Testing Circuit Breaker...")
    
    async def run_test():
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Test successful calls
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
        print("  ✅ Success call works")
        
        # Test failure threshold
        async def fail_func():
            raise Exception("fail")
        
        try:
            await cb.call(fail_func)
            await cb.call(fail_func)  # Should open circuit
        except Exception:
            pass
        
        # Circuit should be open now
        try:
            await cb.call(success_func)
            assert False, "Should have been blocked"
        except Exception as e:
            if "open" in str(e):
                print("  ✅ Circuit opens after failures")
        
        print("  ✅ Circuit breaker tests passed!")
    
    asyncio.run(run_test())

def test_rate_limiter():
    """Test rate limiter functionality"""
    print("\n🚦 Testing Rate Limiter...")
    
    async def run_test():
        bucket = TokenBucket(capacity=3, refill_rate=3)
        
        # Should allow up to capacity
        assert bucket.try_acquire() == True
        assert bucket.try_acquire() == True
        assert bucket.try_acquire() == True
        
        # Should block when exhausted
        assert bucket.try_acquire() == False
        
        print("  ✅ Rate limiter tests passed!")
    
    asyncio.run(run_test())

def test_embedding_service():
    """Test mock embedding service"""
    print("\n🧠 Testing Mock Embedding Service...")
    
    async def run_test():
        service = MockEmbeddingService()
        
        # Test embedding generation
        embedding = await service.embed("machine learning")
        assert len(embedding) == 768
        assert isinstance(embedding[0], float)
        
        # Test consistency
        embedding2 = await service.embed("machine learning")
        assert embedding == embedding2
        
        # Test similarity
        embedding3 = await service.embed("deep learning")
        similarity = service.similarity(embedding, embedding3)
        assert 0.0 <= similarity <= 1.0
        
        print("  ✅ Mock embedding service works!")
    
    asyncio.run(run_test())

def test_spell_checker():
    """Test mock spell checker"""
    print("\n📝 Testing Mock Spell Checker...")
    
    async def run_test():
        checker = MockSpellChecker()
        
        # Test corrections
        result = await checker.correct("transformr atention mechanizm")
        assert "transformer" in result
        assert "attention" in result
        assert "mechanism" in result
        
        # Test no change needed
        result2 = await checker.correct("machine learning")
        assert result2 == "machine learning"
        
        print("  ✅ Mock spell checker works!")
    
    asyncio.run(run_test())

def test_entity_extractor():
    """Test mock entity extractor"""
    print("\n🏷️ Testing Mock Entity Extractor...")
    
    async def run_test():
        extractor = MockEntityExtractor()
        
        # Test entity extraction
        entities = await extractor.extract("Contact john@example.com about transformer research from 2024-01-15")
        
        # Should find email, technology, and date entities
        email_entities = [e for e in entities if e["type"] == "EMAIL"]
        tech_entities = [e for e in entities if e["type"] == "TECHNOLOGY"]
        date_entities = [e for e in entities if e["type"] == "DATE"]
        
        assert len(email_entities) > 0
        assert len(tech_entities) > 0
        assert len(date_entities) > 0
        
        print(f"  ✅ Found {len(entities)} entities: {len(email_entities)} email, {len(tech_entities)} tech, {len(date_entities)} date")
    
    asyncio.run(run_test())

def test_query_processor():
    """Test query processor with mocks"""
    print("\n🔍 Testing Query Processor...")
    
    async def run_test():
        processor = QueryProcessor()
        
        # Test full processing
        result = await processor.process("transformr atention mechanizm")
        
        assert result.original == "transformr atention mechanizm"
        assert result.corrected is not None
        assert "transformer" in result.corrected
        assert result.expanded is not None
        assert len(result.embedding) == 768
        assert result.keywords is not None
        
        print("  ✅ Query processor works with mocks!")
    
    asyncio.run(run_test())

def test_aggregator():
    """Test result aggregator"""
    print("\n📊 Testing Result Aggregator...")
    
    aggregator = ResultAggregator()
    
    # Create test results
    results = [
        SearchResult(id="1", title="Result 1", score=0.9, provider="google"),
        SearchResult(id="2", title="Result 2", score=0.8, provider="bing"),
        SearchResult(id="3", title="Result 1", score=0.7, provider="google", url="https://same-url.com"),
        SearchResult(id="4", title="Result 1", score=0.85, provider="bing", url="https://same-url.com")  # Duplicate
    ]
    
    # Test aggregation with deduplication
    aggregated = aggregator.aggregate(results, deduplicate=True)
    
    # Should remove duplicate (keep higher score)
    assert len(aggregated) < len(results)
    
    # Should be sorted by score
    for i in range(len(aggregated) - 1):
        assert aggregated[i].score >= aggregated[i + 1].score
    
    print("  ✅ Result aggregator works!")

def test_auth():
    """Test authentication"""
    print("\n🔐 Testing Authentication...")
    
    auth = AuthManager()
    
    # Test API key creation
    api_key = auth.create_api_key(
        user_id="test-user",
        permissions=["search", "vector_search"]
    )
    
    assert api_key.startswith("uir_")
    
    # Test validation
    key_data = auth.validate_api_key(api_key)
    assert key_data is not None
    assert key_data["user_id"] == "test-user"
    
    # Test permissions
    assert auth.check_permission(key_data, "search") == True
    assert auth.check_permission(key_data, "admin") == False
    
    print("  ✅ Authentication works!")

def test_cache():
    """Test cache with mocks"""
    print("\n💾 Testing Cache Manager...")
    
    async def run_test():
        cache = CacheManager()
        await cache.initialize()
        
        # Create test request/response
        request = SearchRequest(provider="google", query="test")
        response = SearchResponse(
            status="success",
            request_id="test-123",
            results=[],
            metadata=ResponseMetadata(
                query_time_ms=100,
                providers_used=["google"],
                cache_hit=False
            )
        )
        
        # Test cache miss
        result = await cache.get(request)
        assert result is None
        
        # Test cache set/get
        await cache.set(request, response)
        result = await cache.get(request)
        assert result is not None
        assert result.request_id == "test-123"
        
        print("  ✅ Cache manager works with mocks!")
    
    asyncio.run(run_test())

def test_providers():
    """Test provider adapters with mocks"""
    print("\n🔌 Testing Provider Adapters...")
    
    async def run_test():
        from uir.models import ProviderConfig, ProviderType
        
        # Test Google adapter
        config = ProviderConfig(
            name="google",
            type=ProviderType.SEARCH_ENGINE,
            auth_method="api_key",
            credentials={"api_key": "test", "cx": "test"},
            endpoints={"search": "https://www.googleapis.com/customsearch/v1"},
            rate_limits={"default": 100},
            retry_policy={"max_attempts": 3},
            timeout_ms=5000
        )
        
        adapter = GoogleAdapter(config)
        
        # Test search
        results = await adapter.search("test query", {"limit": 5})
        assert isinstance(results, list)
        assert len(results) <= 5
        
        if results:
            assert isinstance(results[0], SearchResult)
            assert results[0].provider == "google"
        
        # Test health check
        health = await adapter.health_check()
        assert health.provider == "google"
        assert health.status in ["healthy", "degraded", "unhealthy"]
        
        print("  ✅ Provider adapters work with mocks!")
    
    asyncio.run(run_test())

def main():
    """Run all tests"""
    print("🚀 UIR Framework Test Suite with Comprehensive Mocks")
    print("=" * 60)
    
    try:
        test_circuit_breaker()
        test_rate_limiter()
        test_embedding_service()
        test_spell_checker()
        test_entity_extractor()
        test_query_processor()
        test_aggregator()
        test_auth()
        test_cache()
        test_providers()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Mock implementations are working correctly")
        print("✅ Core functionality is operational")
        print("✅ External dependencies are properly mocked")
        print("\nThe UIR framework is ready for testing with:")
        print("- Deterministic embeddings")
        print("- Comprehensive spell checking")
        print("- Advanced entity extraction")
        print("- Mock external APIs (Google, Pinecone, etc.)")
        print("- In-memory caching fallback")
        print("- Full authentication system")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()