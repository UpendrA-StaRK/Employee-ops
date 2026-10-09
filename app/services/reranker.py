"""
Local Cross-Encoder Reranker using ms-marco-MiniLM-L-6-v2.
"""
from typing import List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            logger.info(f"Loading reranker model {self.model_name} on CPU")
            try:
                from sentence_transformers import CrossEncoder
                # Using CPU to ensure compatibility across generic environments, 
                # can be adapted to GPU if torch.cuda.is_available() is checked.
                self._model = CrossEncoder(self.model_name, device="cpu")
                logger.info("Reranker model loaded successfully.")
            except ImportError as e:
                logger.error("Failed to import sentence_transformers for reranking.")
                raise e

    def rerank(self, query: str, candidates: List[Any], get_text_func) -> List[Tuple[Any, float]]:
        """
        Reranks a list of candidates against a query.
        
        Args:
            query: The user question.
            candidates: A list of candidate objects.
            get_text_func: A function to extract the text to score from a candidate.
            
        Returns:
            A list of tuples (candidate, score) sorted by score descending.
        """
        if not candidates:
            return []
            
        self._load_model()
        
        # Prepare question-candidate pairs
        pairs = [[query, get_text_func(candidate)] for candidate in candidates]
        
        # Score pairs
        scores = self._model.predict(pairs)
        
        # Zip candidates with scores and sort descending
        scored_candidates = list(zip(candidates, scores))
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return scored_candidates

# Singleton instance
reranker = Reranker()
