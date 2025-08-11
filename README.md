# Universal Information Retrieval (UIR) Framework

A unified, scalable framework for information retrieval across multiple providers, supporting search engines, vector databases, document stores, and hybrid search capabilities.

## 🌟 Features

### Core Capabilities
- **Multi-Provider Support**: Integrate with 50+ search providers (Google, Bing, Elasticsearch, Pinecone, etc.)
- **Hybrid Search**: Combine keyword, vector, and semantic search strategies
- **Query Intelligence**: Advanced query processing with spell correction, entity extraction, and intent classification
- **Result Fusion**: Smart aggregation with reciprocal rank fusion and weighted scoring
- **High Performance**: Async architecture with circuit breakers, rate limiting, and intelligent caching
- **Enterprise Ready**: JWT authentication, RBAC, usage tracking, and comprehensive monitoring

### Search Types
- **Keyword Search**: Traditional text-based search across web engines and document stores
- **Vector Search**: Semantic similarity search using embedding models
- **Hybrid Search**: Intelligent combination of multiple search strategies
- **RAG Integration**: Optimized retrieval for Retrieval-Augmented Generation pipelines

## Installation

```bash
pip install uir-framework
```

Or install with specific providers:

```bash
pip install uir-framework[google,pinecone,elasticsearch]
```

## Quick Start

```python
from uir import UIR

# Initialize client
client = UIR(
    api_key="your-api-key",
    provider_keys={
        "google": {"api_key": "...", "cx": "..."},
        "pinecone": "pinecone-key",
        "openai": "openai-key"  # For embeddings
    }
)

# Simple search
results = client.search(
    provider="google",
    query="machine learning frameworks",
    limit=10
)

# Vector search
results = client.vector_search(
    provider="pinecone",
    text="What are transformer models?",
    index="research-papers",
    top_k=5
)

# Hybrid search
results = client.hybrid_search(
    strategies=[
        {"type": "keyword", "provider": "elasticsearch", "weight": 0.4, "query": "transformers"},
        {"type": "vector", "provider": "pinecone", "weight": 0.6, "text": "attention mechanism"}
    ],
    fusion_method="reciprocal_rank"
)

# RAG retrieval
context = client.rag_retrieve(
    query="Explain BERT architecture",
    providers=["pinecone", "elasticsearch"],
    num_chunks=5
)
```

## API Documentation

### Search Operations

#### Standard Search
```python
response = client.search(
    provider="google",  # or ["google", "bing"] for multiple
    query="your search query",
    limit=10,
    filters={"date_range": {"start": "2023-01-01"}},
    rerank=True
)
```

#### Vector Search
```python
response = client.vector_search(
    provider="pinecone",
    vector=[0.1, 0.2, ...],  # Or use text for auto-embedding
    text="semantic search query",
    index="documents",
    filters={"category": "research"}
)
```

#### Hybrid Search
```python
response = client.hybrid_search(
    strategies=[
        {"type": "keyword", "provider": "elasticsearch", "weight": 0.3},
        {"type": "vector", "provider": "weaviate", "weight": 0.7}
    ],
    fusion_method="weighted_sum"  # or "reciprocal_rank", "max_score"
)
```

### Advanced Features

#### Query Analysis
```python
analysis = client.analyze_query("transformr atention mechanizm")
# Returns: corrected query, entities, intent, suggested filters
```

#### Document Indexing
```python
result = client.index_documents(
    provider="elasticsearch",
    documents=[
        {
            "id": "doc1",
            "title": "Introduction to AI",
            "content": "...",
            "vector": [0.1, 0.2, ...]
        }
    ]
)
```

#### Batch Operations
```python
results = client.batch_search([
    {"provider": "google", "query": "machine learning"},
    {"provider": "pinecone", "vector": [0.1, 0.2, ...]}
])
```

## Running the API Server

### Using Docker

```bash
docker-compose up
```

### Using Kubernetes

```bash
kubectl apply -f deployments/kubernetes.yaml
```

### Development Mode

```bash
uvicorn src.uir.api.main:app --reload
```

## Configuration

### Environment Variables

```bash
UIR_API_KEY=your-master-key
UIR_GOOGLE_API_KEY=google-key
UIR_GOOGLE_CX=search-engine-id
UIR_PINECONE_API_KEY=pinecone-key
UIR_OPENAI_API_KEY=openai-key
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/uir
```

### Provider Configuration

```python
client = UIR(
    provider_keys={
        "google": {
            "api_key": "...",
            "cx": "..."
        },
        "elasticsearch": {
            "host": "localhost",
            "port": 9200,
            "username": "elastic",
            "password": "..."
        }
    }
)
```

## Supported Providers

### Search Engines
- Google Custom Search
- Bing Search API
- DuckDuckGo
- Brave Search
- And more...

### Vector Databases
- Pinecone
- Weaviate
- Qdrant
- Milvus
- ChromaDB
- And more...

### Document Stores
- Elasticsearch
- OpenSearch
- MongoDB Atlas
- PostgreSQL with pgvector
- And more...

### Knowledge Graphs
- Neo4j
- Amazon Neptune
- ArangoDB
- And more...

## Architecture

The UIR framework follows a layered architecture:

1. **Client Layer**: SDKs for Python, JavaScript, Go
2. **API Gateway**: Authentication, rate limiting, routing
3. **Core Services**: Query processing, provider management, result aggregation
4. **Provider Adapters**: Unified interface for diverse providers
5. **Storage Layer**: Caching, metadata, audit logs

## Performance

- **Latency**: p50 < 100ms, p99 < 500ms
- **Throughput**: 10,000+ requests/second
- **Availability**: 99.99% uptime
- **Scalability**: Horizontal auto-scaling

## Monitoring

The framework includes built-in monitoring with:
- Prometheus metrics
- Grafana dashboards
- Distributed tracing
- Health checks

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Roadmap

- [ ] Additional provider integrations
- [ ] GraphQL API support
- [ ] Real-time streaming results
- [ ] ML-based query understanding
- [ ] Multi-modal search (images, audio)
- [ ] Federated learning for result ranking