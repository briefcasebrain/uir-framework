"""Mock implementations for external services"""

from .embedding_service import MockEmbeddingService
from .spell_checker import MockSpellChecker
from .entity_extractor import MockEntityExtractor
from .database import MockDatabase
from .external_apis import (
    MockGoogleSearchAPI,
    MockPineconeAPI,
    MockElasticsearchAPI,
    MockRedisAPI
)

__all__ = [
    "MockEmbeddingService",
    "MockSpellChecker",
    "MockEntityExtractor",
    "MockDatabase",
    "MockGoogleSearchAPI",
    "MockPineconeAPI", 
    "MockElasticsearchAPI",
    "MockRedisAPI"
]