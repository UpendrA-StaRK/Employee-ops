"""
Semantic vector retrieval mechanism to demonstrate Part 3 RAG flow.
"""
from typing import List
from sqlalchemy.orm import Session
from app.schemas.rag import PolicyEvidence
from app.models.knowledge import PolicyChunkVector
from app.services.embedding import embedding_provider

def retrieve_evidence(db: Session, question: str, top_k: int = 3, max_distance: float = 0.7) -> List[PolicyEvidence]:
    """
    Semantic retrieval mechanism using PostgreSQL + pgvector.
    Returns the Top-K chunks based on cosine similarity, filtered by a maximum distance.
    """
    # 1. Embed the user question
    query_vector = embedding_provider.embed_text(question)
    
    # 2. Perform vector similarity search (cosine distance: <=>)
    # Order by cosine distance ascending (closest first) and apply threshold to maintain no-answer behavior
    distance_col = PolicyChunkVector.embedding.cosine_distance(query_vector)
    results = db.query(PolicyChunkVector).filter(
        distance_col < max_distance
    ).order_by(
        distance_col
    ).limit(top_k).all()
    
    # 3. Map retrieved vectors back to the expected PolicyEvidence representation
    evidence = []
    for record in results:
        # Extract version from metadata_json if available
        version = record.metadata_json.get("version", "1.0")
        
        evidence.append(PolicyEvidence(
            content=record.content,
            source_id=record.source_id,
            policy_id=record.policy_id,
            version=version,
            section=record.section
        ))
            
    return evidence
