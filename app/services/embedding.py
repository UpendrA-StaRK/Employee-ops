from typing import List
from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer

class EmbeddingProvider(ABC):
    """
    Abstract interface for generating embeddings.
    Allows swapping out models without rewriting RAG logic.
    """
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embed a single piece of text."""
        pass
        
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts for indexing."""
        pass
        
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality."""
        pass


class SentenceTransformerProvider(EmbeddingProvider):
    """
    Local embedding provider using SentenceTransformers.
    Chosen model: all-MiniLM-L6-v2 (fast, 384 dimensions, great for CPU).
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
    def embed_text(self, text: str) -> List[float]:
        # Encode returns a numpy array, convert to list of floats for pgvector
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()
        
    @property
    def dimension(self) -> int:
        # MiniLM-L6-v2 has 384 dimensions
        return 384

# Global instance for dependency injection / reuse
embedding_provider = SentenceTransformerProvider()
