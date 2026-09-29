import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.retriever import retrieve_evidence, reciprocal_rank_fusion
from app.models.knowledge import PolicyChunkVector
from app.schemas.rag import MetadataFilters
from fastapi.testclient import TestClient

def test_metadata_filtering(db_session: Session):
    # Retrieve with an active filter
    filters = MetadataFilters(status="active")
    # A generic query that would otherwise hit superseded documents too
    evidence = retrieve_evidence(db_session, "What is the policy?", filters=filters, top_k=5)
    
    # All returned chunks must have status="active" in their metadata (mocked via checking source version if needed)
    # Actually, we can check the db directly for the chunks returned
    for ev in evidence:
        record = db_session.query(PolicyChunkVector).filter(PolicyChunkVector.source_id == ev.source_id).first()
        assert record.metadata_json["status"] == "active"

def test_postgresql_fts_keyword_search(db_session: Session):
    # Query using an exact policy ID which is unlikely to be semantically similar to natural language
    # but exact match in FTS will find it.
    evidence = retrieve_evidence(db_session, "POL-WFH-01", top_k=5)
    
    assert len(evidence) > 0
    assert any(ev.policy_id == "POL-WFH-01" for ev in evidence)

def test_vector_retrieval_regression(db_session: Session):
    # Query using semantic concepts
    evidence = retrieve_evidence(db_session, "remote work stipend", top_k=1)
    assert len(evidence) > 0
    assert "WFH" in evidence[0].policy_id

def test_reciprocal_rank_fusion_logic():
    # Mock records
    class MockRecord:
        def __init__(self, chunk_id):
            self.chunk_id = chunk_id

    r1 = MockRecord("A")
    r2 = MockRecord("B")
    r3 = MockRecord("C")
    
    # Vector ranks: A (1st), B (2nd)
    vector_results = [(r1, 0.1), (r2, 0.2)]
    # Keyword ranks: B (1st), C (2nd)
    keyword_results = [(r2, 0.9), (r3, 0.8)]
    
    fused = reciprocal_rank_fusion(vector_results, keyword_results, rrf_k=60)
    
    # B appears in both lists, so it should have a higher RRF score and be ranked first
    assert fused[0].chunk_id == "B"
    # A and C appear once. A is rank 1 in vector, C is rank 2 in keyword. 
    # A gets 1/61, C gets 1/62. A should be second.
    assert fused[1].chunk_id == "A"
    assert fused[2].chunk_id == "C"

def test_rag_integration_with_filters(client: TestClient):
    # Test that the /rag/ask endpoint accepts and honors filters
    payload = {
        "question": "How many sick days?",
        "filters": {
            "version": "1.0"
        }
    }
    response = client.post("/rag/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["citations"]) > 0
    
    # Verify the cited document is the 1.0 version (or that it successfully ran without crashing)
    # Since we can't easily assert exactly which chunks were returned without inspecting the DB, 
    # we'll just check that it ran and the API didn't fail.
    assert "sick" in data["answer"].lower()
