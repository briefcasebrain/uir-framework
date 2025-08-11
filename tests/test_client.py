"""Tests for UIR Python SDK client"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
import json

from src.uir.client import UIR, UIRConfig
from src.uir.models import SearchResponse, SearchResult, ResponseMetadata


class TestUIRClient:
    """Test UIR client SDK"""
    
    @pytest.fixture
    def mock_response(self):
        """Create mock search response"""
        return {
            "status": "success",
            "request_id": "test-123",
            "results": [
                {
                    "id": "1",
                    "title": "Test Result",
                    "content": "Test content",
                    "url": "https://example.com",
                    "score": 0.95,
                    "provider": "google"
                }
            ],
            "metadata": {
                "query_time_ms": 150,
                "providers_used": ["google"],
                "cache_hit": False
            }
        }
    
    @pytest.fixture
    def client(self):
        """Create UIR client"""
        return UIR(
            api_key="test-key",
            base_url="http://localhost:8000"
        )
    
    def test_client_initialization(self):
        """Test client initialization"""
        client = UIR(api_key="test-key")
        assert client.config.api_key == "test-key"
        assert client.config.base_url == "http://localhost:8000"
        
        # Test with config object
        config = UIRConfig(
            api_key="config-key",
            base_url="http://custom:8080",
            timeout=60
        )
        client = UIR(config=config)
        assert client.config.api_key == "config-key"
        assert client.config.base_url == "http://custom:8080"
        assert client.config.timeout == 60
    
    def test_client_headers(self):
        """Test client headers"""
        client = UIR(api_key="test-key")
        headers = client._get_headers()
        
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert "User-Agent" in headers
    
    @patch.object(httpx.Client, 'post')
    def test_search(self, mock_post, client, mock_response):
        """Test search method"""
        mock_post.return_value = MagicMock(
            json=lambda: mock_response,
            raise_for_status=lambda: None
        )
        
        response = client.search(
            provider="google",
            query="test query",
            limit=10,
            filters={"category": "tech"}
        )
        
        assert isinstance(response, SearchResponse)
        assert response.status == "success"
        assert len(response.results) == 1
        assert response.results[0].title == "Test Result"
        
        # Check request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/search"
        
        request_data = call_args[1]["json"]
        assert request_data["provider"] == "google"
        assert request_data["query"] == "test query"
        assert request_data["options"]["limit"] == 10
        assert request_data["options"]["filters"] == {"category": "tech"}
    
    @patch.object(httpx.AsyncClient, 'post')
    @pytest.mark.asyncio
    async def test_search_async(self, mock_post, client, mock_response):
        """Test async search method"""
        mock_post.return_value = AsyncMock(
            json=lambda: mock_response,
            raise_for_status=lambda: None
        )
        
        response = await client.search_async(
            provider="google",
            query="async test"
        )
        
        assert isinstance(response, SearchResponse)
        assert response.status == "success"
    
    @patch.object(httpx.Client, 'post')
    def test_vector_search(self, mock_post, client, mock_response):
        """Test vector search method"""
        mock_post.return_value = MagicMock(
            json=lambda: mock_response,
            raise_for_status=lambda: None
        )
        
        response = client.vector_search(
            provider="pinecone",
            text="semantic search",
            index="documents",
            top_k=5
        )
        
        assert isinstance(response, SearchResponse)
        
        # Check request
        call_args = mock_post.call_args
        assert call_args[0][0] == "/vector/search"
        
        request_data = call_args[1]["json"]
        assert request_data["provider"] == "pinecone"
        assert request_data["text"] == "semantic search"
        assert request_data["index"] == "documents"
        assert request_data["options"]["limit"] == 5
    
    @patch.object(httpx.Client, 'post')
    def test_hybrid_search(self, mock_post, client, mock_response):
        """Test hybrid search method"""
        mock_post.return_value = MagicMock(
            json=lambda: mock_response,
            raise_for_status=lambda: None
        )
        
        response = client.hybrid_search(
            strategies=[
                {
                    "type": "keyword",
                    "provider": "google",
                    "weight": 0.5,
                    "query": "test"
                },
                {
                    "type": "vector",
                    "provider": "pinecone",
                    "weight": 0.5,
                    "text": "semantic test"
                }
            ],
            fusion_method="reciprocal_rank",
            limit=20
        )
        
        assert isinstance(response, SearchResponse)
        
        # Check request
        call_args = mock_post.call_args
        assert call_args[0][0] == "/hybrid/search"
        
        request_data = call_args[1]["json"]
        assert len(request_data["strategies"]) == 2
        assert request_data["fusion_method"] == "reciprocal_rank"
    
    @patch.object(httpx.Client, 'post')
    def test_rag_retrieve(self, mock_post, client):
        """Test RAG retrieval method"""
        mock_rag_response = {
            "status": "success",
            "context": "Context text",
            "chunks": [
                {"text": "Chunk 1", "source": "doc1", "score": 0.9}
            ]
        }
        
        mock_post.return_value = MagicMock(
            json=lambda: mock_rag_response,
            raise_for_status=lambda: None
        )
        
        response = client.rag_retrieve(
            query="explain transformers",
            providers=["pinecone", "elasticsearch"],
            num_chunks=5
        )
        
        assert response["status"] == "success"
        assert response["context"] == "Context text"
        assert len(response["chunks"]) == 1
        
        # Check request
        call_args = mock_post.call_args
        assert call_args[0][0] == "/rag/retrieve"
        
        request_data = call_args[1]["json"]
        assert request_data["query"] == "explain transformers"
        assert request_data["providers"] == ["pinecone", "elasticsearch"]
        assert request_data["options"]["num_chunks"] == 5
    
    @patch.object(httpx.Client, 'post')
    def test_analyze_query(self, mock_post, client):
        """Test query analysis method"""
        mock_analysis = {
            "original_query": "test",
            "corrected_query": "test",
            "expanded_query": "test expanded",
            "entities": [],
            "intent": {"type": "general"}
        }
        
        mock_post.return_value = MagicMock(
            json=lambda: mock_analysis,
            raise_for_status=lambda: None
        )
        
        response = client.analyze_query("test")
        
        assert response.original_query == "test"
        assert response.expanded_query == "test expanded"
    
    @patch.object(httpx.Client, 'post')
    def test_index_documents(self, mock_post, client):
        """Test document indexing method"""
        mock_index_response = {
            "status": "success",
            "indexed": 2
        }
        
        mock_post.return_value = MagicMock(
            json=lambda: mock_index_response,
            raise_for_status=lambda: None
        )
        
        documents = [
            {"id": "1", "title": "Doc 1", "content": "Content 1"},
            {"id": "2", "title": "Doc 2", "content": "Content 2"}
        ]
        
        response = client.index_documents(
            provider="elasticsearch",
            documents=documents,
            index_name="test-index"
        )
        
        assert response["status"] == "success"
        assert response["indexed"] == 2
        
        # Check request
        call_args = mock_post.call_args
        assert call_args[0][0] == "/documents/index"
        
        request_data = call_args[1]["json"]
        assert request_data["provider"] == "elasticsearch"
        assert len(request_data["documents"]) == 2
        assert request_data["index_name"] == "test-index"
    
    @patch.object(httpx.Client, 'post')
    def test_batch_search(self, mock_post, client):
        """Test batch search method"""
        mock_batch_response = {
            "results": [
                {
                    "status": "success",
                    "request_id": "batch-1",
                    "results": [],
                    "metadata": {
                        "query_time_ms": 100,
                        "providers_used": ["google"],
                        "cache_hit": False
                    }
                },
                {
                    "status": "success",
                    "request_id": "batch-2",
                    "results": [],
                    "metadata": {
                        "query_time_ms": 150,
                        "providers_used": ["bing"],
                        "cache_hit": False
                    }
                }
            ]
        }
        
        mock_post.return_value = MagicMock(
            json=lambda: mock_batch_response,
            raise_for_status=lambda: None
        )
        
        queries = [
            {"provider": "google", "query": "query 1"},
            {"provider": "bing", "query": "query 2"}
        ]
        
        responses = client.batch_search(queries)
        
        assert len(responses) == 2
        assert all(isinstance(r, SearchResponse) for r in responses)
        assert responses[0].metadata.providers_used == ["google"]
        assert responses[1].metadata.providers_used == ["bing"]
    
    @patch.object(httpx.Client, 'get')
    def test_get_providers(self, mock_get, client):
        """Test get providers method"""
        mock_providers = {
            "providers": [
                {"name": "google", "status": "active"},
                {"name": "pinecone", "status": "active"}
            ]
        }
        
        mock_get.return_value = MagicMock(
            json=lambda: mock_providers,
            raise_for_status=lambda: None
        )
        
        response = client.get_providers()
        
        assert "providers" in response
        assert len(response["providers"]) == 2
    
    @patch.object(httpx.Client, 'get')
    def test_get_usage(self, mock_get, client):
        """Test get usage method"""
        mock_usage = {
            "period": "2024-01",
            "total_requests": 1000,
            "by_provider": {"google": 500, "pinecone": 500}
        }
        
        mock_get.return_value = MagicMock(
            json=lambda: mock_usage,
            raise_for_status=lambda: None
        )
        
        response = client.get_usage("2024-01")
        
        assert response["period"] == "2024-01"
        assert response["total_requests"] == 1000
        
        # Check request
        call_args = mock_get.call_args
        assert call_args[1]["params"] == {"period": "2024-01"}
    
    @patch.object(httpx.Client, 'get')
    def test_health_check(self, mock_get, client):
        """Test health check method"""
        mock_health = {
            "status": "healthy",
            "providers": {"healthy": 5, "unhealthy": 0}
        }
        
        mock_get.return_value = MagicMock(
            json=lambda: mock_health,
            raise_for_status=lambda: None
        )
        
        response = client.health_check()
        
        assert response["status"] == "healthy"
        assert response["providers"]["healthy"] == 5
    
    def test_context_manager(self):
        """Test client as context manager"""
        with UIR(api_key="test-key") as client:
            assert client.config.api_key == "test-key"
            assert client.client is not None
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test client as async context manager"""
        async with UIR(api_key="test-key") as client:
            assert client.config.api_key == "test-key"
            assert client.async_client is not None
    
    @patch.object(httpx.Client, 'stream')
    def test_search_stream(self, mock_stream, client):
        """Test streaming search results"""
        # Mock streaming response
        mock_line1 = json.dumps({"id": "1", "title": "Result 1", "score": 0.9, "provider": "google"})
        mock_line2 = json.dumps({"id": "2", "title": "Result 2", "score": 0.8, "provider": "google"})
        
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [mock_line1, mock_line2]
        mock_response.json.side_effect = [
            json.loads(mock_line1),
            json.loads(mock_line2)
        ]
        
        mock_stream.return_value.__enter__.return_value = mock_response
        
        results = list(client.search_stream(
            provider="google",
            query="streaming test"
        ))
        
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)