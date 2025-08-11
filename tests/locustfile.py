"""Locust load testing configuration for UIR Framework API"""

from locust import HttpUser, task, between
import json
import random


class UIRFrameworkUser(HttpUser):
    """Simulated user for load testing UIR Framework API"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Initialize user session"""
        # Create a test API key (in real scenario, this would be pre-created)
        self.headers = {
            "Authorization": "Bearer test-api-key-for-load-testing",
            "Content-Type": "application/json"
        }
        
        # Test queries for different scenarios
        self.queries = [
            "machine learning algorithms",
            "natural language processing",
            "deep learning frameworks",
            "computer vision techniques",
            "reinforcement learning methods",
            "transformer neural networks",
            "artificial intelligence research",
            "data science best practices",
            "python programming tutorials",
            "software engineering patterns"
        ]
        
        self.providers = ["google", "elasticsearch", "pinecone"]
    
    @task(3)
    def health_check(self):
        """Test health check endpoint (lightweight)"""
        with self.client.get("/health", headers={"Accept": "application/json"}) as response:
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
    
    @task(1)
    def ready_check(self):
        """Test readiness endpoint"""
        self.client.get("/ready", headers={"Accept": "application/json"})
    
    @task(10)
    def search_single_provider(self):
        """Test single provider search"""
        query = random.choice(self.queries)
        provider = random.choice(self.providers)
        
        payload = {
            "provider": provider,
            "query": query,
            "options": {
                "limit": random.randint(5, 20),
                "rerank": random.choice([True, False])
            }
        }
        
        with self.client.post("/search", 
                             headers=self.headers, 
                             json=payload,
                             catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    response.success()
                else:
                    response.failure(f"Search failed: {data.get('error', 'Unknown error')}")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")
    
    @task(5)
    def search_multiple_providers(self):
        """Test multi-provider search"""
        query = random.choice(self.queries)
        providers = random.sample(self.providers, random.randint(2, 3))
        
        payload = {
            "provider": providers,
            "query": query,
            "options": {
                "limit": 10,
                "fusion_method": "reciprocal_rank"
            }
        }
        
        with self.client.post("/search", 
                             headers=self.headers, 
                             json=payload) as response:
            if response.status_code == 200:
                data = response.json()
                # Multi-provider might have partial success
                assert data["status"] in ["success", "partial"]
    
    @task(3)
    def vector_search(self):
        """Test vector search"""
        query = random.choice(self.queries)
        
        payload = {
            "provider": "pinecone",
            "text": query,
            "index": "test-index",
            "options": {
                "limit": random.randint(3, 10),
                "include_metadata": True
            }
        }
        
        with self.client.post("/vector/search", 
                             headers=self.headers, 
                             json=payload) as response:
            if response.status_code in [200, 404]:  # 404 if index doesn't exist in mock
                pass  # Accept both for load testing
    
    @task(2)
    def hybrid_search(self):
        """Test hybrid search"""
        query = random.choice(self.queries)
        
        payload = {
            "strategies": [
                {
                    "type": "keyword",
                    "provider": "elasticsearch",
                    "query": query,
                    "weight": 0.4
                },
                {
                    "type": "vector", 
                    "provider": "pinecone",
                    "text": query,
                    "weight": 0.6
                }
            ],
            "fusion_method": "reciprocal_rank",
            "options": {
                "limit": 10
            }
        }
        
        self.client.post("/hybrid/search", 
                        headers=self.headers, 
                        json=payload)
    
    @task(2)
    def query_analyze(self):
        """Test query analysis"""
        query = random.choice(self.queries)
        
        # Add some intentional typos for spell correction testing
        if random.random() < 0.3:
            query = query.replace("machine", "machien").replace("learning", "lerning")
        
        payload = {
            "query": query,
            "options": {
                "spell_correction": True,
                "entity_extraction": True,
                "intent_classification": True
            }
        }
        
        self.client.post("/query/analyze", 
                        headers=self.headers, 
                        json=payload)
    
    @task(1)
    def get_providers(self):
        """Test provider status endpoint"""
        self.client.get("/providers", headers=self.headers)
    
    @task(1)
    def get_usage(self):
        """Test usage statistics endpoint"""
        self.client.get("/usage", headers=self.headers)
    
    @task(1)
    def rag_retrieve(self):
        """Test RAG retrieval endpoint"""
        query = random.choice(self.queries)
        
        payload = {
            "query": query,
            "providers": ["elasticsearch", "pinecone"],
            "options": {
                "num_chunks": random.randint(3, 8),
                "max_chunk_size": 1000
            }
        }
        
        self.client.post("/rag/retrieve", 
                        headers=self.headers, 
                        json=payload)


class HighVolumeUser(HttpUser):
    """High-volume user for stress testing"""
    
    wait_time = between(0.1, 0.5)  # Very fast requests
    weight = 1
    
    @task
    def rapid_health_checks(self):
        """Rapid health check requests"""
        self.client.get("/health")
    
    @task
    def rapid_searches(self):
        """Rapid search requests"""
        payload = {
            "provider": "google",
            "query": "test query",
            "options": {"limit": 5}
        }
        
        headers = {
            "Authorization": "Bearer test-api-key",
            "Content-Type": "application/json"
        }
        
        self.client.post("/search", headers=headers, json=payload)


class BurstyUser(HttpUser):
    """User that creates bursty traffic patterns"""
    
    wait_time = between(10, 30)  # Long waits between bursts
    weight = 1
    
    @task
    def burst_requests(self):
        """Create a burst of requests"""
        headers = {
            "Authorization": "Bearer test-api-key",
            "Content-Type": "application/json"
        }
        
        # Send 10 rapid requests
        for i in range(10):
            payload = {
                "provider": "google", 
                "query": f"burst query {i}",
                "options": {"limit": 5}
            }
            self.client.post("/search", headers=headers, json=payload)