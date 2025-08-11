"""Elasticsearch provider adapter"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

from ..models import SearchResult, ProviderHealth, ProviderConfig
from ..core.adapter import ProviderAdapter

logger = structlog.get_logger()


class ElasticsearchAdapter(ProviderAdapter):
    """Adapter for Elasticsearch"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.host = config.credentials.get("host", "localhost")
        self.port = config.credentials.get("port", 9200)
        self.username = config.credentials.get("username")
        self.password = config.credentials.get("password")
        self.index_name = config.credentials.get("index", "_all")
        
        # Build base URL
        protocol = "https" if config.credentials.get("use_ssl", True) else "http"
        self.base_url = f"{protocol}://{self.host}:{self.port}"
        
        # Set auth header if credentials provided
        self.auth_headers = {}
        if self.username and self.password:
            import base64
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            self.auth_headers["Authorization"] = f"Basic {credentials}"
    
    async def search(
        self,
        query: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Execute Elasticsearch text search"""
        try:
            # Build Elasticsearch query
            es_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content", "description"],
                        "type": "best_fields"
                    }
                },
                "size": options.get("limit", 10) if options else 10,
                "from": options.get("offset", 0) if options else 0
            }
            
            # Add filters if provided
            if options and options.get("filters"):
                es_query["query"] = {
                    "bool": {
                        "must": es_query["query"],
                        "filter": self._build_filters(options["filters"])
                    }
                }
            
            # Add highlighting
            es_query["highlight"] = {
                "fields": {
                    "content": {"fragment_size": 150},
                    "title": {}
                }
            }
            
            # Make request
            response = await self._execute_request(
                method="POST",
                endpoint=f"{self.base_url}/{self.index_name}/_search",
                headers={
                    **self.auth_headers,
                    "Content-Type": "application/json"
                },
                json=es_query
            )
            
            return self.transform_response(response)
            
        except Exception as e:
            self.logger.error(f"Elasticsearch search failed: {e}")
            raise
    
    async def vector_search(
        self,
        vector: List[float],
        options: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Execute vector similarity search in Elasticsearch"""
        try:
            # Build kNN search query
            es_query = {
                "knn": {
                    "field": options.get("vector_field", "embedding") if options else "embedding",
                    "query_vector": vector,
                    "k": options.get("limit", 10) if options else 10,
                    "num_candidates": options.get("num_candidates", 100) if options else 100
                }
            }
            
            # Add filters if provided
            if options and options.get("filter"):
                es_query["filter"] = self._build_filters(options["filter"])
            
            # Make request
            response = await self._execute_request(
                method="POST",
                endpoint=f"{self.base_url}/{self.index_name}/_knn_search",
                headers={
                    **self.auth_headers,
                    "Content-Type": "application/json"
                },
                json=es_query
            )
            
            return self.transform_response(response)
            
        except Exception as e:
            self.logger.error(f"Elasticsearch vector search failed: {e}")
            raise
    
    async def index(
        self,
        documents: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Index documents into Elasticsearch"""
        try:
            # Prepare bulk indexing request
            bulk_body = []
            
            for doc in documents:
                # Add index action
                bulk_body.append({
                    "index": {
                        "_index": options.get("index_name", self.index_name) if options else self.index_name,
                        "_id": doc.get("id")
                    }
                })
                
                # Add document
                bulk_body.append({
                    "title": doc.get("title"),
                    "content": doc.get("content"),
                    "url": doc.get("url"),
                    "embedding": doc.get("vector"),
                    "metadata": doc.get("metadata", {}),
                    "timestamp": datetime.now().isoformat()
                })
            
            # Convert to NDJSON format
            ndjson = "\n".join([
                self._json_to_str(item) for item in bulk_body
            ]) + "\n"
            
            # Make bulk request
            response = await self._execute_request(
                method="POST",
                endpoint=f"{self.base_url}/_bulk",
                headers={
                    **self.auth_headers,
                    "Content-Type": "application/x-ndjson"
                },
                content=ndjson
            )
            
            return {
                "status": "success",
                "indexed": len(documents),
                "errors": response.get("errors", False),
                "items": response.get("items", [])
            }
            
        except Exception as e:
            self.logger.error(f"Elasticsearch indexing failed: {e}")
            raise
    
    async def health_check(self) -> ProviderHealth:
        """Check Elasticsearch cluster health"""
        try:
            response = await self._execute_request(
                method="GET",
                endpoint=f"{self.base_url}/_cluster/health",
                headers=self.auth_headers
            )
            
            status_map = {
                "green": "healthy",
                "yellow": "degraded",
                "red": "unhealthy"
            }
            
            return ProviderHealth(
                provider="elasticsearch",
                status=status_map.get(response.get("status"), "unhealthy"),
                last_check=datetime.now(),
                metadata={
                    "cluster_name": response.get("cluster_name"),
                    "number_of_nodes": response.get("number_of_nodes"),
                    "active_shards": response.get("active_shards"),
                    "unassigned_shards": response.get("unassigned_shards")
                }
            )
        except Exception as e:
            return ProviderHealth(
                provider="elasticsearch",
                status="unhealthy",
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    def transform_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform UIR request to Elasticsearch format"""
        es_query = {
            "size": request.get("limit", 10),
            "from": request.get("offset", 0)
        }
        
        if request.get("query"):
            es_query["query"] = {
                "multi_match": {
                    "query": request["query"],
                    "fields": ["title^2", "content", "description"]
                }
            }
        elif request.get("vector"):
            es_query["knn"] = {
                "field": "embedding",
                "query_vector": request["vector"],
                "k": request.get("limit", 10)
            }
        
        return es_query
    
    def transform_response(self, response: Dict[str, Any]) -> List[SearchResult]:
        """Transform Elasticsearch response to UIR format"""
        results = []
        
        hits = response.get("hits", {}).get("hits", [])
        max_score = response.get("hits", {}).get("max_score", 1.0) or 1.0
        
        for hit in hits:
            source = hit.get("_source", {})
            
            # Extract highlights
            highlights = []
            if hit.get("highlight"):
                for field, values in hit["highlight"].items():
                    highlights.extend(values)
            
            result = SearchResult(
                id=hit.get("_id"),
                title=source.get("title"),
                content=source.get("content"),
                url=source.get("url"),
                snippet=source.get("content", "")[:200] if source.get("content") else None,
                score=self.normalize_score(hit.get("_score", 0), 0, max_score),
                provider="elasticsearch",
                metadata={
                    **source.get("metadata", {}),
                    "_index": hit.get("_index"),
                    "_type": hit.get("_type")
                },
                highlights=highlights if highlights else None
            )
            
            results.append(result)
        
        return results
    
    def _build_filters(self, filters: Dict) -> List[Dict]:
        """Build Elasticsearch filter clauses"""
        filter_clauses = []
        
        for field, value in filters.items():
            if isinstance(value, dict):
                # Handle range queries
                if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                    filter_clauses.append({"range": {field: value}})
                elif "in" in value:
                    filter_clauses.append({"terms": {field: value["in"]}})
            elif isinstance(value, list):
                filter_clauses.append({"terms": {field: value}})
            else:
                filter_clauses.append({"term": {field: value}})
        
        return filter_clauses
    
    def _json_to_str(self, obj: Dict) -> str:
        """Convert dict to JSON string"""
        import json
        return json.dumps(obj, ensure_ascii=False)