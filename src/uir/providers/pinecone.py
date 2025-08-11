"""Pinecone vector database provider adapter"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog
import numpy as np

from ..models import SearchResult, ProviderHealth, ProviderConfig
from ..core.adapter import ProviderAdapter

logger = structlog.get_logger()


class PineconeAdapter(ProviderAdapter):
    """Adapter for Pinecone vector database"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.credentials.get("api_key")
        self.environment = config.credentials.get("environment", "us-west1-gcp")
        self.index_name = config.credentials.get("index_name", "default")
        self.base_url = f"https://{self.index_name}.svc.{self.environment}.pinecone.io"
    
    async def search(
        self,
        query: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Text search not directly supported - would need embedding"""
        raise NotImplementedError(
            "Pinecone requires vector embeddings. Use vector_search with a vector or text."
        )
    
    async def vector_search(
        self,
        vector: List[float],
        options: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Execute vector similarity search in Pinecone"""
        try:
            # Prepare request
            request_body = {
                "vector": vector,
                "topK": options.get("limit", 10) if options else 10,
                "includeValues": False,
                "includeMetadata": True
            }
            
            # Add namespace if provided
            if options and options.get("namespace"):
                request_body["namespace"] = options["namespace"]
            
            # Add metadata filter if provided
            if options and options.get("filter"):
                request_body["filter"] = self._transform_filter(options["filter"])
            
            # Make request to Pinecone
            response = await self._execute_request(
                method="POST",
                endpoint=f"{self.base_url}/query",
                headers={
                    "Api-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            # Transform response
            return self.transform_response(response)
            
        except Exception as e:
            self.logger.error(f"Pinecone vector search failed: {e}")
            raise
    
    async def index(
        self,
        documents: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Index documents into Pinecone"""
        try:
            # Prepare vectors for indexing
            vectors = []
            for doc in documents:
                vector_data = {
                    "id": doc.get("id", str(hash(doc.get("content", "")))),
                    "values": doc.get("vector", []),
                    "metadata": {
                        "title": doc.get("title", ""),
                        "content": doc.get("content", ""),
                        "url": doc.get("url", ""),
                        **doc.get("metadata", {})
                    }
                }
                vectors.append(vector_data)
            
            # Batch upsert vectors
            request_body = {
                "vectors": vectors
            }
            
            if options and options.get("namespace"):
                request_body["namespace"] = options["namespace"]
            
            response = await self._execute_request(
                method="POST",
                endpoint=f"{self.base_url}/vectors/upsert",
                headers={
                    "Api-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            return {
                "status": "success",
                "indexed": len(vectors),
                "response": response
            }
            
        except Exception as e:
            self.logger.error(f"Pinecone indexing failed: {e}")
            raise
    
    async def health_check(self) -> ProviderHealth:
        """Check Pinecone index health"""
        try:
            # Get index stats
            response = await self._execute_request(
                method="GET",
                endpoint=f"{self.base_url}/describe_index_stats",
                headers={
                    "Api-Key": self.api_key
                }
            )
            
            return ProviderHealth(
                provider="pinecone",
                status="healthy",
                last_check=datetime.now(),
                success_rate=1.0,
                metadata={
                    "total_vectors": response.get("totalVectorCount", 0),
                    "dimensions": response.get("dimension", 0)
                }
            )
        except Exception as e:
            return ProviderHealth(
                provider="pinecone",
                status="unhealthy",
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    def transform_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform UIR request to Pinecone format"""
        return {
            "vector": request.get("vector", []),
            "topK": request.get("limit", 10),
            "filter": self._transform_filter(request.get("filter")) if request.get("filter") else None,
            "namespace": request.get("namespace"),
            "includeMetadata": True
        }
    
    def transform_response(self, response: Dict[str, Any]) -> List[SearchResult]:
        """Transform Pinecone response to UIR format"""
        results = []
        
        matches = response.get("matches", [])
        
        for match in matches:
            metadata = match.get("metadata", {})
            
            result = SearchResult(
                id=match.get("id"),
                title=metadata.get("title"),
                content=metadata.get("content"),
                url=metadata.get("url"),
                snippet=metadata.get("snippet", metadata.get("content", "")[:200]),
                score=match.get("score", 0.0),
                provider="pinecone",
                metadata=metadata,
                vector=match.get("values") if match.get("values") else None
            )
            
            results.append(result)
        
        return results
    
    def _transform_filter(self, filter_dict: Dict) -> Dict:
        """Transform UIR filter format to Pinecone filter format"""
        # Pinecone uses MongoDB-style filters
        pinecone_filter = {}
        
        for key, value in filter_dict.items():
            if isinstance(value, dict):
                # Handle operators like $gte, $lte, $in
                pinecone_filter[key] = value
            elif isinstance(value, list):
                # Convert list to $in operator
                pinecone_filter[key] = {"$in": value}
            else:
                # Simple equality
                pinecone_filter[key] = {"$eq": value}
        
        return pinecone_filter