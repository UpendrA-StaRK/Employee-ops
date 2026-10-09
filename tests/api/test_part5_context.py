import pytest
from app.services.context_assembler import context_assembler, estimate_tokens
from app.models.knowledge import PolicyChunkVector
from app.schemas.rag import PolicyEvidence

def test_token_estimation():
    text = "This is five words long."
    # 5 words * 1.3 = 6.5 -> 6
    assert estimate_tokens(text) == 6
    assert estimate_tokens("") == 0

def test_deduplication():
    # Same chunk_id
    c1 = PolicyChunkVector(chunk_id="chunk_1", content="ABC")
    c2 = PolicyChunkVector(chunk_id="chunk_1", content="ABC")
    # Same content, different chunk_id
    c3 = PolicyChunkVector(chunk_id="chunk_2", content="ABC")
    # Distinct
    c4 = PolicyChunkVector(chunk_id="chunk_3", content="XYZ")
    
    candidates = [c1, c2, c3, c4]
    deduped = context_assembler.deduplicate(candidates)
    
    # Should keep c1, drop c2 (same chunk_id).
    # Should drop c3 (same content as c1).
    # Should keep c4.
    assert len(deduped) == 2
    assert deduped[0].chunk_id == "chunk_1"
    assert deduped[1].chunk_id == "chunk_3"

def test_context_budget_enforcement():
    # Set a very low budget
    assembler = type(context_assembler)(max_context_tokens=15)
    
    c1 = PolicyChunkVector(
        chunk_id="c1", 
        content="Short", 
        policy_id="POL-1", 
        source_id="S1", 
        section="1", 
        metadata_json={}
    )
    c2 = PolicyChunkVector(
        chunk_id="c2", 
        content="Also short", 
        policy_id="POL-1", 
        source_id="S1", 
        section="2", 
        metadata_json={}
    )
    c3 = PolicyChunkVector(
        chunk_id="c3", 
        content="This one is a bit longer and will exceed the very small budget.", 
        policy_id="POL-1", 
        source_id="S1", 
        section="3", 
        metadata_json={}
    )
    
    candidates = [c1, c2, c3]
    evidence = assembler.assemble(candidates)
    
    # We should get at least 1, maybe 2 depending on overhead, but not all 3
    assert len(evidence) < 3
    assert len(evidence) >= 1
    assert isinstance(evidence[0], PolicyEvidence)
