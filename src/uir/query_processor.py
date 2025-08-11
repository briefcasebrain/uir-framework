"""Query processing and enhancement module"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import structlog
import hashlib

from .models import QueryAnalysis
from .mocks.embedding_service import MockEmbeddingService
from .mocks.spell_checker import MockSpellChecker
from .mocks.entity_extractor import MockEntityExtractor

logger = structlog.get_logger()


@dataclass
class ProcessedQuery:
    """Processed query with enhancements"""
    original: str
    corrected: Optional[str] = None
    expanded: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    intent: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    filters: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None


class QueryProcessor:
    """Handles query understanding, enhancement, and optimization"""
    
    def __init__(self, embedding_service: Optional[Any] = None):
        self.embedding_service = embedding_service or MockEmbeddingService()
        self.spell_checker = MockSpellChecker()
        self.entity_extractor = MockEntityExtractor()
        self.query_expander = QueryExpander()
        self.intent_classifier = IntentClassifier()
        self.logger = logger.bind(component="query_processor")
    
    async def process(self, query: str) -> ProcessedQuery:
        """Process and enhance query"""
        # Run processing tasks in parallel
        tasks = [
            self.spell_check(query),
            self.extract_entities(query),
            self.classify_intent(query),
            self.extract_keywords(query)
        ]
        
        if self.embedding_service:
            tasks.append(self.generate_embedding(query))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        corrected = results[0] if not isinstance(results[0], Exception) else None
        entities = results[1] if not isinstance(results[1], Exception) else None
        intent = results[2] if not isinstance(results[2], Exception) else None
        keywords = results[3] if not isinstance(results[3], Exception) else None
        embedding = results[4] if len(results) > 4 and not isinstance(results[4], Exception) else None
        
        # Expand query based on extracted information
        expanded = await self.expand_query(corrected or query, entities)
        
        # Generate filters from entities
        filters = self.generate_filters(entities, intent)
        
        return ProcessedQuery(
            original=query,
            corrected=corrected if corrected != query else None,
            expanded=expanded,
            entities=entities,
            intent=intent,
            embedding=embedding,
            filters=filters,
            keywords=keywords
        )
    
    async def spell_check(self, query: str) -> str:
        """Check and correct spelling"""
        return await self.spell_checker.correct(query)
    
    async def extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract named entities from query"""
        return await self.entity_extractor.extract(query)
    
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify query intent"""
        return await self.intent_classifier.classify(query)
    
    async def extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        # Simple keyword extraction
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "is", "are", "was", "were", "been", "be"}
        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords
    
    async def expand_query(
        self,
        query: str,
        entities: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Expand query with synonyms and related terms"""
        return await self.query_expander.expand(query, entities)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding"""
        return await self.embedding_service.embed(text)
    
    def generate_filters(
        self,
        entities: Optional[List[Dict[str, Any]]],
        intent: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Generate search filters from entities and intent"""
        if not entities and not intent:
            return None
        
        filters = {}
        
        # Extract filters from entities
        if entities:
            for entity in entities:
                if entity.get("type") == "DATE":
                    filters["date_range"] = entity.get("value")
                elif entity.get("type") == "LOCATION":
                    filters["location"] = entity.get("value")
                elif entity.get("type") == "ORGANIZATION":
                    filters["organization"] = entity.get("value")
        
        # Add intent-based filters
        if intent:
            if intent.get("type") == "academic":
                filters["document_type"] = ["paper", "article", "thesis"]
            elif intent.get("type") == "news":
                filters["document_type"] = ["news", "blog"]
        
        return filters if filters else None
    
    def get_query_hash(self, query: str, filters: Optional[Dict] = None) -> str:
        """Generate hash for query caching"""
        content = query
        if filters:
            content += str(sorted(filters.items()))
        return hashlib.sha256(content.encode()).hexdigest()


class SpellChecker:
    """Simple spell checker"""
    
    async def correct(self, text: str) -> str:
        """Correct spelling errors"""
        # Simple implementation - in production would use proper spell checker
        corrections = {
            "transformr": "transformer",
            "atention": "attention",
            "mechanizm": "mechanism",
            "serch": "search",
            "databse": "database"
        }
        
        result = text
        for wrong, right in corrections.items():
            result = re.sub(r'\b' + wrong + r'\b', right, result, flags=re.IGNORECASE)
        
        return result


class EntityExtractor:
    """Extract named entities from text"""
    
    async def extract(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities"""
        entities = []
        
        # Simple pattern-based extraction
        # Date patterns
        date_pattern = r'\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b'
        for match in re.finditer(date_pattern, text):
            entities.append({
                "text": match.group(),
                "type": "DATE",
                "value": match.group(),
                "confidence": 0.9
            })
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append({
                "text": match.group(),
                "type": "EMAIL",
                "value": match.group(),
                "confidence": 0.95
            })
        
        # Technology terms (simple list-based)
        tech_terms = ["transformer", "attention", "bert", "gpt", "machine learning", "deep learning", "neural network"]
        text_lower = text.lower()
        for term in tech_terms:
            if term in text_lower:
                entities.append({
                    "text": term,
                    "type": "TECHNOLOGY",
                    "value": term,
                    "confidence": 0.85
                })
        
        return entities


class QueryExpander:
    """Expand queries with synonyms and related terms"""
    
    async def expand(
        self,
        query: str,
        entities: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Expand query with related terms"""
        # Simple synonym expansion
        synonyms = {
            "machine learning": ["ML", "artificial intelligence", "AI", "deep learning"],
            "transformer": ["attention mechanism", "self-attention", "bert", "gpt"],
            "search": ["retrieval", "query", "find", "lookup"],
            "database": ["datastore", "repository", "storage", "db"]
        }
        
        expanded_terms = [query]
        query_lower = query.lower()
        
        for term, syns in synonyms.items():
            if term in query_lower:
                # Add first synonym as expansion
                if syns:
                    expanded_terms.append(syns[0])
        
        # Add entity-based expansions
        if entities:
            for entity in entities:
                if entity.get("type") == "TECHNOLOGY":
                    # Add related technology terms
                    related = synonyms.get(entity.get("value", "").lower(), [])
                    if related:
                        expanded_terms.extend(related[:1])
        
        return " ".join(expanded_terms)


class IntentClassifier:
    """Classify query intent"""
    
    async def classify(self, query: str) -> Dict[str, Any]:
        """Classify the intent of a query"""
        query_lower = query.lower()
        
        # Simple keyword-based classification
        if any(word in query_lower for word in ["explain", "what is", "how does", "define"]):
            return {"type": "explanation", "confidence": 0.85}
        elif any(word in query_lower for word in ["compare", "difference", "versus", "vs"]):
            return {"type": "comparison", "confidence": 0.80}
        elif any(word in query_lower for word in ["latest", "recent", "new", "news"]):
            return {"type": "news", "confidence": 0.75}
        elif any(word in query_lower for word in ["paper", "research", "study", "academic"]):
            return {"type": "academic", "confidence": 0.80}
        elif any(word in query_lower for word in ["tutorial", "guide", "how to", "example"]):
            return {"type": "tutorial", "confidence": 0.85}
        else:
            return {"type": "general", "confidence": 0.60}


class QueryAnalyzer:
    """Comprehensive query analysis"""
    
    async def analyze(self, query: str) -> QueryAnalysis:
        """Perform full query analysis"""
        processor = QueryProcessor()
        processed = await processor.process(query)
        
        return QueryAnalysis(
            original_query=query,
            corrected_query=processed.corrected,
            expanded_query=processed.expanded,
            entities=processed.entities,
            intent=processed.intent,
            suggested_filters=processed.filters,
            keywords=processed.keywords
        )