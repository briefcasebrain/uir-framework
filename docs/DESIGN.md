# UIR Framework Design Document

## Design Philosophy

The Universal Information Retrieval (UIR) Framework is designed around five core principles:

1. **Simplicity**: Easy to use, understand, and maintain
2. **Extensibility**: Easy to add new providers and capabilities
3. **Performance**: Optimized for high-throughput, low-latency operations
4. **Reliability**: Built for production workloads with fault tolerance
5. **Developer Experience**: Intuitive APIs and comprehensive documentation

## System Design

### Design Goals

#### Primary Goals
- **Unified Interface**: Single API for all information retrieval needs
- **Provider Abstraction**: Hide provider complexity behind clean interfaces
- **Intelligent Routing**: Smart provider selection and fallback
- **Result Quality**: Advanced result fusion and ranking algorithms
- **Scalability**: Handle enterprise-scale workloads efficiently

#### Secondary Goals
- **Cost Optimization**: Minimize API costs through intelligent caching
- **Monitoring**: Comprehensive observability and debugging capabilities
- **Security**: Enterprise-grade security and access control
- **Flexibility**: Support diverse use cases and deployment patterns

### Design Constraints

#### Technical Constraints
- **Language**: Python 3.9+ for maximum compatibility
- **Async**: Async/await throughout for performance
- **Dependencies**: Minimize external dependencies
- **Memory**: Efficient memory usage for large-scale deployments
- **Latency**: p50 < 100ms, p99 < 500ms response times

#### Business Constraints
- **Provider APIs**: Work within rate limits and quotas
- **Cost**: Minimize per-request costs through caching and optimization
- **Compliance**: Support GDPR, SOC2, and other compliance requirements
- **SLA**: 99.9% uptime with graceful degradation

## Component Design

### 1. Router Service Design

**Purpose**: Central orchestrator for all search operations

```python
class RouterService:
    """Central router for search operations"""
    
    def __init__(
        self,
        provider_manager: ProviderManager,
        query_processor: QueryProcessor,
        aggregator: ResultAggregator,
        cache_manager: CacheManager
    ):
        self.provider_manager = provider_manager
        self.query_processor = query_processor
        self.aggregator = aggregator
        self.cache_manager = cache_manager
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute standard text search"""
        # 1. Check cache
        # 2. Process query
        # 3. Select providers
        # 4. Execute parallel searches
        # 5. Aggregate results
        # 6. Cache response
        # 7. Return response
```

**Design Decisions**:
- **Dependency Injection**: All dependencies injected for testability
- **Error Isolation**: Provider failures don't crash the service
- **Timeout Handling**: Configurable timeouts with graceful degradation
- **Request Correlation**: Unique request IDs for debugging and tracing

### 2. Query Processor Design

**Purpose**: Transform and enhance user queries for optimal search

```python
class QueryProcessor:
    """Intelligent query processing and enhancement"""
    
    async def process(self, query: str) -> ProcessedQuery:
        """Process raw query into enhanced version"""
        # Run processing tasks in parallel
        tasks = [
            self.spell_check(query),
            self.extract_entities(query),
            self.classify_intent(query),
            self.extract_keywords(query)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Generate embeddings if needed
        embedding = await self.generate_embedding(query)
        
        # Expand query with synonyms and related terms
        expanded = await self.expand_query(query, entities)
        
        return ProcessedQuery(
            original=query,
            corrected=results[0],
            entities=results[1],
            intent=results[2],
            keywords=results[3],
            embedding=embedding,
            expanded=expanded
        )
```

**Design Decisions**:
- **Parallel Processing**: All NLP tasks run concurrently
- **Pluggable Components**: Each processing step is replaceable
- **Graceful Degradation**: Processing failures don't block search
- **Caching**: Cache expensive operations like embeddings

### 3. Provider Manager Design

**Purpose**: Manage provider lifecycle and health monitoring

```python
class ProviderManager:
    """Manages provider adapters and health monitoring"""
    
    def __init__(self):
        self.adapters: Dict[str, ProviderAdapter] = {}
        self.health_status: Dict[str, ProviderHealth] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.load_balancers: Dict[str, LoadBalancer] = {}
    
    async def execute_search(
        self, 
        providers: List[str], 
        search_func: Callable
    ) -> List[SearchResult]:
        """Execute search across multiple providers"""
        # Select healthy providers
        healthy_providers = self.get_healthy_providers(providers)
        
        # Execute with circuit breaker protection
        tasks = []
        for provider in healthy_providers:
            if self.circuit_breakers[provider].can_execute():
                tasks.append(self._protected_search(provider, search_func))
        
        # Gather results with timeout
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update health metrics
        self._update_health_metrics(providers, results)
        
        return results
```

**Design Decisions**:
- **Circuit Breaker Pattern**: Prevent cascade failures
- **Health Monitoring**: Continuous health checks and metrics
- **Load Balancing**: Distribute load across healthy providers
- **Graceful Degradation**: Continue with available providers

### 4. Result Aggregator Design

**Purpose**: Intelligent result fusion and ranking

```python
class ResultAggregator:
    """Advanced result aggregation and ranking"""
    
    def aggregate(
        self,
        results: List[SearchResult],
        deduplicate: bool = True,
        fusion_method: str = "reciprocal_rank"
    ) -> List[SearchResult]:
        """Aggregate results from multiple providers"""
        
        if deduplicate:
            results = self.deduplicate_results(results)
        
        if fusion_method == "reciprocal_rank":
            return self.reciprocal_rank_fusion(results)
        elif fusion_method == "weighted_sum":
            return self.weighted_sum_fusion(results)
        elif fusion_method == "max_score":
            return self.max_score_fusion(results)
        else:
            return sorted(results, key=lambda x: x.score, reverse=True)
    
    def reciprocal_rank_fusion(
        self, 
        result_lists: List[List[SearchResult]], 
        k: int = 60
    ) -> List[SearchResult]:
        """Reciprocal Rank Fusion algorithm"""
        scores = defaultdict(float)
        results_by_id = {}
        
        for result_list in result_lists:
            for rank, result in enumerate(result_list, 1):
                scores[result.id] += 1.0 / (k + rank)
                results_by_id[result.id] = result
        
        # Sort by RRF score
        sorted_ids = sorted(scores.keys(), key=scores.get, reverse=True)
        
        # Return results with new scores
        fused_results = []
        for result_id in sorted_ids:
            result = results_by_id[result_id]
            result.score = scores[result_id]
            fused_results.append(result)
        
        return fused_results
```

**Design Decisions**:
- **Multiple Fusion Algorithms**: Support different fusion strategies
- **Deduplication**: Smart duplicate detection using URL and content similarity
- **Score Normalization**: Normalize scores across providers
- **Diversity Injection**: Optionally inject diversity into results

### 5. Cache Manager Design

**Purpose**: Multi-tier caching for performance optimization

```python
class CacheManager:
    """Multi-tier caching system"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_client = redis.from_url(redis_url)
        self.local_cache: Dict[str, Any] = {}
        self.default_ttl = default_ttl
    
    async def get(self, request: SearchRequest) -> Optional[SearchResponse]:
        """Get cached response for request"""
        cache_key = self._generate_cache_key(request)
        
        # Check if caching is disabled for this request
        if not self._is_cacheable(request):
            return None
        
        # Try Redis first (L2 cache)
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    return self._deserialize_response(cached_data)
            except Exception:
                # Redis failure, continue with local cache
                pass
        
        # Fall back to local cache (L1 cache)
        if cache_key in self.local_cache:
            entry = self.local_cache[cache_key]
            if entry["expires_at"] > datetime.now():
                return entry["data"]
            else:
                del self.local_cache[cache_key]
        
        return None
    
    def _generate_cache_key(self, request: SearchRequest) -> str:
        """Generate deterministic cache key"""
        key_parts = [
            request.provider if isinstance(request.provider, str) else ",".join(sorted(request.provider)),
            hashlib.md5(request.query.encode()).hexdigest(),
            hashlib.md5(json.dumps(request.options.model_dump() if request.options else {}, sort_keys=True).encode()).hexdigest()[:8]
        ]
        return f"uir:v1:{':'.join(key_parts)}"
```

**Design Decisions**:
- **Two-Tier Caching**: Redis (L2) + Memory (L1) for optimal performance
- **Cache Key Design**: Deterministic keys based on request parameters
- **TTL Strategy**: Configurable TTL with cache warming
- **Failure Handling**: Graceful degradation when cache is unavailable

### 6. Authentication Design

**Purpose**: Secure access control and usage tracking

```python
class AuthManager:
    """Authentication and authorization management"""
    
    def __init__(self, jwt_secret: str):
        self.jwt_secret = jwt_secret
        self.api_keys: Dict[str, Dict] = {}  # In production: use database
        self.rate_limiters: Dict[str, RateLimiter] = {}
    
    def create_api_key(
        self,
        user_id: str,
        permissions: List[str],
        rate_limit: int = 1000,
        expires_at: Optional[datetime] = None
    ) -> str:
        """Create new API key with permissions"""
        api_key = f"uir_{secrets.token_urlsafe(32)}"
        
        self.api_keys[api_key] = {
            "user_id": user_id,
            "permissions": set(permissions),
            "rate_limit": rate_limit,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "usage_count": 0,
            "last_used": None
        }
        
        # Create rate limiter for this key
        self.rate_limiters[api_key] = RateLimiter(rate_limit)
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key and return key data"""
        if api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        
        # Check expiration
        if key_data["expires_at"] and key_data["expires_at"] < datetime.now():
            return None
        
        # Update usage
        key_data["usage_count"] += 1
        key_data["last_used"] = datetime.now()
        
        return key_data
```

**Design Decisions**:
- **API Key Format**: Prefixed keys for easy identification
- **Permission System**: Granular permissions for different operations
- **Rate Limiting**: Per-key rate limiting with token bucket algorithm
- **Usage Tracking**: Track usage patterns for analytics and billing

## Data Models

### Core Models

```python
# Request Models
class SearchRequest(BaseModel):
    provider: Union[str, List[str]]
    query: str
    options: Optional[SearchOptions] = None

class SearchOptions(BaseModel):
    limit: int = 10
    offset: int = 0
    min_score: Optional[float] = None
    filters: Optional[Dict[str, Any]] = None
    rerank: bool = False
    cache: Optional[CacheOptions] = None

# Response Models
class SearchResponse(BaseModel):
    status: str  # "success", "partial", "error"
    request_id: str
    results: List[SearchResult]
    metadata: ResponseMetadata
    errors: Optional[List[Dict[str, str]]] = None

class SearchResult(BaseModel):
    id: str
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    score: float
    provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    highlights: Optional[List[str]] = None

# Configuration Models
class ProviderConfig(BaseModel):
    name: str
    type: ProviderType
    auth_method: str
    credentials: Dict[str, Any]
    endpoints: Dict[str, str]
    rate_limits: Dict[str, int]
    retry_policy: Dict[str, int]
    timeout_ms: int
    circuit_breaker_config: Dict[str, int]
```

**Design Decisions**:
- **Pydantic Models**: Type safety and validation
- **Optional Fields**: Flexible models that work across providers
- **Extensible Metadata**: Provider-specific data in metadata field
- **Consistent Naming**: Clear, descriptive field names

## API Design

### RESTful Design Principles

The UIR Framework API follows REST principles with some pragmatic adaptations:

#### Resource-Oriented URLs
```
POST /search                    # Search across providers
POST /vector/search            # Vector similarity search  
POST /hybrid/search           # Hybrid search strategies
POST /query/analyze           # Query analysis
GET  /providers               # List available providers
GET  /health                  # System health
```

#### HTTP Methods
- **POST**: Used for search operations (request body needed)
- **GET**: Used for resource retrieval and status endpoints
- **PUT/PATCH**: Used for configuration updates (admin endpoints)
- **DELETE**: Used for resource deletion (admin endpoints)

#### Status Codes
- **200**: Success with results
- **202**: Accepted (async processing started)
- **400**: Bad request (validation error)
- **401**: Unauthorized (missing/invalid API key)
- **403**: Forbidden (insufficient permissions)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error
- **503**: Service Unavailable (maintenance mode)

#### Response Format
```json
{
    "status": "success",
    "request_id": "req_123456789",
    "results": [...],
    "metadata": {
        "query_time_ms": 150,
        "providers_used": ["google", "pinecone"],
        "cache_hit": false,
        "total_results": 1000
    },
    "pagination": {
        "offset": 0,
        "limit": 10,
        "has_more": true
    }
}
```

### Error Handling Design

```python
class UIRException(Exception):
    """Base exception for UIR framework"""
    
    def __init__(self, message: str, code: str, details: Dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class ProviderException(UIRException):
    """Provider-specific errors"""
    pass

class RateLimitException(UIRException):
    """Rate limit exceeded"""
    pass

class AuthenticationException(UIRException):
    """Authentication/authorization errors"""
    pass
```

**Error Response Format**:
```json
{
    "error": {
        "code": "PROVIDER_TIMEOUT",
        "message": "Provider request timed out",
        "details": {
            "provider": "google",
            "timeout_ms": 5000
        },
        "request_id": "req_123456789"
    }
}
```

## Configuration Design

### Environment-Based Configuration

```python
class Config:
    """Application configuration"""
    
    # Core settings
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    DATABASE_URL: str = Field(env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Authentication
    JWT_SECRET: str = Field(env="JWT_SECRET")
    API_KEY_PREFIX: str = Field(default="uir_", env="API_KEY_PREFIX")
    
    # Provider credentials
    GOOGLE_API_KEY: Optional[str] = Field(env="GOOGLE_API_KEY")
    PINECONE_API_KEY: Optional[str] = Field(env="PINECONE_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(env="OPENAI_API_KEY")
    
    # Performance
    DEFAULT_TIMEOUT_MS: int = Field(default=5000, env="DEFAULT_TIMEOUT_MS")
    MAX_CONCURRENT_REQUESTS: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    DEFAULT_CACHE_TTL: int = Field(default=3600, env="DEFAULT_CACHE_TTL")
    
    # Feature flags
    ENABLE_QUERY_EXPANSION: bool = Field(default=True, env="ENABLE_QUERY_EXPANSION")
    ENABLE_RESULT_CACHING: bool = Field(default=True, env="ENABLE_RESULT_CACHING")
    MOCK_MODE: bool = Field(default=False, env="MOCK_MODE")

    class Config:
        env_file = ".env"
        case_sensitive = True
```

### Provider Configuration

```yaml
# config/providers.yaml
providers:
  google:
    enabled: true
    type: "search_engine"
    auth_method: "api_key"
    credentials:
      api_key: "${GOOGLE_API_KEY}"
      cx: "${GOOGLE_CSE_ID}"
    endpoints:
      search: "https://www.googleapis.com/customsearch/v1"
    rate_limits:
      default: 100
      burst: 10
    retry_policy:
      max_attempts: 3
      backoff_multiplier: 2
      max_backoff_ms: 10000
    timeout_ms: 5000
    circuit_breaker:
      failure_threshold: 5
      recovery_timeout: 60
      min_requests: 10
    
  pinecone:
    enabled: true
    type: "vector_db"
    auth_method: "api_key"
    credentials:
      api_key: "${PINECONE_API_KEY}"
      environment: "us-west1-gcp"
      index_name: "default"
    endpoints:
      query: "https://{index}.svc.{environment}.pinecone.io"
    rate_limits:
      default: 100
    timeout_ms: 3000
```

## Testing Design

### Testing Strategy

#### Unit Tests
- Test individual components in isolation
- Mock all external dependencies
- Focus on business logic and edge cases
- Target 90%+ code coverage

#### Integration Tests
- Test component interactions
- Use real external services in staging
- Verify end-to-end workflows
- Include error scenarios

#### Mock Testing
- Comprehensive mocks for all providers
- Deterministic results for reproducible tests
- Performance testing without external costs
- Development without API keys

```python
# Mock Design Pattern
class MockProviderAdapter(ProviderAdapter):
    """Mock provider for testing"""
    
    def __init__(self, responses: List[SearchResult]):
        self.responses = responses
        self.call_count = 0
    
    async def search(self, query: str, options: Dict) -> List[SearchResult]:
        self.call_count += 1
        await asyncio.sleep(0.1)  # Simulate API latency
        return self.responses[:options.get("limit", 10)]
    
    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider="mock",
            status="healthy",
            latency_ms=100,
            success_rate=1.0
        )
```

### Test Data Management

```python
# Fixtures for consistent test data
@pytest.fixture
def sample_search_results():
    return [
        SearchResult(
            id="1",
            title="Machine Learning Basics",
            content="Introduction to ML concepts",
            url="https://example.com/ml-basics",
            score=0.95,
            provider="google"
        ),
        # ... more results
    ]

@pytest.fixture
def mock_google_adapter(sample_search_results):
    return MockGoogleAdapter(sample_search_results)
```

## Performance Design

### Performance Requirements

- **Latency**: p50 < 100ms, p95 < 300ms, p99 < 500ms
- **Throughput**: 10,000+ requests per second
- **Availability**: 99.9% uptime
- **Scalability**: Linear scaling with load

### Optimization Strategies

#### Async/Await Architecture
```python
async def parallel_provider_search(providers: List[str], query: str) -> List[SearchResult]:
    """Execute searches in parallel"""
    tasks = [
        provider_adapter.search(query) 
        for provider_adapter in providers
    ]
    
    # Wait for all with timeout
    results = await asyncio.gather(
        *tasks, 
        return_exceptions=True
    )
    
    return [r for r in results if not isinstance(r, Exception)]
```

#### Connection Pooling
```python
class ProviderAdapter:
    def __init__(self):
        # Use connection pooling for HTTP clients
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=httpx.Timeout(5.0)
        )
```

#### Memory Management
```python
class CacheManager:
    def __init__(self, max_memory_mb: int = 100):
        self.max_memory_mb = max_memory_mb
        self.local_cache = {}
    
    def _evict_if_needed(self):
        """Evict cache entries if memory limit exceeded"""
        current_size = sys.getsizeof(self.local_cache) / (1024 * 1024)
        if current_size > self.max_memory_mb:
            # LRU eviction
            oldest_keys = sorted(
                self.local_cache.keys(),
                key=lambda k: self.local_cache[k]["last_accessed"]
            )[:len(self.local_cache) // 4]
            
            for key in oldest_keys:
                del self.local_cache[key]
```

## Security Design

### Security Principles

1. **Defense in Depth**: Multiple layers of security
2. **Principle of Least Privilege**: Minimal required permissions
3. **Secure by Default**: Security enabled out of the box
4. **Audit Everything**: Comprehensive logging and monitoring

### Security Implementation

#### Input Validation
```python
class QueryValidator:
    """Validate and sanitize search queries"""
    
    MAX_QUERY_LENGTH = 1000
    BLOCKED_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'union\s+select',            # SQL injection
        r'javascript:',               # JavaScript URLs
    ]
    
    def validate_query(self, query: str) -> str:
        """Validate and sanitize query"""
        if len(query) > self.MAX_QUERY_LENGTH:
            raise ValidationError("Query too long")
        
        # Check for malicious patterns
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                raise SecurityError("Malicious query detected")
        
        # HTML encode special characters
        return html.escape(query)
```

#### Rate Limiting
```python
class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, capacity: int, refill_rate: int):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
```

#### Data Protection
```python
class DataProtection:
    """Data privacy and protection utilities"""
    
    @staticmethod
    def redact_pii(text: str) -> str:
        """Redact personally identifiable information"""
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Social security numbers
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        return text
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
```

This design document provides the detailed technical design for implementing a production-ready Universal Information Retrieval Framework with enterprise-grade features, performance, and security.