"""Data models for UIR framework"""

from enum import Enum
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ProviderType(str, Enum):
    """Types of information retrieval providers"""
    SEARCH_ENGINE = "search_engine"
    VECTOR_DB = "vector_db"
    DOCUMENT_STORE = "document_store"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    ENTERPRISE = "enterprise"
    ACADEMIC = "academic"
    DATA_WAREHOUSE = "data_warehouse"


class Provider(str, Enum):
    """Available providers"""
    # Search Engines
    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    BRAVE = "brave"
    SERPER = "serper"
    SERPAPI = "serpapi"
    YOU = "you"
    
    # Vector Databases
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    MILVUS = "milvus"
    CHROMADB = "chromadb"
    ZILLIZ = "zilliz"
    VESPA = "vespa"
    VALD = "vald"
    FAISS = "faiss"
    ANNOY = "annoy"
    
    # Document Stores
    ELASTICSEARCH = "elasticsearch"
    OPENSEARCH = "opensearch"
    SOLR = "solr"
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    COUCHDB = "couchdb"
    MARKLOGIC = "marklogic"
    
    # Knowledge Graphs
    NEO4J = "neo4j"
    NEPTUNE = "neptune"
    ARANGODB = "arangodb"
    TIGERGRAPH = "tigergraph"
    DGRAPH = "dgraph"
    JANUSGRAPH = "janusgraph"
    MEMGRAPH = "memgraph"
    
    # Enterprise & Specialized
    ALGOLIA = "algolia"
    TYPESENSE = "typesense"
    MEILISEARCH = "meilisearch"
    AZURE_SEARCH = "azure_search"
    KENDRA = "kendra"
    COVEO = "coveo"
    SWIFTYPE = "swiftype"
    CONSTRUCTOR = "constructor"
    
    # Academic
    SEMANTIC_SCHOLAR = "semantic_scholar"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    CROSSREF = "crossref"
    CORE = "core"
    
    # Data Warehouses
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    CLICKHOUSE = "clickhouse"
    DRUID = "druid"


class CacheOptions(BaseModel):
    """Cache configuration options"""
    enabled: bool = True
    ttl_seconds: int = 3600
    key: Optional[str] = None


class FilterClause(BaseModel):
    """Filter clause for search queries"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, contains
    value: Any


class DateRange(BaseModel):
    """Date range filter"""
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class SearchOptions(BaseModel):
    """Options for search operations"""
    limit: int = Field(default=10, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    timeout_ms: int = Field(default=5000, ge=100, le=60000)
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[DateRange] = None
    include_metadata: bool = True
    include_explanation: bool = False
    rerank: bool = False
    cache: Optional[CacheOptions] = None
    fallback_providers: Optional[List[str]] = None
    min_score: Optional[float] = None
    deduplicate: bool = True


class SearchResult(BaseModel):
    """Individual search result"""
    id: str
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    score: float
    provider: str
    metadata: Optional[Dict[str, Any]] = None
    highlights: Optional[List[str]] = None
    explanation: Optional[str] = None
    vector: Optional[List[float]] = None


class ResponseMetadata(BaseModel):
    """Metadata about the search response"""
    total_results: Optional[int] = None
    query_time_ms: int
    providers_used: List[str]
    providers_failed: Optional[List[str]] = None
    cache_hit: bool = False
    transformations_applied: Optional[List[str]] = None
    filters_applied: Optional[List[str]] = None
    spell_corrected: bool = False


class SearchRequest(BaseModel):
    """Standard search request"""
    model_config = ConfigDict(protected_namespaces=())
    
    provider: Union[str, List[str]]
    query: str
    options: Optional[SearchOptions] = None
    metadata: Optional[Dict[str, Any]] = None


class VectorSearchRequest(BaseModel):
    """Vector similarity search request"""
    model_config = ConfigDict(protected_namespaces=())
    
    provider: Union[str, List[str]]
    vector: Optional[List[float]] = None
    text: Optional[str] = None
    index: Optional[str] = None
    namespace: Optional[str] = None
    options: Optional[SearchOptions] = None
    metadata: Optional[Dict[str, Any]] = None


class HybridStrategy(BaseModel):
    """Strategy for hybrid search"""
    type: str  # keyword, vector, knowledge_graph
    provider: str
    weight: float = Field(ge=0.0, le=1.0)
    query: Optional[str] = None
    text: Optional[str] = None
    vector: Optional[List[float]] = None
    cypher: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class HybridSearchRequest(BaseModel):
    """Hybrid search combining multiple strategies"""
    strategies: List[HybridStrategy]
    fusion_method: str = "reciprocal_rank"  # reciprocal_rank, weighted_sum, max_score
    options: Optional[SearchOptions] = None


class SearchResponse(BaseModel):
    """Unified search response"""
    status: str  # success, partial, error
    request_id: str
    results: List[SearchResult]
    metadata: ResponseMetadata
    errors: Optional[List[Dict[str, Any]]] = None
    provider_used: Optional[str] = None
    query_id: Optional[str] = None


class IndexRequest(BaseModel):
    """Document indexing request"""
    provider: str
    documents: List[Dict[str, Any]]
    index_name: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class QueryAnalysis(BaseModel):
    """Query analysis results"""
    original_query: str
    corrected_query: Optional[str] = None
    expanded_query: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    intent: Optional[Dict[str, Any]] = None
    suggested_filters: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    sentiment: Optional[str] = None
    complexity: Optional[float] = None


class ProviderConfig(BaseModel):
    """Provider configuration"""
    name: str
    type: ProviderType
    auth_method: str
    credentials: Dict[str, Any]
    endpoints: Dict[str, str]
    rate_limits: Dict[str, int]
    retry_policy: Dict[str, Any]
    timeout_ms: int = 5000
    circuit_breaker_config: Optional[Dict[str, Any]] = None


class ProviderHealth(BaseModel):
    """Provider health status"""
    provider: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: Optional[float] = None
    success_rate: Optional[float] = None
    last_check: datetime
    error_message: Optional[str] = None


class UsageMetrics(BaseModel):
    """Usage metrics for tracking"""
    period: str
    total_requests: int
    by_provider: Dict[str, int]
    by_operation: Dict[str, int]
    tokens_processed: Optional[int] = None
    storage_gb: Optional[float] = None
    cost_usd: Optional[float] = None