"""Performance benchmarks for UIR Framework"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

from src.uir.router import RouterService
from src.uir.query_processor import QueryProcessor
from src.uir.aggregator import ResultAggregator
from src.uir.cache import CacheManager
from src.uir.models import SearchRequest, SearchResult


@pytest.fixture
def benchmark_data():
    """Create test data for benchmarks"""
    return {
        "query": "machine learning algorithms for natural language processing",
        "results": [
            SearchResult(
                id=f"result_{i}",
                title=f"Test Result {i}",
                content=f"Content for result {i}" * 10,
                score=0.9 - (i * 0.1),
                provider="test"
            ) for i in range(100)
        ]
    }


class TestQueryProcessingBenchmarks:
    """Benchmark query processing performance"""
    
    def test_spell_correction_performance(self, benchmark, benchmark_data):
        """Benchmark spell correction performance"""
        from src.uir.mocks.spell_checker import MockSpellChecker
        
        spell_checker = MockSpellChecker()
        query = "machien lerning algorthms for natual languag procesing"
        
        def spell_check():
            return spell_checker.correct(query)
        
        result = benchmark(spell_check)
        assert result != query  # Should be corrected

    def test_entity_extraction_performance(self, benchmark, benchmark_data):
        """Benchmark entity extraction performance"""
        from src.uir.mocks.entity_extractor import MockEntityExtractor
        
        extractor = MockEntityExtractor()
        
        def extract_entities():
            return extractor.extract(benchmark_data["query"])
        
        result = benchmark(extract_entities)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_query_processing_pipeline(self, benchmark, benchmark_data):
        """Benchmark full query processing pipeline"""
        processor = QueryProcessor()
        
        async def process_query():
            return await processor.process(benchmark_data["query"])
        
        # Use pytest-asyncio benchmark
        result = await benchmark.pedantic(process_query, iterations=100, rounds=5)
        assert result.corrected is not None


class TestSearchBenchmarks:
    """Benchmark search operations"""
    
    @pytest.mark.asyncio
    async def test_single_provider_search(self, benchmark, benchmark_data):
        """Benchmark single provider search"""
        router = RouterService(
            provider_manager=MagicMock(),
            query_processor=AsyncMock(),
            aggregator=MagicMock(),
            cache_manager=AsyncMock()
        )
        
        # Mock the dependencies
        router.query_processor.process.return_value = MagicMock(
            corrected=benchmark_data["query"],
            filters=None
        )
        router.provider_manager.get_available_providers.return_value = ["test"]
        router.provider_manager.get_adapter.return_value.search.return_value = benchmark_data["results"][:10]
        router.aggregator.aggregate.return_value = benchmark_data["results"][:10]
        router.cache_manager.get.return_value = None
        
        request = SearchRequest(
            provider="test",
            query=benchmark_data["query"]
        )
        
        async def search():
            return await router.search(request)
        
        result = await benchmark.pedantic(search, iterations=50, rounds=3)
        assert result.status == "success"

    def test_result_aggregation_performance(self, benchmark, benchmark_data):
        """Benchmark result aggregation"""
        aggregator = ResultAggregator()
        results = benchmark_data["results"]
        
        def aggregate():
            return aggregator.aggregate(results, deduplicate=True)
        
        aggregated = benchmark(aggregate)
        assert len(aggregated) <= len(results)

    def test_reciprocal_rank_fusion(self, benchmark, benchmark_data):
        """Benchmark reciprocal rank fusion"""
        aggregator = ResultAggregator()
        
        # Create multiple result lists
        result_lists = [
            benchmark_data["results"][:20],
            benchmark_data["results"][10:30],
            benchmark_data["results"][5:25]
        ]
        
        def rrf():
            return aggregator.reciprocal_rank_fusion(result_lists)
        
        fused = benchmark(rrf)
        assert len(fused) > 0


class TestCacheBenchmarks:
    """Benchmark caching operations"""
    
    @pytest.mark.asyncio
    async def test_cache_get_performance(self, benchmark, benchmark_data):
        """Benchmark cache get operations"""
        cache = CacheManager(redis_url=None)  # Use local cache only
        
        # Pre-populate cache
        request = SearchRequest(provider="test", query=benchmark_data["query"])
        cache.local_cache["test_key"] = {
            "data": "test_data",
            "expires_at": time.time() + 3600
        }
        
        async def cache_get():
            return await cache.get(request)
        
        await benchmark.pedantic(cache_get, iterations=1000, rounds=5)

    def test_cache_key_generation(self, benchmark, benchmark_data):
        """Benchmark cache key generation"""
        cache = CacheManager(redis_url=None)
        request = SearchRequest(provider="test", query=benchmark_data["query"])
        
        def generate_key():
            return cache._generate_cache_key(request)
        
        key = benchmark(generate_key)
        assert key is not None


class TestMemoryBenchmarks:
    """Benchmark memory usage"""
    
    def test_large_result_set_memory(self, benchmark, benchmark_data):
        """Test memory efficiency with large result sets"""
        # Create a very large result set
        large_results = [
            SearchResult(
                id=f"result_{i}",
                title=f"Large Result {i}",
                content="Very long content " * 100,
                score=0.9 - (i * 0.001),
                provider="test"
            ) for i in range(10000)
        ]
        
        aggregator = ResultAggregator()
        
        def process_large_results():
            return aggregator.aggregate(large_results, deduplicate=True)
        
        result = benchmark(process_large_results)
        assert len(result) <= len(large_results)

    def test_concurrent_processing(self, benchmark):
        """Test memory usage under concurrent load"""
        async def concurrent_task():
            processor = QueryProcessor()
            tasks = []
            for i in range(100):
                task = processor.process(f"query number {i}")
                tasks.append(task)
            return await asyncio.gather(*tasks)
        
        def run_concurrent():
            return asyncio.run(concurrent_task())
        
        results = benchmark(run_concurrent)
        assert len(results) == 100


class TestThroughputBenchmarks:
    """Benchmark system throughput"""
    
    @pytest.mark.asyncio
    async def test_concurrent_search_throughput(self, benchmark, benchmark_data):
        """Benchmark concurrent search throughput"""
        router = RouterService(
            provider_manager=MagicMock(),
            query_processor=AsyncMock(),
            aggregator=MagicMock(),
            cache_manager=AsyncMock()
        )
        
        # Mock fast responses
        router.query_processor.process.return_value = MagicMock(corrected="test", filters=None)
        router.provider_manager.get_available_providers.return_value = ["test"]
        router.provider_manager.get_adapter.return_value.search.return_value = benchmark_data["results"][:5]
        router.aggregator.aggregate.return_value = benchmark_data["results"][:5]
        router.cache_manager.get.return_value = None
        
        async def throughput_test():
            tasks = []
            for i in range(50):  # 50 concurrent requests
                request = SearchRequest(
                    provider="test",
                    query=f"concurrent query {i}"
                )
                tasks.append(router.search(request))
            
            return await asyncio.gather(*tasks)
        
        results = await benchmark.pedantic(throughput_test, iterations=1, rounds=3)
        assert len(results) == 50
        assert all(r.status == "success" for r in results)