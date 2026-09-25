"""Tests for the Part 1 minimal RAG capability."""
import pytest
from fastapi.testclient import TestClient

def test_rag_supported_question_wfh(client: TestClient):
    """Case A — supported question (WFH)."""
    response = client.post("/rag/ask", json={"question": "What is the remote work policy?"})
    assert response.status_code == 200
    data = response.json()
    assert "Based on the provided policy evidence" in data["answer"]
    assert "remote" in data["answer"].lower()
    assert len(data["citations"]) > 0
    citation = data["citations"][0]
    assert citation["policy_id"] == "POL-WFH-01"
    assert citation["source_id"] == "POL-WFH-01.md"

def test_rag_supported_question_sick(client: TestClient):
    """Case B — another supported question (Sick leave)."""
    response = client.post("/rag/ask", json={"question": "How many sick days do I get?"})
    assert response.status_code == 200
    data = response.json()
    assert "Based on the provided policy evidence" in data["answer"]
    assert "sick" in data["answer"].lower()
    assert len(data["citations"]) > 0
    citation = data["citations"][0]
    assert citation["policy_id"] == "POL-LEAVE-02"
    assert citation["source_id"] == "POL-LEAVE-02.md"

def test_rag_unsupported_question(client: TestClient):
    """Case C — unsupported question."""
    response = client.post("/rag/ask", json={"question": "Can I bring my pet iguana to the office?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "I'm sorry, I couldn't find sufficient approved policy evidence to answer your question."
    assert len(data["citations"]) == 0
