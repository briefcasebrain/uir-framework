"""Mock external APIs for testing without real services"""

import asyncio
import hashlib
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np


class MockGoogleSearchAPI:
    """Mock Google Custom Search API"""
    
    def __init__(self, api_key: str = "test", cx: str = "test"):
        self.api_key = api_key
        self.cx = cx
        self.request_count = 0
    
    async def search(
        self,
        query: str,
        num: int = 10,
        start: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock Google search"""
        self.request_count += 1
        await asyncio.sleep(0.1)  # Simulate API latency
        
        # Generate deterministic results based on query
        query_hash = hashlib.md5(query.encode()).hexdigest()
        random.seed(int(query_hash[:8], 16))
        
        total_results = random.randint(1000, 1000000)
        
        items = []
        for i in range(min(num, 10)):
            rank = start + i
            items.append({
                "title": f"Result {rank} for '{query}'",
                "link": f"https://example.com/result-{rank}",
                "snippet": f"This is a sample snippet for result {rank} about {query}. It contains relevant information and context.",
                "displayLink": "example.com",
                "cacheId": f"cache_{query_hash}_{rank}",
                "mime": "text/html",
                "htmlSnippet": f"This is a sample snippet for result {rank} about <b>{query}</b>.",
                "pagemap": {
                    "metatags": [{"description": f"Page about {query}"}]
                }
            })
        
        return {
            "kind": "customsearch#search",
            "url": {"type": "application/json"},
            "queries": {
                "request": [{
                    "title": "Google Custom Search",
                    "totalResults": str(total_results),
                    "searchTerms": query,
                    "count": len(items),
                    "startIndex": start
                }]
            },
            "searchInformation": {
                "searchTime": 0.123456,
                "formattedSearchTime": "0.12",
                "totalResults": str(total_results),
                "formattedTotalResults": f"{total_results:,}"
            },
            "items": items
        }


class MockPineconeAPI:
    """Mock Pinecone vector database API"""
    
    def __init__(self, api_key: str = "test", environment: str = "test"):
        self.api_key = api_key
        self.environment = environment
        self.vectors = {}  # Store vectors by ID
        self.request_count = 0
    
    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        namespace: str = "",
        filter: Optional[Dict] = None,
        include_metadata: bool = True,
        include_values: bool = False
    ) -> Dict[str, Any]:
        """Mock Pinecone query"""
        self.request_count += 1
        await asyncio.sleep(0.05)  # Simulate API latency
        
        # Generate mock matches
        matches = []
        
        # Create some deterministic matches
        query_vector = np.array(vector)
        
        for i in range(min(top_k, 5)):
            # Generate a similar vector
            match_vector = query_vector + np.random.normal(0, 0.1, len(vector))
            match_vector = match_vector / np.linalg.norm(match_vector)  # Normalize
            
            # Calculate similarity
            similarity = float(np.dot(query_vector, match_vector))
            
            match = {
                "id": f"doc_{i+1}",
                "score": max(0.0, similarity),
                "metadata": {
                    "title": f"Document {i+1}",
                    "content": f"This is the content of document {i+1}",
                    "category": random.choice(["AI", "ML", "NLP", "CV"]),
                    "date": "2024-01-01"
                }
            }
            
            if include_values:
                match["values"] = match_vector.tolist()
            
            matches.append(match)
        
        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "matches": matches,
            "namespace": namespace
        }
    
    async def upsert(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """Mock Pinecone upsert"""
        self.request_count += 1
        await asyncio.sleep(0.02)  # Simulate API latency
        
        # Store vectors
        for vector in vectors:
            self.vectors[vector["id"]] = vector
        
        return {
            "upserted_count": len(vectors)
        }
    
    async def describe_index_stats(self) -> Dict[str, Any]:
        """Mock index stats"""
        await asyncio.sleep(0.01)
        
        return {
            "dimension": 768,
            "indexFullness": 0.1,
            "totalVectorCount": len(self.vectors),
            "namespaces": {
                "": {
                    "vectorCount": len(self.vectors)
                }
            }
        }


class MockElasticsearchAPI:
    """Mock Elasticsearch API"""
    
    def __init__(self, host: str = "localhost", port: int = 9200):
        self.host = host
        self.port = port
        self.documents = {}  # Store documents by index and ID
        self.request_count = 0
    
    async def search(
        self,
        index: str,
        body: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Mock Elasticsearch search"""
        self.request_count += 1
        await asyncio.sleep(0.08)  # Simulate API latency
        
        # Extract query parameters
        query = body.get("query", {})
        size = body.get("size", 10)
        from_param = body.get("from", 0)
        
        # Generate mock hits
        hits = []
        
        # Generate deterministic results
        if "multi_match" in query:
            query_text = query["multi_match"]["query"]
            query_hash = hashlib.md5(query_text.encode()).hexdigest()
            random.seed(int(query_hash[:8], 16))
            
            for i in range(min(size, 8)):
                doc_id = f"doc_{from_param + i + 1}"
                score = random.uniform(0.5, 1.0)
                
                hit = {
                    "_index": index,
                    "_type": "_doc",
                    "_id": doc_id,
                    "_score": score,
                    "_source": {
                        "title": f"Elasticsearch Result {i+1} for '{query_text}'",
                        "content": f"This is the content of document {i+1} related to {query_text}. It contains detailed information and analysis.",
                        "url": f"https://example.com/es-doc-{doc_id}",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "category": random.choice(["technology", "research", "tutorial"])
                    }
                }
                
                # Add highlights if requested
                if "highlight" in body:
                    hit["highlight"] = {
                        "content": [f"This document is about <em>{query_text}</em>"],
                        "title": [f"Result about <em>{query_text}</em>"]
                    }
                
                hits.append(hit)
        
        # Sort by score descending
        hits.sort(key=lambda x: x["_score"], reverse=True)
        
        max_score = hits[0]["_score"] if hits else 0
        
        return {
            "took": random.randint(5, 50),
            "timed_out": False,
            "hits": {
                "total": {
                    "value": random.randint(100, 10000),
                    "relation": "eq"
                },
                "max_score": max_score,
                "hits": hits
            }
        }
    
    async def index(
        self,
        index: str,
        doc_type: str,
        id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock document indexing"""
        self.request_count += 1
        await asyncio.sleep(0.02)
        
        # Store document
        if index not in self.documents:
            self.documents[index] = {}
        self.documents[index][id] = body
        
        return {
            "_index": index,
            "_type": doc_type,
            "_id": id,
            "_version": 1,
            "result": "created"
        }
    
    async def bulk(self, body: str, **kwargs) -> Dict[str, Any]:
        """Mock bulk operations"""
        self.request_count += 1
        await asyncio.sleep(0.05)
        
        # Parse NDJSON
        lines = body.strip().split('\n')
        operations = len(lines) // 2
        
        items = []
        for i in range(operations):
            items.append({
                "index": {
                    "_index": "test",
                    "_type": "_doc",
                    "_id": f"doc_{i}",
                    "_version": 1,
                    "result": "created",
                    "status": 201
                }
            })
        
        return {
            "took": random.randint(10, 100),
            "errors": False,
            "items": items
        }
    
    async def cluster_health(self) -> Dict[str, Any]:
        """Mock cluster health"""
        await asyncio.sleep(0.01)
        
        return {
            "cluster_name": "mock-cluster",
            "status": "green",
            "timed_out": False,
            "number_of_nodes": 3,
            "number_of_data_nodes": 3,
            "active_primary_shards": 10,
            "active_shards": 20,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 0
        }


class MockRedisAPI:
    """Mock Redis API"""
    
    def __init__(self):
        self.data = {}
        self.expires = {}
        self.stats = {"hits": 0, "misses": 0}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        await asyncio.sleep(0.001)  # Simulate network latency
        
        if key in self.data:
            self.stats["hits"] += 1
            return self.data[key]
        else:
            self.stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set key-value pair"""
        await asyncio.sleep(0.001)
        
        self.data[key] = value
        if ex:
            self.expires[key] = datetime.now().timestamp() + ex
        
        return True
    
    async def setex(self, key: str, time: int, value: str) -> bool:
        """Set with expiration"""
        return await self.set(key, value, time)
    
    async def delete(self, *keys: str) -> int:
        """Delete keys"""
        await asyncio.sleep(0.001)
        
        deleted = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                self.expires.pop(key, None)
                deleted += 1
        
        return deleted
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        await asyncio.sleep(0.002)
        
        # Simple pattern matching (just contains for now)
        pattern = pattern.replace("*", "")
        return [k for k in self.data.keys() if pattern in k]
    
    async def flushdb(self) -> bool:
        """Clear database"""
        await asyncio.sleep(0.001)
        self.data.clear()
        self.expires.clear()
        return True
    
    async def info(self, section: str = "all") -> Dict[str, Any]:
        """Get Redis info"""
        await asyncio.sleep(0.001)
        
        if section == "stats":
            return {
                "keyspace_hits": self.stats["hits"],
                "keyspace_misses": self.stats["misses"]
            }
        
        return {
            "redis_version": "7.0.0-mock",
            "used_memory": len(str(self.data)),
            "connected_clients": 1
        }
    
    async def ping(self) -> bool:
        """Ping Redis"""
        return True