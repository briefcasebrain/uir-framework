"""Tests for result aggregation and fusion"""

import pytest
from unittest.mock import MagicMock

from src.uir.aggregator import ResultAggregator
from src.uir.models import SearchResult


class TestResultAggregator:
    """Test result aggregation functionality"""
    
    @pytest.fixture
    def aggregator(self):
        """Create result aggregator"""
        return ResultAggregator()
    
    @pytest.fixture
    def duplicate_results(self):
        """Create results with duplicates"""
        return [
            SearchResult(
                id="1",
                title="Machine Learning",
                url="https://example.com/ml",
                score=0.95,
                provider="google"
            ),
            SearchResult(
                id="2",
                title="Machine Learning",  # Same title, same URL
                url="https://example.com/ml",
                score=0.88,
                provider="bing"
            ),
            SearchResult(
                id="3",
                title="Deep Learning",
                url="https://example.com/dl",
                score=0.92,
                provider="google"
            ),
            SearchResult(
                id="4",
                title="Neural Networks",
                content="Introduction to neural networks",
                score=0.85,
                provider="elasticsearch"
            ),
            SearchResult(
                id="5",
                title="Neural Networks",  # Same title, different content
                content="Advanced neural network architectures",
                score=0.90,
                provider="elasticsearch"
            )
        ]
    
    def test_aggregate_basic(self, aggregator, sample_search_results):
        """Test basic aggregation"""
        results = aggregator.aggregate(sample_search_results)
        
        assert len(results) == len(sample_search_results)
        # Should be sorted by score descending
        assert results[0].score >= results[1].score
        assert results[1].score >= results[2].score
    
    def test_aggregate_with_deduplication(self, aggregator, duplicate_results):
        """Test aggregation with deduplication"""
        results = aggregator.aggregate(duplicate_results, deduplicate=True)
        
        # Should remove duplicate with same URL
        assert len(results) < len(duplicate_results)
        
        # Should keep higher scoring duplicate
        ml_results = [r for r in results if "Machine Learning" in r.title]
        assert len(ml_results) == 1
        assert ml_results[0].score == 0.95  # Higher score
        
        # Should keep both neural network results (different content)
        nn_results = [r for r in results if "Neural Networks" in r.title]
        assert len(nn_results) == 2
    
    def test_aggregate_without_deduplication(self, aggregator, duplicate_results):
        """Test aggregation without deduplication"""
        results = aggregator.aggregate(duplicate_results, deduplicate=False)
        
        assert len(results) == len(duplicate_results)
        # Should still be sorted by score
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score
    
    def test_reciprocal_rank_fusion(self, aggregator, sample_search_results):
        """Test reciprocal rank fusion"""
        # Create multiple result lists
        list1 = sample_search_results[:2]
        list2 = sample_search_results[1:3]  # Overlap with list1
        list3 = [sample_search_results[2]]
        
        result_lists = [list1, list2, list3]
        
        fused = aggregator.reciprocal_rank_fusion(result_lists, k=60)
        
        # Should combine all unique results
        assert len(fused) == 3
        
        # Result that appears in multiple lists should rank higher
        # sample_search_results[1] appears in list1 and list2
        assert fused[0].id == sample_search_results[1].id or fused[1].id == sample_search_results[1].id
        
        # Scores should be RRF scores
        assert all(0 < r.score <= 1 for r in fused)
    
    def test_weighted_sum_fusion(self, aggregator):
        """Test weighted sum fusion"""
        result1 = SearchResult(id="1", title="Result 1", score=0.8, provider="google")
        result2 = SearchResult(id="2", title="Result 2", score=0.7, provider="google")
        result3 = SearchResult(id="1", title="Result 1", score=0.6, provider="bing")  # Same as result1
        
        list1 = [result1, result2]
        list2 = [result3]
        
        fused = aggregator.weighted_sum_fusion([list1, list2])
        
        # Result 1 should have combined score (0.8 + 0.6 = 1.4)
        assert len(fused) == 2
        assert fused[0].id == "1"
        assert fused[0].score == 1.4
        assert fused[1].id == "2"
        assert fused[1].score == 0.7
    
    def test_max_score_fusion(self, aggregator):
        """Test max score fusion"""
        result1 = SearchResult(id="1", title="Result 1", score=0.8, provider="google")
        result2 = SearchResult(id="1", title="Result 1", score=0.9, provider="bing")  # Higher score
        result3 = SearchResult(id="2", title="Result 2", score=0.7, provider="google")
        
        list1 = [result1, result3]
        list2 = [result2]
        
        fused = aggregator.max_score_fusion([list1, list2])
        
        assert len(fused) == 2
        assert fused[0].id == "1"
        assert fused[0].score == 0.9  # Max score
        assert fused[0].provider == "bing"  # From higher scoring source
        assert fused[1].id == "2"
        assert fused[1].score == 0.7
    
    @pytest.mark.asyncio
    async def test_rerank(self, aggregator, sample_search_results):
        """Test result reranking"""
        # Modify results to have different relevance to query
        results = [
            SearchResult(
                id="1",
                title="Deep Learning",
                content="Introduction to deep learning",
                score=0.8,
                provider="google"
            ),
            SearchResult(
                id="2",
                title="Machine Learning Tutorial",
                content="Complete machine learning guide with examples",
                score=0.7,
                provider="google"
            ),
            SearchResult(
                id="3",
                title="AI Overview",
                content="Brief overview of artificial intelligence",
                score=0.9,
                provider="google"
            )
        ]
        
        query = "machine learning tutorial"
        reranked = await aggregator.rerank(results, query)
        
        # Result 2 should rank higher after reranking (matches query better)
        assert reranked[0].id == "2"
        assert reranked[0].score > 0.7  # Score should be boosted
    
    def test_diversify_results(self, aggregator):
        """Test result diversification"""
        # Create results with multiple from same domain
        results = [
            SearchResult(id="1", title="Result 1", url="https://example.com/1", score=0.95, provider="google"),
            SearchResult(id="2", title="Result 2", url="https://example.com/2", score=0.94, provider="google"),
            SearchResult(id="3", title="Result 3", url="https://example.com/3", score=0.93, provider="google"),
            SearchResult(id="4", title="Result 4", url="https://other.com/1", score=0.92, provider="google"),
            SearchResult(id="5", title="Result 5", url="https://example.com/4", score=0.91, provider="google"),
        ]
        
        diversified = aggregator.diversify_results(results, max_similar=2)
        
        # Should limit results from same domain
        example_com_count = sum(1 for r in diversified if "example.com" in r.url)
        assert example_com_count <= 2
        
        # Should keep top results
        assert diversified[0].id == "1"
        
        # Should include result from other domain
        assert any("other.com" in r.url for r in diversified)
    
    def test_get_content_hash(self, aggregator):
        """Test content hash generation"""
        # Results with same URL should have same hash
        result1 = SearchResult(id="1", title="Title 1", url="https://example.com/page", score=0.9, provider="google")
        result2 = SearchResult(id="2", title="Title 2", url="https://example.com/page", score=0.8, provider="bing")
        
        hash1 = aggregator._get_content_hash(result1)
        hash2 = aggregator._get_content_hash(result2)
        assert hash1 == hash2
        
        # Results without URL should use content
        result3 = SearchResult(id="3", title="Same Title", content="Same Content", score=0.9, provider="google")
        result4 = SearchResult(id="4", title="Same Title", content="Same Content", score=0.8, provider="bing")
        
        hash3 = aggregator._get_content_hash(result3)
        hash4 = aggregator._get_content_hash(result4)
        assert hash3 == hash4
        
        # Different content should have different hash
        result5 = SearchResult(id="5", title="Different", content="Different", score=0.9, provider="google")
        hash5 = aggregator._get_content_hash(result5)
        assert hash5 != hash3