"""Mock entity extractor with comprehensive patterns"""

import re
from typing import List, Dict, Any
from datetime import datetime
import asyncio


class MockEntityExtractor:
    """Mock entity extractor with comprehensive pattern matching"""
    
    def __init__(self):
        self.patterns = {
            "DATE": [
                r'\b\d{4}-\d{2}-\d{2}\b',  # 2024-01-15
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # 1/15/2024, 01/15/24
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # January 15, 2024
                r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # 15 January 2024
            ],
            "EMAIL": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            "URL": [
                r'https?://[^\s<>"{}|\\^`\[\]]+',
                r'www\.[^\s<>"{}|\\^`\[\]]+',
                r'[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.(?:com|org|net|edu|gov|mil|int|arpa|biz|info|name|museum|coop|aero|[a-z]{2})\b'
            ],
            "PHONE": [
                r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
                r'\b\d{3}-\d{3}-\d{4}\b',
                r'\(\d{3}\)\s?\d{3}-\d{4}'
            ],
            "MONEY": [
                r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
                r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s?(?:USD|dollars?|cents?)\b',
            ],
            "PERCENTAGE": [
                r'\b\d+(?:\.\d+)?%',
                r'\b\d+(?:\.\d+)?\s?percent\b'
            ],
            "TIME": [
                r'\b\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM|am|pm)?\b',
                r'\b(?:morning|afternoon|evening|night)\b'
            ]
        }
        
        # Technology and domain-specific entities
        self.keyword_entities = {
            "TECHNOLOGY": [
                "transformer", "transformers", "bert", "gpt", "gpt-2", "gpt-3", "gpt-4",
                "attention", "self-attention", "multi-head", "encoder", "decoder",
                "neural network", "neural networks", "cnn", "rnn", "lstm", "gru",
                "machine learning", "deep learning", "artificial intelligence", "ai",
                "natural language processing", "nlp", "computer vision", "cv",
                "reinforcement learning", "supervised learning", "unsupervised learning",
                "classification", "regression", "clustering", "dimensionality reduction",
                "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
                "python", "java", "javascript", "go", "rust", "c++", "sql",
                "docker", "kubernetes", "aws", "azure", "gcp", "cloud computing",
                "api", "rest", "graphql", "microservices", "database", "nosql",
                "elasticsearch", "mongodb", "postgresql", "redis", "cassandra",
                "spark", "hadoop", "kafka", "rabbitmq", "nginx", "apache"
            ],
            "ORGANIZATION": [
                "google", "microsoft", "apple", "amazon", "meta", "facebook",
                "netflix", "uber", "airbnb", "twitter", "linkedin", "github",
                "openai", "huggingface", "deepmind", "nvidia", "intel", "amd",
                "mit", "stanford", "harvard", "berkeley", "carnegie mellon",
                "ieee", "acm", "arxiv", "pubmed", "nature", "science"
            ],
            "PERSON": [
                "john", "jane", "smith", "johnson", "brown", "davis", "miller",
                "wilson", "moore", "taylor", "anderson", "thomas", "jackson",
                "white", "harris", "martin", "thompson", "garcia", "martinez",
                "robinson", "clark", "rodriguez", "lewis", "lee", "walker"
            ],
            "LOCATION": [
                "new york", "los angeles", "chicago", "houston", "phoenix",
                "philadelphia", "san antonio", "san diego", "dallas", "san jose",
                "austin", "jacksonville", "san francisco", "columbus", "charlotte",
                "fort worth", "indianapolis", "seattle", "denver", "boston",
                "california", "texas", "florida", "new york", "pennsylvania",
                "illinois", "ohio", "georgia", "north carolina", "michigan",
                "usa", "united states", "america", "canada", "uk", "england",
                "france", "germany", "italy", "spain", "japan", "china", "india"
            ],
            "RESEARCH_FIELD": [
                "computer science", "machine learning", "artificial intelligence",
                "data science", "statistics", "mathematics", "physics",
                "biology", "chemistry", "medicine", "psychology", "neuroscience",
                "linguistics", "economics", "finance", "engineering",
                "electrical engineering", "software engineering", "bioengineering"
            ]
        }
    
    async def extract(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text"""
        entities = []
        text_lower = text.lower()
        
        # Extract pattern-based entities
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        "text": match.group(),
                        "type": entity_type,
                        "value": match.group(),
                        "confidence": 0.95,
                        "start": match.start(),
                        "end": match.end()
                    })
        
        # Extract keyword-based entities
        for entity_type, keywords in self.keyword_entities.items():
            for keyword in keywords:
                # Find whole word matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Calculate confidence based on exact match
                    confidence = 0.9 if match.group().lower() == keyword else 0.8
                    
                    entities.append({
                        "text": match.group(),
                        "type": entity_type,
                        "value": keyword,
                        "confidence": confidence,
                        "start": match.start(),
                        "end": match.end()
                    })
        
        # Extract numbers and quantities
        number_patterns = [
            (r'\b\d+(?:,\d{3})*(?:\.\d+)?\s?(?:billion|million|thousand|hundred)\b', "QUANTITY"),
            (r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', "NUMBER"),
            (r'\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b', "ORDINAL"),
            (r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b', "CARDINAL")
        ]
        
        for pattern, entity_type in number_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "text": match.group(),
                    "type": entity_type,
                    "value": match.group(),
                    "confidence": 0.85,
                    "start": match.start(),
                    "end": match.end()
                })
        
        # Remove duplicates and overlapping entities
        entities = self._remove_overlaps(entities)
        
        # Sort by position in text
        entities.sort(key=lambda x: x["start"])
        
        # Simulate processing time
        await asyncio.sleep(0.005)
        
        return entities
    
    def _remove_overlaps(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove overlapping entities, keeping highest confidence ones"""
        if not entities:
            return entities
        
        # Sort by start position, then by confidence (descending)
        entities.sort(key=lambda x: (x["start"], -x["confidence"]))
        
        filtered = []
        for entity in entities:
            # Check if this entity overlaps with any already accepted entity
            overlaps = False
            for accepted in filtered:
                if (entity["start"] < accepted["end"] and 
                    entity["end"] > accepted["start"]):
                    # There's an overlap
                    if entity["confidence"] <= accepted["confidence"]:
                        overlaps = True
                        break
                    else:
                        # This entity has higher confidence, remove the accepted one
                        filtered.remove(accepted)
                        break
            
            if not overlaps:
                filtered.append(entity)
        
        return filtered
    
    async def extract_by_type(self, text: str, entity_type: str) -> List[Dict[str, Any]]:
        """Extract specific type of entities"""
        all_entities = await self.extract(text)
        return [e for e in all_entities if e["type"] == entity_type]
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported entity types"""
        pattern_types = list(self.patterns.keys())
        keyword_types = list(self.keyword_entities.keys())
        additional_types = ["QUANTITY", "NUMBER", "ORDINAL", "CARDINAL"]
        
        return sorted(set(pattern_types + keyword_types + additional_types))