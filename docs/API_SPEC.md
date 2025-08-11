# UIR Framework API Specification

## Overview

The Universal Information Retrieval (UIR) Framework provides a unified REST API for searching across multiple information retrieval providers. This specification defines all endpoints, request/response formats, error codes, and authentication methods.

**Base URL**: `https://api.uir-framework.com/v1`  
**Protocol**: HTTPS  
**Authentication**: API Key or JWT Bearer Token  
**Content-Type**: `application/json`

## Authentication

### API Key Authentication

Include the API key in the `Authorization` header:

```http
Authorization: Bearer uir_abc123def456ghi789
```

### JWT Token Authentication

For user-based authentication:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Creating API Keys

```http
POST /auth/keys
Content-Type: application/json
Authorization: Bearer <admin_token>

{
    "user_id": "user_123",
    "permissions": ["search", "vector_search", "hybrid_search"],
    "rate_limit": 1000,
    "expires_at": "2024-12-31T23:59:59Z",
    "name": "Production API Key"
}
```

**Response**:
```json
{
    "api_key": "uir_abc123def456ghi789",
    "user_id": "user_123",
    "permissions": ["search", "vector_search", "hybrid_search"],
    "rate_limit": 1000,
    "expires_at": "2024-12-31T23:59:59Z",
    "created_at": "2024-01-15T10:30:00Z"
}
```

## Search Endpoints

### Text Search

Execute text-based search across one or multiple providers.

```http
POST /search
Content-Type: application/json
Authorization: Bearer <api_key>

{
    "provider": "google",
    "query": "machine learning algorithms 2024",
    "options": {
        "limit": 20,
        "offset": 0,
        "min_score": 0.5,
        "filters": {
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            },
            "language": "en",
            "domain": "arxiv.org"
        },
        "rerank": true,
        "deduplicate": true,
        "cache": {
            "enabled": true,
            "ttl_seconds": 3600
        }
    }
}
```

**Parameters**:
- `provider` (string|array): Single provider or list of providers
- `query` (string): Search query text
- `options` (object): Optional search parameters
  - `limit` (integer): Maximum results to return (1-100, default: 10)
  - `offset` (integer): Pagination offset (default: 0)
  - `min_score` (float): Minimum relevance score (0-1)
  - `filters` (object): Provider-specific filters
  - `rerank` (boolean): Enable ML-based reranking (default: false)
  - `deduplicate` (boolean): Remove duplicate results (default: true)
  - `cache` (object): Caching options

**Response**:
```json
{
    "status": "success",
    "request_id": "req_abc123def456",
    "results": [
        {
            "id": "google_1",
            "title": "Advanced Machine Learning Algorithms in 2024",
            "content": "This paper presents the latest developments in ML algorithms...",
            "url": "https://arxiv.org/abs/2024.01.001",
            "score": 0.95,
            "provider": "google",
            "metadata": {
                "published_date": "2024-01-15",
                "authors": ["Dr. Jane Smith", "Prof. John Doe"],
                "citations": 42,
                "file_type": "pdf"
            },
            "highlights": [
                "This paper presents the latest developments in <em>machine learning algorithms</em>",
                "The 2024 survey covers <em>deep learning</em> and <em>transformer models</em>"
            ]
        }
    ],
    "metadata": {
        "query_time_ms": 245,
        "providers_used": ["google"],
        "providers_failed": [],
        "cache_hit": false,
        "spell_corrected": false,
        "total_results": 1500,
        "filters_applied": {
            "date_range": "2024-01-01:2024-12-31"
        }
    },
    "pagination": {
        "offset": 0,
        "limit": 20,
        "has_more": true,
        "total_pages": 75
    }
}
```

### Vector Search

Execute semantic similarity search using vector embeddings.

```http
POST /vector/search
Content-Type: application/json
Authorization: Bearer <api_key>

{
    "provider": "pinecone",
    "text": "neural network architectures for natural language processing",
    "vector": [0.1, -0.2, 0.3, ...],  // Alternative to text
    "index": "research-papers",
    "options": {
        "limit": 10,
        "namespace": "ai-papers",
        "include_metadata": true,
        "include_values": false,
        "filters": {
            "category": {"$eq": "machine_learning"},
            "year": {"$gte": 2020}
        }
    }
}
```

**Parameters**:
- `provider` (string): Vector database provider
- `text` (string): Text to convert to vector (alternative to vector)
- `vector` (array): Pre-computed embedding vector
- `index` (string): Target index name
- `options` (object): Provider-specific options
  - `namespace` (string): Vector namespace
  - `include_metadata` (boolean): Include result metadata
  - `include_values` (boolean): Include vector values in response
  - `filters` (object): Metadata filters

**Response**:
```json
{
    "status": "success",
    "request_id": "req_def456ghi789",
    "results": [
        {
            "id": "vec_12345",
            "title": "Transformer Networks for NLP",
            "content": "Attention mechanisms in neural networks...",
            "score": 0.89,
            "provider": "pinecone",
            "metadata": {
                "category": "machine_learning",
                "year": 2023,
                "venue": "NeurIPS"
            },
            "vector": [0.1, -0.2, 0.3, ...]  // If include_values=true
        }
    ],
    "metadata": {
        "query_time_ms": 156,
        "providers_used": ["pinecone"],
        "embedding_model": "text-embedding-ada-002",
        "index_stats": {
            "total_vectors": 1000000,
            "dimension": 1536
        }
    }
}
```

### Hybrid Search

Combine multiple search strategies with intelligent fusion.

```http
POST /hybrid/search
Content-Type: application/json
Authorization: Bearer <api_key>

{
    "strategies": [
        {
            "type": "keyword",
            "provider": "elasticsearch", 
            "query": "machine learning algorithms",
            "weight": 0.4,
            "options": {
                "index": "research-db",
                "boost_fields": ["title^2", "abstract^1.5"]
            }
        },
        {
            "type": "vector",
            "provider": "pinecone",
            "text": "neural network architectures", 
            "weight": 0.6,
            "options": {
                "index": "paper-embeddings",
                "namespace": "cs-papers"
            }
        }
    ],
    "fusion_method": "reciprocal_rank",
    "options": {
        "limit": 15,
        "rerank": true,
        "diversity_threshold": 0.7
    }
}
```

**Parameters**:
- `strategies` (array): List of search strategies to combine
  - `type` (string): "keyword", "vector", or "graph"
  - `provider` (string): Provider for this strategy
  - `query`/`text`/`vector`: Query parameters based on type
  - `weight` (float): Relative weight for fusion (0-1)
  - `options` (object): Strategy-specific options
- `fusion_method` (string): "reciprocal_rank", "weighted_sum", "max_score"
- `options` (object): Global hybrid search options

**Response**:
```json
{
    "status": "success",
    "request_id": "req_ghi789jkl012",
    "results": [
        {
            "id": "hybrid_1",
            "title": "Deep Learning for NLP: A Survey",
            "content": "Comprehensive review of deep learning approaches...",
            "score": 0.92,
            "provider": "hybrid",
            "metadata": {
                "fusion_score": 0.92,
                "strategy_scores": {
                    "elasticsearch": 0.85,
                    "pinecone": 0.94
                },
                "diversity_score": 0.78
            }
        }
    ],
    "metadata": {
        "query_time_ms": 320,
        "providers_used": ["elasticsearch", "pinecone"],
        "fusion_method": "reciprocal_rank",
        "strategies_executed": 2,
        "reranking_applied": true
    }
}
```

## Query Analysis

### Analyze Query

Analyze and enhance user queries with spell correction, entity extraction, and intent classification.

```http
POST /query/analyze
Content-Type: application/json
Authorization: Bearer <api_key>

{
    "query": "machien leraning algorthims for natual language procesing",
    "options": {
        "spell_correction": true,
        "entity_extraction": true,
        "intent_classification": true,
        "query_expansion": true,
        "generate_embedding": true
    }
}
```

**Response**:
```json
{
    "original_query": "machien leraning algorthims for natual language procesing",
    "corrected_query": "machine learning algorithms for natural language processing",
    "expanded_query": "machine learning algorithms ML artificial intelligence natural language processing NLP computational linguistics",
    "entities": [
        {
            "text": "machine learning",
            "type": "TECHNOLOGY",
            "confidence": 0.95,
            "start": 0,
            "end": 16
        },
        {
            "text": "natural language processing",
            "type": "TECHNOLOGY", 
            "confidence": 0.98,
            "start": 31,
            "end": 58
        }
    ],
    "intent": {
        "type": "informational",
        "confidence": 0.87,
        "category": "research"
    },
    "suggested_filters": {
        "domain": ["cs.AI", "cs.CL"],
        "keywords": ["machine learning", "NLP", "algorithms"],
        "categories": ["artificial intelligence", "computational linguistics"]
    },
    "keywords": ["machine", "learning", "algorithms", "natural", "language", "processing"],
    "embedding": [0.1, -0.2, 0.3, ...],  // If generate_embedding=true
    "query_complexity": "medium",
    "language": "en"
}
```

## Document Management

### Index Documents

Add documents to a provider's index for future retrieval.

```http
POST /documents/index
Content-Type: application/json
Authorization: Bearer <api_key>

{
    "provider": "elasticsearch",
    "index": "research-papers",
    "documents": [
        {
            "id": "doc_001",
            "title": "Attention Is All You Need",
            "content": "We propose a new simple network architecture, the Transformer...",
            "url": "https://arxiv.org/abs/1706.03762",
            "metadata": {
                "authors": ["Ashish Vaswani", "Noam Shazeer"],
                "year": 2017,
                "venue": "NeurIPS",
                "categories": ["cs.CL", "cs.LG"]
            },
            "vector": [0.1, -0.2, 0.3, ...]  // Optional pre-computed embedding
        }
    ],
    "options": {
        "generate_embeddings": true,
        "embedding_model": "text-embedding-ada-002",
        "batch_size": 100,
        "update_if_exists": true
    }
}
```

**Response**:
```json
{
    "status": "success",
    "request_id": "req_index_001",
    "indexed_count": 1,
    "failed_count": 0,
    "results": [
        {
            "id": "doc_001",
            "status": "indexed",
            "provider_id": "es_doc_001_v1"
        }
    ],
    "metadata": {
        "processing_time_ms": 1250,
        "embeddings_generated": 1,
        "index": "research-papers",
        "provider": "elasticsearch"
    }
}
```

### Batch Operations

Execute multiple search operations in a single request.

```http
POST /batch
Content-Type: application/json
Authorization: Bearer <api_key>

{
    "operations": [
        {
            "id": "search_1",
            "type": "search",
            "params": {
                "provider": "google",
                "query": "machine learning trends 2024"
            }
        },
        {
            "id": "vector_search_1", 
            "type": "vector_search",
            "params": {
                "provider": "pinecone",
                "text": "neural network architectures",
                "index": "ai-papers"
            }
        }
    ],
    "options": {
        "parallel": true,
        "fail_fast": false
    }
}
```

## RAG Integration

### RAG Retrieve

Optimized retrieval for Retrieval-Augmented Generation pipelines.

```http
POST /rag/retrieve
Content-Type: application/json
Authorization: Bearer <api_key>

{
    "query": "Explain the attention mechanism in transformers",
    "providers": ["pinecone", "elasticsearch"],
    "options": {
        "num_chunks": 5,
        "chunk_overlap": 100,
        "max_chunk_size": 1000,
        "include_sources": true,
        "rerank_for_relevance": true,
        "diversity_penalty": 0.3
    }
}
```

**Response**:
```json
{
    "status": "success",
    "context": "The attention mechanism is a key component of transformer architectures...\n\nIn the original Transformer paper, attention allows the model to focus...",
    "chunks": [
        {
            "text": "The attention mechanism is a key component of transformer architectures that allows models to weigh the importance of different input tokens.",
            "source": "https://arxiv.org/abs/1706.03762",
            "score": 0.94,
            "metadata": {
                "title": "Attention Is All You Need",
                "chunk_index": 0,
                "provider": "pinecone"
            }
        }
    ],
    "metadata": {
        "providers_queried": ["pinecone", "elasticsearch"],
        "query_time_ms": 180,
        "total_chunks_found": 25,
        "chunks_returned": 5,
        "reranking_applied": true
    }
}
```

## Management Endpoints

### Provider Status

Get status and health information for all providers.

```http
GET /providers
Authorization: Bearer <api_key>
```

**Response**:
```json
{
    "providers": {
        "total_providers": 8,
        "healthy": 6,
        "degraded": 1, 
        "unhealthy": 1,
        "providers": {
            "google": {
                "status": "healthy",
                "latency_ms": 120,
                "success_rate": 0.99,
                "last_check": "2024-01-15T10:45:00Z",
                "capabilities": ["search"],
                "rate_limit": {
                    "requests_per_minute": 100,
                    "remaining": 87
                }
            },
            "pinecone": {
                "status": "degraded",
                "latency_ms": 450,
                "success_rate": 0.85,
                "last_check": "2024-01-15T10:45:00Z",
                "capabilities": ["vector_search"],
                "error_message": "Elevated latency detected"
            },
            "elasticsearch": {
                "status": "unhealthy",
                "last_check": "2024-01-15T10:45:00Z",
                "error_message": "Connection timeout"
            }
        }
    }
}
```

### Usage Statistics

Get usage statistics and billing information.

```http
GET /usage?period=current_month
Authorization: Bearer <api_key>
```

**Response**:
```json
{
    "period": "2024-01",
    "user_id": "user_123",
    "statistics": {
        "total_requests": 15420,
        "successful_requests": 14891,
        "error_rate": 0.034,
        "avg_response_time_ms": 156,
        "requests_by_type": {
            "search": 8500,
            "vector_search": 4200,
            "hybrid_search": 2720
        },
        "providers_used": {
            "google": 6800,
            "pinecone": 4200,
            "elasticsearch": 4420
        },
        "cache_hit_rate": 0.23
    },
    "billing": {
        "total_cost": 45.67,
        "cost_by_provider": {
            "google": 12.30,
            "pinecone": 18.90,
            "elasticsearch": 14.47
        },
        "requests_remaining": 4580,
        "rate_limit": 1000
    }
}
```

### Health Check

System health and readiness endpoints.

```http
GET /health
```

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:45:00Z",
    "version": "1.2.0",
    "uptime_seconds": 1234567,
    "dependencies": {
        "database": "healthy",
        "cache": "healthy", 
        "providers": "degraded"
    },
    "metrics": {
        "requests_per_second": 125.4,
        "avg_response_time_ms": 145,
        "memory_usage_percent": 67,
        "cpu_usage_percent": 23
    }
}
```

```http
GET /ready
```

**Response**:
```json
{
    "ready": true,
    "checks": {
        "database_connected": true,
        "cache_available": true,
        "providers_configured": true
    }
}
```

## Error Responses

### Error Format

All errors follow a consistent format:

```json
{
    "error": {
        "code": "PROVIDER_TIMEOUT",
        "message": "Provider request timed out after 5000ms",
        "details": {
            "provider": "google",
            "timeout_ms": 5000,
            "query": "machine learning"
        },
        "request_id": "req_abc123def456",
        "timestamp": "2024-01-15T10:45:00Z",
        "documentation_url": "https://docs.uir-framework.com/errors/PROVIDER_TIMEOUT"
    }
}
```

### Error Codes

#### Authentication Errors (401)
- `MISSING_API_KEY`: API key not provided
- `INVALID_API_KEY`: API key is invalid or expired
- `EXPIRED_TOKEN`: JWT token has expired

#### Authorization Errors (403)  
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded for API key
- `QUOTA_EXCEEDED`: Usage quota exceeded

#### Request Errors (400)
- `INVALID_REQUEST`: Request format is invalid
- `MISSING_REQUIRED_FIELD`: Required field is missing
- `INVALID_FIELD_VALUE`: Field value is invalid
- `QUERY_TOO_LONG`: Query exceeds maximum length
- `UNSUPPORTED_PROVIDER`: Provider is not supported

#### Provider Errors (502, 503)
- `PROVIDER_TIMEOUT`: Provider request timed out
- `PROVIDER_ERROR`: Provider returned an error
- `PROVIDER_UNAVAILABLE`: Provider is temporarily unavailable
- `ALL_PROVIDERS_FAILED`: All requested providers failed

#### System Errors (500)
- `INTERNAL_ERROR`: Unexpected system error
- `SERVICE_UNAVAILABLE`: Service is temporarily unavailable
- `CONFIGURATION_ERROR`: System configuration error

## Rate Limits

### Default Limits

| Plan | Requests/Minute | Requests/Day | Concurrent |
|------|----------------|--------------|------------|
| Free | 100 | 1,000 | 5 |
| Pro | 1,000 | 50,000 | 20 |  
| Enterprise | 10,000 | 1,000,000 | 100 |

### Rate Limit Headers

Response headers include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987  
X-RateLimit-Reset: 1642781400
X-RateLimit-Reset-After: 45
```

### Rate Limit Response

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 45

{
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Rate limit of 1000 requests per minute exceeded",
        "details": {
            "limit": 1000,
            "remaining": 0,
            "reset_at": "2024-01-15T10:46:00Z",
            "retry_after": 45
        }
    }
}
```

## Webhooks

### Webhook Configuration

Configure webhooks to receive real-time updates:

```http
POST /webhooks
Content-Type: application/json
Authorization: Bearer <api_key>

{
    "url": "https://your-app.com/webhooks/uir",
    "events": ["search.completed", "search.failed", "provider.status_changed"],
    "secret": "webhook_secret_key",
    "active": true
}
```

### Webhook Events

#### search.completed
```json
{
    "event": "search.completed",
    "timestamp": "2024-01-15T10:45:00Z",
    "data": {
        "request_id": "req_abc123def456",
        "user_id": "user_123", 
        "query": "machine learning",
        "provider": "google",
        "results_count": 10,
        "response_time_ms": 156
    }
}
```

#### provider.status_changed
```json
{
    "event": "provider.status_changed",
    "timestamp": "2024-01-15T10:45:00Z", 
    "data": {
        "provider": "google",
        "previous_status": "healthy",
        "current_status": "degraded", 
        "reason": "Elevated response time"
    }
}
```

## SDKs

### Python SDK

```python
from uir_client import UIRClient

client = UIRClient(
    api_key="uir_abc123def456",
    base_url="https://api.uir-framework.com/v1"
)

# Search
results = await client.search(
    provider="google",
    query="machine learning algorithms"
)

# Vector search
results = await client.vector_search(
    provider="pinecone", 
    text="neural networks",
    index="ai-papers"
)

# Hybrid search  
results = await client.hybrid_search(
    strategies=[
        {"type": "keyword", "provider": "elasticsearch", "weight": 0.4},
        {"type": "vector", "provider": "pinecone", "weight": 0.6}
    ]
)
```

### JavaScript SDK

```javascript
import { UIRClient } from '@uir/client';

const client = new UIRClient({
    apiKey: 'uir_abc123def456',
    baseUrl: 'https://api.uir-framework.com/v1'
});

// Search
const results = await client.search({
    provider: 'google',
    query: 'machine learning algorithms'
});

// Vector search
const vectorResults = await client.vectorSearch({
    provider: 'pinecone',
    text: 'neural networks', 
    index: 'ai-papers'
});
```

This comprehensive API specification provides developers with all the information needed to integrate with the UIR Framework effectively.