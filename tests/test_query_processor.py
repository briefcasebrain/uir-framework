"""Tests for query processing and enhancement"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.uir.query_processor import (
    QueryProcessor,
    ProcessedQuery,
    SpellChecker,
    EntityExtractor,
    QueryExpander,
    IntentClassifier
)


class TestQueryProcessor:
    """Test query processor functionality"""
    
    @pytest.fixture
    def query_processor(self):
        """Create query processor"""
        return QueryProcessor()
    
    @pytest.mark.asyncio
    async def test_process_basic_query(self, query_processor):
        """Test basic query processing"""
        result = await query_processor.process("machine learning algorithms")
        
        assert result.original == "machine learning algorithms"
        assert result.keywords == ["machine", "learning", "algorithms"]
        assert result.corrected is None  # No spelling errors
        assert isinstance(result.expanded, str)
        assert len(result.expanded) > len(result.original)
    
    @pytest.mark.asyncio
    async def test_process_with_spelling_correction(self, query_processor):
        """Test query processing with spelling correction"""
        result = await query_processor.process("transformr atention mechanizm")
        
        assert result.original == "transformr atention mechanizm"
        assert result.corrected == "transformer attention mechanism"
        assert result.expanded is not None
    
    @pytest.mark.asyncio
    async def test_process_with_entity_extraction(self, query_processor):
        """Test entity extraction in query processing"""
        result = await query_processor.process("papers about BERT from 2024-01-15")
        
        assert result.entities is not None
        assert len(result.entities) > 0
        
        # Should extract date entity
        date_entities = [e for e in result.entities if e["type"] == "DATE"]
        assert len(date_entities) > 0
        assert "2024-01-15" in date_entities[0]["value"]
        
        # Should extract technology entity
        tech_entities = [e for e in result.entities if e["type"] == "TECHNOLOGY"]
        assert len(tech_entities) > 0
    
    @pytest.mark.asyncio
    async def test_process_with_intent_classification(self, query_processor):
        """Test intent classification"""
        # Test explanation intent
        result = await query_processor.process("explain how transformers work")
        assert result.intent["type"] == "explanation"
        
        # Test comparison intent
        result = await query_processor.process("compare BERT vs GPT")
        assert result.intent["type"] == "comparison"
        
        # Test tutorial intent
        result = await query_processor.process("how to implement attention mechanism")
        assert result.intent["type"] == "tutorial"
        
        # Test news intent
        result = await query_processor.process("latest developments in AI")
        assert result.intent["type"] == "news"
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, query_processor):
        """Test embedding generation"""
        embedding = await query_processor.generate_embedding("test query")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768  # Default embedding size
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_filters(self, query_processor):
        """Test filter generation from entities and intent"""
        entities = [
            {"type": "DATE", "value": "2024-01-01"},
            {"type": "LOCATION", "value": "San Francisco"},
            {"type": "ORGANIZATION", "value": "OpenAI"}
        ]
        
        intent = {"type": "academic"}
        
        filters = query_processor.generate_filters(entities, intent)
        
        assert filters["date_range"] == "2024-01-01"
        assert filters["location"] == "San Francisco"
        assert filters["organization"] == "OpenAI"
        assert "paper" in filters["document_type"]
    
    def test_get_query_hash(self, query_processor):
        """Test query hash generation"""
        hash1 = query_processor.get_query_hash("test query")
        hash2 = query_processor.get_query_hash("test query")
        hash3 = query_processor.get_query_hash("different query")
        
        assert hash1 == hash2  # Same query produces same hash
        assert hash1 != hash3  # Different queries produce different hashes
        
        # Test with filters
        hash_with_filter = query_processor.get_query_hash(
            "test query",
            {"category": "AI"}
        )
        assert hash_with_filter != hash1


class TestSpellChecker:
    """Test spell checker functionality"""
    
    @pytest.fixture
    def spell_checker(self):
        return SpellChecker()
    
    @pytest.mark.asyncio
    async def test_correct_spelling(self, spell_checker):
        """Test spelling correction"""
        result = await spell_checker.correct("transformr atention mechanizm")
        assert result == "transformer attention mechanism"
        
        result = await spell_checker.correct("serch for databse")
        assert result == "search for database"
    
    @pytest.mark.asyncio
    async def test_no_correction_needed(self, spell_checker):
        """Test when no correction is needed"""
        result = await spell_checker.correct("machine learning")
        assert result == "machine learning"


class TestEntityExtractor:
    """Test entity extraction"""
    
    @pytest.fixture
    def entity_extractor(self):
        return EntityExtractor()
    
    @pytest.mark.asyncio
    async def test_extract_dates(self, entity_extractor):
        """Test date extraction"""
        entities = await entity_extractor.extract("papers from 2024-01-15 to 2024-12-31")
        
        date_entities = [e for e in entities if e["type"] == "DATE"]
        assert len(date_entities) >= 2
        assert any("2024-01-15" in e["value"] for e in date_entities)
        assert any("2024-12-31" in e["value"] for e in date_entities)
    
    @pytest.mark.asyncio
    async def test_extract_emails(self, entity_extractor):
        """Test email extraction"""
        entities = await entity_extractor.extract("contact john@example.com for details")
        
        email_entities = [e for e in entities if e["type"] == "EMAIL"]
        assert len(email_entities) == 1
        assert email_entities[0]["value"] == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_extract_technology_terms(self, entity_extractor):
        """Test technology term extraction"""
        entities = await entity_extractor.extract("using transformer and BERT for NLP")
        
        tech_entities = [e for e in entities if e["type"] == "TECHNOLOGY"]
        assert len(tech_entities) >= 2
        assert any("transformer" in e["value"] for e in tech_entities)
        assert any("bert" in e["value"] for e in tech_entities)


class TestQueryExpander:
    """Test query expansion"""
    
    @pytest.fixture
    def query_expander(self):
        return QueryExpander()
    
    @pytest.mark.asyncio
    async def test_expand_with_synonyms(self, query_expander):
        """Test query expansion with synonyms"""
        expanded = await query_expander.expand("machine learning")
        
        assert "machine learning" in expanded
        # Should include synonyms
        assert any(term in expanded.lower() for term in ["ml", "artificial intelligence", "ai"])
    
    @pytest.mark.asyncio
    async def test_expand_with_entities(self, query_expander):
        """Test query expansion with entities"""
        entities = [
            {"type": "TECHNOLOGY", "value": "transformer"}
        ]
        
        expanded = await query_expander.expand("transformer models", entities)
        
        assert "transformer" in expanded
        # Should include related terms
        assert any(term in expanded.lower() for term in ["attention", "bert", "gpt"])


class TestIntentClassifier:
    """Test intent classification"""
    
    @pytest.fixture
    def intent_classifier(self):
        return IntentClassifier()
    
    @pytest.mark.asyncio
    async def test_classify_explanation_intent(self, intent_classifier):
        """Test explanation intent classification"""
        intent = await intent_classifier.classify("explain how neural networks work")
        assert intent["type"] == "explanation"
        assert intent["confidence"] >= 0.8
    
    @pytest.mark.asyncio
    async def test_classify_comparison_intent(self, intent_classifier):
        """Test comparison intent classification"""
        intent = await intent_classifier.classify("difference between CNN and RNN")
        assert intent["type"] == "comparison"
    
    @pytest.mark.asyncio
    async def test_classify_tutorial_intent(self, intent_classifier):
        """Test tutorial intent classification"""
        intent = await intent_classifier.classify("tutorial on implementing LSTM")
        assert intent["type"] == "tutorial"
    
    @pytest.mark.asyncio
    async def test_classify_academic_intent(self, intent_classifier):
        """Test academic intent classification"""
        intent = await intent_classifier.classify("research papers on quantum computing")
        assert intent["type"] == "academic"
    
    @pytest.mark.asyncio
    async def test_classify_general_intent(self, intent_classifier):
        """Test general intent classification"""
        intent = await intent_classifier.classify("artificial intelligence")
        assert intent["type"] == "general"
        assert intent["confidence"] <= 0.7  # Lower confidence for general