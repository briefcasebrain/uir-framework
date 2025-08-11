"""Google Custom Search provider adapter"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

from ..models import SearchResult, ProviderHealth, ProviderConfig
from ..core.adapter import ProviderAdapter
from ..mocks.external_apis import MockGoogleSearchAPI

logger = structlog.get_logger()


class GoogleAdapter(ProviderAdapter):
    """Adapter for Google Custom Search API"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.credentials.get("api_key")
        self.cx = config.credentials.get("cx")  # Custom search engine ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        # Use mock API for testing
        self.mock_api = MockGoogleSearchAPI(self.api_key, self.cx)
    
    async def search(
        self,
        query: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Execute Google search"""
        try:
            params = {
                "key": self.api_key,
                "cx": self.cx,
                "q": query,
                "num": options.get("limit", 10) if options else 10,
                "start": options.get("offset", 0) + 1 if options else 1
            }
            
            # Add filters if provided
            if options:
                if options.get("date_range"):
                    # Google uses date restrict parameter
                    params["dateRestrict"] = self._format_date_range(options["date_range"])
                
                if options.get("file_type"):
                    params["fileType"] = ",".join(options["file_type"])
                
                if options.get("site"):
                    params["siteSearch"] = options["site"]
            
            # Use mock API instead of real request
            # In production, use: response = await self._execute_request(...)
            response = await self.mock_api.search(
                query=query,
                num=params.get("num", 10),
                start=params.get("start", 1),
                **{k: v for k, v in params.items() if k not in ["key", "cx", "q", "num", "start"]}
            )
            
            # Transform response
            return self.transform_response(response)
            
        except Exception as e:
            self.logger.error(f"Google search failed: {e}")
            raise
    
    async def vector_search(
        self,
        vector: List[float],
        options: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Google doesn't support vector search directly"""
        raise NotImplementedError("Google Custom Search doesn't support vector search")
    
    async def index(
        self,
        documents: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Google doesn't support indexing"""
        raise NotImplementedError("Google Custom Search doesn't support document indexing")
    
    async def health_check(self) -> ProviderHealth:
        """Check Google API health"""
        try:
            # Use mock API for health check
            await self.mock_api.search("test", num=1)
            
            return ProviderHealth(
                provider="google",
                status="healthy",
                last_check=datetime.now(),
                success_rate=1.0
            )
        except Exception as e:
            return ProviderHealth(
                provider="google",
                status="unhealthy",
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    def transform_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform UIR request to Google format"""
        return {
            "q": request.get("query"),
            "num": request.get("limit", 10),
            "start": request.get("offset", 0) + 1
        }
    
    def transform_response(self, response: Dict[str, Any]) -> List[SearchResult]:
        """Transform Google response to UIR format"""
        results = []
        
        items = response.get("items", [])
        total_results = int(response.get("searchInformation", {}).get("totalResults", 0))
        
        for i, item in enumerate(items):
            result = SearchResult(
                id=f"google_{item.get('cacheId', str(i))}",
                title=item.get("title"),
                url=item.get("link"),
                snippet=item.get("snippet"),
                score=self.normalize_score(
                    len(items) - i,  # Use position as score
                    0,
                    len(items)
                ),
                provider="google",
                metadata={
                    "display_link": item.get("displayLink"),
                    "mime": item.get("mime"),
                    "file_format": item.get("fileFormat"),
                    "page_map": item.get("pagemap", {})
                }
            )
            
            # Extract highlights
            if item.get("htmlSnippet"):
                result.highlights = [item["htmlSnippet"]]
            
            results.append(result)
        
        return results
    
    def _format_date_range(self, date_range: Dict) -> str:
        """Format date range for Google API"""
        # Google uses formats like d[number] for days, w[number] for weeks
        # For simplicity, we'll calculate days difference
        if "start" in date_range:
            start = datetime.fromisoformat(date_range["start"])
            days = (datetime.now() - start).days
            if days <= 1:
                return "d1"
            elif days <= 7:
                return "w1"
            elif days <= 30:
                return "m1"
            elif days <= 365:
                return "y1"
        return ""