"""Mock embedding service for testing without external APIs"""

import hashlib
import numpy as np
from typing import List, Dict, Any
import asyncio


class MockEmbeddingService:
    """Mock embedding service that generates deterministic embeddings"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.cache = {}
        self.model_name = "mock-embedding-model"
    
    async def embed(self, text: str) -> List[float]:
        """Generate deterministic embedding from text"""
        # Check cache first
        if text in self.cache:
            return self.cache[text]
        
        # Generate deterministic embedding based on text content
        # This ensures same text always gets same embedding
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to numbers
        np.random.seed(int(text_hash[:8], 16))
        
        # Generate embedding with some structure
        embedding = []
        
        # Add some semantic structure based on text features
        text_lower = text.lower()
        
        # Base random values
        base_embedding = np.random.randn(self.dimension) * 0.5
        
        # Add semantic signals
        if "machine learning" in text_lower:
            base_embedding[0:50] += 0.3
        if "deep learning" in text_lower:
            base_embedding[50:100] += 0.3
        if "transformer" in text_lower:
            base_embedding[100:150] += 0.4
        if "attention" in text_lower:
            base_embedding[150:200] += 0.35
        if "neural" in text_lower:
            base_embedding[200:250] += 0.3
        if "search" in text_lower:
            base_embedding[250:300] += 0.25
        if "query" in text_lower:
            base_embedding[300:350] += 0.25
        if "document" in text_lower:
            base_embedding[350:400] += 0.3
        if "vector" in text_lower:
            base_embedding[400:450] += 0.35
        if "semantic" in text_lower:
            base_embedding[450:500] += 0.4
        
        # Add length signal
        base_embedding[500:510] += len(text) / 100.0
        
        # Normalize to unit vector
        norm = np.linalg.norm(base_embedding)
        if norm > 0:
            base_embedding = base_embedding / norm
        
        embedding = base_embedding.tolist()
        
        # Cache for consistency
        self.cache[text] = embedding
        
        # Simulate API latency
        await asyncio.sleep(0.01)
        
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts"""
        tasks = [self.embed(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "type": "mock",
            "cached_embeddings": len(self.cache)
        }