import pytest
from sqlalchemy.orm import Session
from app.services.embedding import embedding_provider
from app.services.retriever import retrieve_evidence
from app.services.vector_indexing import index_policy_corpus
from app.models.knowledge import PolicyChunkVector
from sqlalchemy import text

def test_embedding_provider_initializes():
    assert embedding_provider.dimension == 384
    
def test_embedding_generation():
    text = "Work from home allowance"
    vector = embedding_provider.embed_text(text)
    assert len(vector) == 384
    assert isinstance(vector[0], float)

def test_vector_storage(db_session: Session):
    # Verify storage
    count = db_session.query(PolicyChunkVector).count()
    assert count > 0
    
    # Verify metadata and dimensionality
    record = db_session.query(PolicyChunkVector).first()
    assert record.chunk_id is not None
    assert record.policy_id is not None
    assert len(record.embedding) == 384
    assert isinstance(record.metadata_json, dict)

def test_semantic_retrieval_and_top_k(db_session: Session):
    # Semantic query that doesn't exactly match the keyword but implies "Work from home"
    query = "remote job location equipment stipend"
    evidence = retrieve_evidence(db_session, query, top_k=2)
    
    assert len(evidence) <= 2
    # Should retrieve the WFH policy
    assert any("WFH" in e.policy_id for e in evidence)

def test_unrelated_query(db_session: Session):
    # A completely unrelated query might still return *something* because cosine similarity always ranks everything.
    # However, for testing, we just check that it doesn't crash and respects top_K.
    query = "recipe for chocolate chip cookies"
    evidence = retrieve_evidence(db_session, query, top_k=3)
    assert len(evidence) <= 3
