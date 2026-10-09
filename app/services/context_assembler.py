"""
Context Assembly for RAG.
Handles deduplication, context budgeting, and structured formatting.
"""
from typing import List, Dict, Any, Set
from app.schemas.rag import PolicyEvidence, DocumentChunk
from app.models.knowledge import PolicyChunkVector
import logging

logger = logging.getLogger(__name__)

def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count (using a conservative 1.3 tokens per word).
    Does not replace a proper tokenizer, but serves as a simple proxy for the budget.
    """
    if not text:
        return 0
    return int(len(text.split()) * 1.3)

class ContextAssembler:
    def __init__(self, max_context_tokens: int = 3000):
        # We set a context budget (default 3000 tokens)
        self.max_context_tokens = max_context_tokens

    def deduplicate(self, candidates: List[PolicyChunkVector]) -> List[PolicyChunkVector]:
        """
        Conservative deduplication:
        - Removes duplicate chunk_ids.
        - Removes exact content duplicates to avoid redundancy.
        - Preserves complementary policy evidence (different sections/chunks).
        """
        seen_chunk_ids = set()
        seen_contents = set()
        deduped = []
        
        for candidate in candidates:
            # Check for chunk_id duplication
            if candidate.chunk_id in seen_chunk_ids:
                continue
                
            # Check for exact text duplication
            if candidate.content in seen_contents:
                continue
                
            seen_chunk_ids.add(candidate.chunk_id)
            seen_contents.add(candidate.content)
            deduped.append(candidate)
            
        return deduped

    def assemble(self, reranked_candidates: List[PolicyChunkVector]) -> List[PolicyEvidence]:
        """
        Takes reranked candidates, deduplicates, applies the context budget, 
        and maps them to structured PolicyEvidence representations (which include OKF relationships).
        """
        # 1. Deduplicate
        unique_candidates = self.deduplicate(reranked_candidates)
        
        # 2. Enforce context budget & create structured representation
        selected_evidence = []
        current_tokens = 0
        
        for candidate in unique_candidates:
            version = candidate.metadata_json.get("version", "1.0")
            jurisdiction = candidate.metadata_json.get("jurisdiction")
            status = candidate.metadata_json.get("status")
            
            evidence_item = PolicyEvidence(
                content=candidate.content,
                source_id=candidate.source_id,
                policy_id=candidate.policy_id,
                version=version,
                section=candidate.section,
                chunk_id=candidate.chunk_id
            )
            
            # The context budget should account for the rendered evidence text + metadata overhead
            # We approximate the overhead by serializing the evidence item
            item_text = f"Policy: {evidence_item.policy_id} (Version: {version})\nSection: {evidence_item.section}\nContent: {evidence_item.content}"
            item_tokens = estimate_tokens(item_text)
            
            if current_tokens + item_tokens <= self.max_context_tokens:
                selected_evidence.append(evidence_item)
                current_tokens += item_tokens
            else:
                # We have reached our context budget, stop adding more evidence
                logger.info(f"Context budget reached ({current_tokens} tokens). Omitting further candidates.")
                break
                
        return selected_evidence

context_assembler = ContextAssembler()
