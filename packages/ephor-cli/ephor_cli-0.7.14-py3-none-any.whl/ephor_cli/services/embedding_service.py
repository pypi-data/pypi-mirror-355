import os
import logging
import time
from typing import List, Dict, Any
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using OpenAI's text-embedding-3-small model."""
    
    def __init__(self):
        # Read OpenAI API key from .env
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.model = "text-embedding-3-small"  # Hardcoded model
        self.batch_size = 20  # Hardcoded batch size
        
        self.client = OpenAI(api_key=self.api_key)
        
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts with batching."""
        if not texts:
            return []
        
        all_embeddings = []
        
        # Process in batches to avoid rate limits
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._generate_batch_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Small delay between batches to be respectful to API
            if i + self.batch_size < len(texts):
                time.sleep(0.1)
        
        logger.info(f"Generated embeddings for {len(texts)} texts")
        return all_embeddings
    
    def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a single batch of texts."""
        try:
            # Clean and prepare texts
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            response = self.client.embeddings.create(
                model=self.model,
                input=cleaned_texts,
                encoding_format="float"
            )
            
            embeddings = []
            for embedding_obj in response.data:
                embeddings.append(embedding_obj.embedding)
            
            logger.debug(f"Generated batch of {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 1536 for _ in texts]
    
    def generate_query_embedding(self, query_text: str) -> List[float]:
        """Generate embedding for a single query text."""
        try:
            cleaned_text = self._clean_text(query_text)
            
            response = self.client.embeddings.create(
                model=self.model,
                input=[cleaned_text],
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated query embedding for text length: {len(query_text)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536
    
    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for embedding generation."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = ' '.join(text.split())
        
        # Truncate if too long (OpenAI has token limits)
        max_chars = 8000  # Conservative limit for text-embedding-3-small
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars]
            logger.warning(f"Truncated text from {len(text)} to {max_chars} characters")
        
        return cleaned
    
    def estimate_cost(self, texts: List[str]) -> Dict[str, Any]:
        """Estimate the cost of generating embeddings for given texts."""
        total_chars = sum(len(text) for text in texts)
        # Approximate tokens (1 token ≈ 4 characters for English)
        estimated_tokens = total_chars / 4
        
        # text-embedding-3-small pricing: $0.02 per 1M tokens
        cost_per_token = 0.02 / 1_000_000
        estimated_cost = estimated_tokens * cost_per_token
        
        return {
            "total_texts": len(texts),
            "total_characters": total_chars,
            "estimated_tokens": int(estimated_tokens),
            "estimated_cost_usd": round(estimated_cost, 6),
            "model": self.model
        }
    
    def test_connection(self) -> bool:
        """Test connection to OpenAI API."""
        try:
            test_embedding = self.generate_query_embedding("test connection")
            return len(test_embedding) == 1536
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False 