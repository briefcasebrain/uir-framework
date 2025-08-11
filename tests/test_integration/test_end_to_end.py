"""End-to-end integration tests"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from uir.client import UIR
from uir.models import SearchRequest, SearchResponse, SearchResult


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization"""
    client = UIR(
        api_key="test-key",
        provider_keys={
            "google": {"api_key": "test", "cx": "test"},
            "pinecone": "test-key"
        }
    )
    assert client is not None
    assert client.api_key == "test-key"


@pytest.mark.asyncio
async def test_search_with_mock_provider():
    """Test search with mocked provider"""
    with patch('uir.providers.manager.ProviderManager') as mock_manager:
        mock_provider = Mock()
        mock_provider.search.return_value = [
            SearchResult(
                id="1",
                title="Test Result",
                url="https://example.com",
                snippet="Test snippet",
                score=0.95,
                provider="google"
            )
        ]
        mock_manager.return_value.get_provider.return_value = mock_provider
        
        client = UIR(api_key="test-key")
        results = await client.search(
            provider="google",
            query="test query",
            limit=10
        )
        
        assert results is not None
        assert len(results.results) > 0
        assert results.results[0].title == "Test Result"


@pytest.mark.asyncio
async def test_hybrid_search_integration():
    """Test hybrid search with multiple strategies"""
    with patch('uir.providers.manager.ProviderManager') as mock_manager:
        # Mock keyword provider
        mock_keyword_provider = Mock()
        mock_keyword_provider.search.return_value = [
            SearchResult(
                id="k1",
                title="Keyword Result",
                score=0.8,
                provider="elasticsearch"
            )
        ]
        
        # Mock vector provider
        mock_vector_provider = Mock()
        mock_vector_provider.vector_search.return_value = [
            SearchResult(
                id="v1",
                title="Vector Result",
                score=0.9,
                provider="pinecone"
            )
        ]
        
        def get_provider(name):
            if name == "elasticsearch":
                return mock_keyword_provider
            elif name == "pinecone":
                return mock_vector_provider
            return None
        
        mock_manager.return_value.get_provider.side_effect = get_provider
        
        client = UIR(api_key="test-key")
        results = await client.hybrid_search(
            strategies=[
                {"type": "keyword", "provider": "elasticsearch", "weight": 0.4},
                {"type": "vector", "provider": "pinecone", "weight": 0.6}
            ],
            fusion_method="weighted_sum"
        )
        
        assert results is not None
        assert len(results.results) > 0


@pytest.mark.asyncio
async def test_rag_retrieval():
    """Test RAG retrieval functionality"""
    with patch('uir.providers.manager.ProviderManager') as mock_manager:
        mock_provider = Mock()
        mock_provider.search.return_value = [
            SearchResult(
                id="1",
                title="Document 1",
                content="This is the content for RAG retrieval.",
                score=0.95,
                provider="pinecone"
            )
        ]
        mock_manager.return_value.get_provider.return_value = mock_provider
        
        client = UIR(api_key="test-key")
        context = await client.rag_retrieve(
            query="test query",
            providers=["pinecone"],
            num_chunks=5
        )
        
        assert context is not None
        assert len(context) > 0


@pytest.mark.asyncio
async def test_query_processing_pipeline():
    """Test complete query processing pipeline"""
    client = UIR(api_key="test-key")
    
    # Test query analysis
    with patch('uir.query_processor.QueryProcessor.process') as mock_process:
        mock_process.return_value = Mock(
            original="test query",
            corrected="test query",
            expanded="test query related terms",
            keywords=["test", "query"],
            entities=[],
            embedding=[0.1] * 768
        )
        
        analysis = await client.analyze_query("test query")
        assert analysis is not None
        assert analysis.corrected == "test query"


@pytest.mark.asyncio
async def test_caching_integration():
    """Test caching integration"""
    with patch('uir.cache.CacheManager') as mock_cache:
        mock_cache.return_value.get.return_value = None
        mock_cache.return_value.set.return_value = None
        
        client = UIR(api_key="test-key", enable_cache=True)
        
        # First request should miss cache
        with patch('uir.providers.manager.ProviderManager') as mock_manager:
            mock_provider = Mock()
            mock_provider.search.return_value = [
                SearchResult(id="1", title="Result", score=0.9, provider="google")
            ]
            mock_manager.return_value.get_provider.return_value = mock_provider
            
            results1 = await client.search("google", "test query")
            assert results1 is not None
            
            # Cache should have been set
            mock_cache.return_value.set.assert_called()


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in integration scenarios"""
    client = UIR(api_key="test-key")
    
    with patch('uir.providers.manager.ProviderManager') as mock_manager:
        mock_provider = Mock()
        mock_provider.search.side_effect = Exception("Provider error")
        mock_manager.return_value.get_provider.return_value = mock_provider
        
        with pytest.raises(Exception):
            await client.search("google", "test query")


@pytest.mark.asyncio
async def test_rate_limiting_integration():
    """Test rate limiting in integration"""
    client = UIR(
        api_key="test-key",
        rate_limits={"default": 10}
    )
    
    with patch('uir.core.rate_limiter.RateLimiter') as mock_limiter:
        mock_limiter.return_value.check_rate_limit.return_value = True
        
        # Should succeed
        results = await client.search("google", "test query")
        
        mock_limiter.return_value.check_rate_limit.return_value = False
        
        # Should be rate limited
        with pytest.raises(Exception):
            await client.search("google", "test query")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])