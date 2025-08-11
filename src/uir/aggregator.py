"""Result aggregation and fusion service"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
import hashlib
import structlog

from .models import SearchResult

logger = structlog.get_logger()


class ResultAggregator:
    """Aggregates and ranks search results from multiple providers"""
    
    def __init__(self):
        self.logger = logger.bind(component="aggregator")
    
    def aggregate(
        self,
        results: List[SearchResult],
        deduplicate: bool = True
    ) -> List[SearchResult]:
        """Aggregate results from multiple sources"""
        if not results:
            return []
        
        if deduplicate:
            results = self._deduplicate(results)
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content similarity"""
        seen = {}
        unique_results = []
        
        for result in results:
            # Generate hash for deduplication
            content_hash = self._get_content_hash(result)
            
            if content_hash not in seen:
                seen[content_hash] = result
                unique_results.append(result)
            else:
                # Keep the result with higher score
                if result.score > seen[content_hash].score:
                    # Replace with higher scoring result
                    idx = unique_results.index(seen[content_hash])
                    unique_results[idx] = result
                    seen[content_hash] = result
        
        return unique_results
    
    def _get_content_hash(self, result: SearchResult) -> str:
        """Generate hash for result deduplication"""
        # Use URL if available, otherwise use title and content
        if result.url:
            return hashlib.md5(result.url.encode()).hexdigest()
        
        content = f"{result.title or ''}{result.content or ''}{result.snippet or ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def reciprocal_rank_fusion(
        self,
        result_lists: List[List[SearchResult]],
        k: int = 60
    ) -> List[SearchResult]:
        """Reciprocal Rank Fusion for combining multiple ranked lists"""
        scores = defaultdict(float)
        result_map = {}
        
        for result_list in result_lists:
            for rank, result in enumerate(result_list, 1):
                result_id = self._get_content_hash(result)
                scores[result_id] += 1.0 / (k + rank)
                
                # Store the result object
                if result_id not in result_map:
                    result_map[result_id] = result
        
        # Create final ranked list
        final_results = []
        for result_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            result = result_map[result_id]
            result.score = score  # Update score with RRF score
            final_results.append(result)
        
        return final_results
    
    def weighted_sum_fusion(
        self,
        result_lists: List[List[SearchResult]]
    ) -> List[SearchResult]:
        """Weighted sum fusion for combining results"""
        scores = defaultdict(float)
        result_map = {}
        
        for result_list in result_lists:
            for result in result_list:
                result_id = self._get_content_hash(result)
                scores[result_id] += result.score
                
                # Store the result with highest individual score
                if result_id not in result_map or result.score > result_map[result_id].score:
                    result_map[result_id] = result
        
        # Create final ranked list
        final_results = []
        for result_id, total_score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            result = result_map[result_id]
            result.score = total_score
            final_results.append(result)
        
        return final_results
    
    def max_score_fusion(
        self,
        result_lists: List[List[SearchResult]]
    ) -> List[SearchResult]:
        """Max score fusion - take maximum score for each result"""
        best_scores = {}
        result_map = {}
        
        for result_list in result_lists:
            for result in result_list:
                result_id = self._get_content_hash(result)
                
                if result_id not in best_scores or result.score > best_scores[result_id]:
                    best_scores[result_id] = result.score
                    result_map[result_id] = result
        
        # Create final ranked list
        final_results = []
        for result_id, score in sorted(best_scores.items(), key=lambda x: x[1], reverse=True):
            result = result_map[result_id]
            result.score = score
            final_results.append(result)
        
        return final_results
    
    async def rerank(
        self,
        results: List[SearchResult],
        query: str,
        model: Optional[str] = None
    ) -> List[SearchResult]:
        """Rerank results using cross-encoder model"""
        # In production, this would use a real reranking model
        # For now, we'll do a simple relevance boost based on query terms
        
        query_terms = set(query.lower().split())
        
        for result in results:
            # Calculate relevance boost
            content = f"{result.title or ''} {result.content or ''} {result.snippet or ''}".lower()
            matching_terms = sum(1 for term in query_terms if term in content)
            
            # Apply boost to score
            relevance_boost = matching_terms / len(query_terms) if query_terms else 0
            result.score = result.score * (1 + relevance_boost * 0.5)
        
        # Re-sort by new scores
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def diversify_results(
        self,
        results: List[SearchResult],
        diversity_factor: float = 0.3,
        max_similar: int = 2
    ) -> List[SearchResult]:
        """Diversify results to reduce redundancy"""
        if not results:
            return []
        
        diversified = [results[0]]  # Always include top result
        similarity_counts = defaultdict(int)
        
        for result in results[1:]:
            # Check similarity with already selected results
            is_too_similar = False
            
            for selected in diversified:
                if self._are_similar(result, selected):
                    result_domain = self._get_domain(result)
                    similarity_counts[result_domain] += 1
                    
                    if similarity_counts[result_domain] >= max_similar:
                        is_too_similar = True
                        break
            
            if not is_too_similar:
                diversified.append(result)
        
        return diversified
    
    def _are_similar(self, result1: SearchResult, result2: SearchResult) -> bool:
        """Check if two results are similar"""
        # Simple domain-based similarity for URLs
        if result1.url and result2.url:
            return self._get_domain(result1) == self._get_domain(result2)
        
        # Title similarity
        if result1.title and result2.title:
            # Simple check - in production would use better similarity metrics
            return result1.title.lower()[:50] == result2.title.lower()[:50]
        
        return False
    
    def _get_domain(self, result: SearchResult) -> str:
        """Extract domain from URL"""
        if not result.url:
            return ""
        
        # Simple domain extraction
        from urllib.parse import urlparse
        parsed = urlparse(result.url)
        return parsed.netloc