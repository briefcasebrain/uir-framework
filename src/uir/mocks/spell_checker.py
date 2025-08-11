"""Mock spell checker for testing"""

import re
from typing import Dict, List
import asyncio
from difflib import SequenceMatcher


class MockSpellChecker:
    """Mock spell checker with comprehensive dictionary"""
    
    def __init__(self):
        # Comprehensive corrections dictionary
        self.corrections = {
            # Technology terms
            "transformr": "transformer",
            "transformers": "transformers", 
            "atention": "attention",
            "mechanizm": "mechanism",
            "machien": "machine",
            "leraning": "learning",
            "learnign": "learning",
            "artifical": "artificial",
            "inteligence": "intelligence",
            "nueral": "neural",
            "netowrk": "network",
            "netwrok": "network",
            "algoritm": "algorithm",
            "algorithmn": "algorithm",
            "serch": "search",
            "seach": "search",
            "databse": "database",
            "databas": "database",
            "retreival": "retrieval",
            "retreval": "retrieval",
            "informaton": "information",
            "informtion": "information",
            
            # Common misspellings
            "teh": "the",
            "hte": "the",
            "adn": "and",
            "nad": "and",
            "wiht": "with",
            "wihth": "with",
            "whith": "with",
            "taht": "that",
            "thta": "that",
            "wich": "which",
            "whcih": "which",
            "recieve": "receive",
            "recieve": "receive",
            "seperate": "separate",
            "seprate": "separate",
            "occured": "occurred",
            "occure": "occur",
            "occurence": "occurrence",
            "begining": "beginning",
            "begging": "beginning",
            "comming": "coming",
            "runing": "running",
            "geting": "getting",
            "puting": "putting",
            "writting": "writing",
            "writng": "writing",
            
            # Research terms
            "reserch": "research",
            "reasearch": "research",
            "publshed": "published",
            "publised": "published",
            "anaylsis": "analysis",
            "analisys": "analysis",
            "expirment": "experiment",
            "experment": "experiment",
            "comparision": "comparison",
            "compairson": "comparison",
            "performace": "performance",
            "preformance": "performance",
            "assesment": "assessment",
            "assesments": "assessments",
            
            # Document terms
            "docuemnt": "document",
            "documnet": "document",
            "relavent": "relevant",
            "relevent": "relevant",
            "similiar": "similar",
            "simular": "similar",
            "accross": "across",
            "acros": "across",
            "procces": "process",
            "prcess": "process",
            "procesing": "processing",
            "processng": "processing"
        }
        
        # Valid words dictionary (for checking)
        self.valid_words = {
            "machine", "learning", "deep", "neural", "network", "transformer",
            "attention", "mechanism", "algorithm", "algorithms", "search", "retrieval",
            "database", "document", "query", "vector", "semantic", "model",
            "training", "inference", "prediction", "classification", "clustering",
            "supervised", "unsupervised", "reinforcement", "artificial",
            "intelligence", "data", "mining", "analysis", "processing",
            "computer", "vision", "language", "natural", "processing",
            "embedding", "similarity", "distance", "cosine", "euclidean",
            "research", "paper", "study", "experiment", "result", "conclusion",
            "method", "approach", "technique", "framework", "system",
            "performance", "accuracy", "precision", "recall", "score"
        }
    
    async def correct(self, text: str) -> str:
        """Correct spelling in text"""
        # Split text into words, preserving punctuation
        words = re.findall(r'\b\w+\b|\W+', text)
        corrected_words = []
        
        for word in words:
            if word.isalpha():
                # Check if word needs correction
                word_lower = word.lower()
                if word_lower in self.corrections:
                    # Apply correction while preserving case
                    corrected = self.corrections[word_lower]
                    if word.isupper():
                        corrected = corrected.upper()
                    elif word.istitle():
                        corrected = corrected.title()
                    corrected_words.append(corrected)
                else:
                    # Check for fuzzy matches
                    corrected = await self._fuzzy_correct(word_lower)
                    if corrected != word_lower:
                        # Apply case preservation
                        if word.isupper():
                            corrected = corrected.upper()
                        elif word.istitle():
                            corrected = corrected.title()
                        corrected_words.append(corrected)
                    else:
                        corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        # Add small delay to simulate processing
        await asyncio.sleep(0.001)
        
        return ''.join(corrected_words)
    
    async def _fuzzy_correct(self, word: str) -> str:
        """Find best fuzzy match for word"""
        if len(word) < 3:
            return word
        
        best_match = word
        best_ratio = 0.0
        
        # Check against valid words
        for valid_word in self.valid_words:
            if abs(len(word) - len(valid_word)) <= 2:  # Similar length
                ratio = SequenceMatcher(None, word, valid_word).ratio()
                if ratio > 0.8 and ratio > best_ratio:
                    best_ratio = ratio
                    best_match = valid_word
        
        # Check against correction keys
        for typo in self.corrections:
            if abs(len(word) - len(typo)) <= 1:
                ratio = SequenceMatcher(None, word, typo).ratio()
                if ratio > 0.85 and ratio > best_ratio:
                    best_ratio = ratio
                    best_match = self.corrections[typo]
        
        return best_match if best_ratio > 0.8 else word
    
    def is_misspelled(self, word: str) -> bool:
        """Check if word is misspelled"""
        word_lower = word.lower()
        return (word_lower not in self.valid_words and 
                word_lower not in self.corrections.values())
    
    def suggest_corrections(self, word: str) -> List[str]:
        """Get correction suggestions for a word"""
        word_lower = word.lower()
        
        if word_lower in self.corrections:
            return [self.corrections[word_lower]]
        
        suggestions = []
        
        # Find similar words
        for valid_word in self.valid_words:
            ratio = SequenceMatcher(None, word_lower, valid_word).ratio()
            if ratio > 0.6:
                suggestions.append((valid_word, ratio))
        
        # Sort by similarity and return top 3
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [word for word, _ in suggestions[:3]]