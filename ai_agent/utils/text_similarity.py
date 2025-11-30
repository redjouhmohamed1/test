"""
Text similarity utilities for semantic search
"""

import numpy as np
from typing import Optional, List
import logging


class TextSimilarity:
    """Simple text similarity using basic embeddings"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.initialized = False
    
    async def initialize(self):
        """Initialize the similarity model"""
        # In a real implementation, you might load a sentence transformer model
        # For now, we'll use a simple approach
        self.initialized = True
        self.logger.info("Text similarity initialized")
    
    async def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text (simplified implementation)"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Simple word-based embedding (in practice, use sentence-transformers)
            words = text.lower().split()
            if not words:
                return None
            
            # Create a simple hash-based embedding
            embedding = np.zeros(100)  # 100-dimensional embedding
            
            for i, word in enumerate(words[:50]):  # Limit to 50 words
                # Simple hash-based feature
                hash_val = hash(word) % 100
                embedding[hash_val] += 1.0 / (i + 1)  # Position weighting
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return None
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            embedding2_array = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(embedding1, embedding2_array)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2_array)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0