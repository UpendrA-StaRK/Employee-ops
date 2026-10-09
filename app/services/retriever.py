"""
Hybrid semantic + keyword retrieval mechanism to demonstrate Part 4 RAG flow.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas.rag import PolicyEvidence, MetadataFilters
from app.models.knowledge import PolicyChunkVector
from app.services.embedding import embedding_provider
from app.services.reranker import reranker
from app.services.context_assembler import context_assembler

def _apply_metadata_filters(query, filters: Optional[MetadataFilters]):
    """Applies metadata constraints to a base SQLAlchemy query."""
    if not filters:
        return query
        
    if filters.jurisdiction:
        query = query.filter(PolicyChunkVector.metadata_json.op('->>')('jurisdiction') == filters.jurisdiction)
    if filters.status:
        query = query.filter(PolicyChunkVector.metadata_json.op('->>')('status') == filters.status)
    if filters.policy_type:
        query = query.filter(PolicyChunkVector.metadata_json.op('->>')('policy_type') == filters.policy_type)
    if filters.policy_id:
        query = query.filter(PolicyChunkVector.policy_id == filters.policy_id)
    if filters.version:
        query = query.filter(PolicyChunkVector.metadata_json.op('->>')('version') == filters.version)
        
    return query

def reciprocal_rank_fusion(vector_results, keyword_results, rrf_k=60) -> List[PolicyChunkVector]:
    """
    Merges independent ranked lists using Reciprocal Rank Fusion (RRF).
    RRF score = sum( 1 / (rrf_k + rank_i) )
    """
    scores = {}
    records = {}
    
    # Process vector ranks
    for rank, (record, _) in enumerate(vector_results):
        scores[record.chunk_id] = scores.get(record.chunk_id, 0.0) + 1.0 / (rrf_k + rank + 1)
        records[record.chunk_id] = record
        
    # Process keyword ranks
    for rank, (record, _) in enumerate(keyword_results):
        scores[record.chunk_id] = scores.get(record.chunk_id, 0.0) + 1.0 / (rrf_k + rank + 1)
        records[record.chunk_id] = record
        
    # Sort by descending RRF score
    sorted_chunk_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    return [records[cid] for cid in sorted_chunk_ids]

def retrieve_evidence(
    db: Session, 
    question: str, 
    filters: Optional[MetadataFilters] = None,
    top_k: int = 3, 
    max_distance: float = 0.7,
    strategy: str = "hybrid_rerank"
) -> List[PolicyEvidence]:
    """
    Retrieval mechanism supporting multiple strategies for evaluation comparison.
    Strategies:
      - 'vector': Part 3 vector-only baseline
      - 'hybrid': Part 4 vector + keyword RRF
      - 'hybrid_rerank': Part 5 RRF + Cross-Encoder reranking + Context assembly
    """
    # Number of candidates to pull from each sub-query before fusion
    candidate_k = max(top_k * 2, 10)
    
    # ---------------------------------------------------------
    # Path 1: Vector Retrieval (Semantic)
    # ---------------------------------------------------------
    query_vector = embedding_provider.embed_text(question)
    distance_col = PolicyChunkVector.embedding.cosine_distance(query_vector)
    
    vec_base_query = db.query(PolicyChunkVector, distance_col.label('distance')).filter(
        distance_col < max_distance
    )
    vec_filtered_query = _apply_metadata_filters(vec_base_query, filters)
    
    vector_results = vec_filtered_query.order_by(distance_col).limit(candidate_k).all()
    
    # ---------------------------------------------------------
    # Path 2: Keyword Retrieval (PostgreSQL FTS)
    # ---------------------------------------------------------
    # plainto_tsquery transforms a natural language string into an AND-ed keyword query
    ts_query = func.plainto_tsquery('english', question)
    rank_col = func.ts_rank(PolicyChunkVector.fts_document, ts_query)
    
    fts_base_query = db.query(PolicyChunkVector, rank_col.label('rank')).filter(
        PolicyChunkVector.fts_document.op('@@')(ts_query)
    )
    fts_filtered_query = _apply_metadata_filters(fts_base_query, filters)
    
    # Only return matches with positive relevance
    keyword_results = fts_filtered_query.filter(rank_col > 0).order_by(rank_col.desc()).limit(candidate_k).all()
    
    # ---------------------------------------------------------
    # Result Fusion (RRF)
    # ---------------------------------------------------------
    fused_records = reciprocal_rank_fusion(vector_results, keyword_results)
    
    if strategy == "vector":
        final_records = vector_results[:top_k]
        # Remove the score tuple from vector_results which returns (record, distance)
        final_records = [r[0] for r in final_records]
    elif strategy == "hybrid":
        final_records = fused_records[:top_k]
    else:
        # ---------------------------------------------------------
        # Part 5: Cross-Encoder Reranking
        # ---------------------------------------------------------
        # Take a larger pool of RRF candidates for reranking (e.g., top 20)
        rerank_pool = fused_records[:max(top_k * 3, 20)]
        
        reranked = reranker.rerank(
            query=question,
            candidates=rerank_pool,
            get_text_func=lambda c: c.content
        )
        
        # Extract candidates in reranked order
        reranked_records = [candidate for candidate, score in reranked]
        
        # ---------------------------------------------------------
        # Part 5: Context Assembly
        # ---------------------------------------------------------
        # deduplicate, apply budget, and format to PolicyEvidence
        return context_assembler.assemble(reranked_records)
        
    # Map retrieved records back to PolicyEvidence representation for non-assembly strategies
    evidence = []
    for record in final_records:
        version = record.metadata_json.get("version", "1.0")
        
        evidence.append(PolicyEvidence(
            content=record.content,
            source_id=record.source_id,
            policy_id=record.policy_id,
            version=version,
            section=record.section,
            chunk_id=record.chunk_id
        ))
            
    return evidence
