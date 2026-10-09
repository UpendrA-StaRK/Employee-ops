import pytest
from app.evaluation.metrics import (
    calculate_recall_at_k,
    calculate_precision_at_k,
    calculate_mrr,
    evaluate_citations,
    check_no_answer
)

def test_calculate_recall_at_k():
    expected = ["chunk_1", "chunk_2"]
    
    # Perfect recall
    assert calculate_recall_at_k(expected, ["chunk_1", "chunk_2", "chunk_3"], k=3) == 1.0
    
    # Partial recall
    assert calculate_recall_at_k(expected, ["chunk_1", "chunk_4"], k=3) == 0.5
    
    # Zero recall
    assert calculate_recall_at_k(expected, ["chunk_3", "chunk_4"], k=3) == 0.0
    
    # K limit cuts off the relevant chunk
    assert calculate_recall_at_k(expected, ["chunk_3", "chunk_4", "chunk_1"], k=2) == 0.0

def test_calculate_precision_at_k():
    expected = ["chunk_1", "chunk_2"]
    
    # Perfect precision (all retrieved up to k are relevant)
    assert calculate_precision_at_k(expected, ["chunk_1", "chunk_2"], k=2) == 1.0
    
    # 1 out of 2 relevant
    assert calculate_precision_at_k(expected, ["chunk_1", "chunk_3"], k=2) == 0.5
    
    # 0 out of 2 relevant
    assert calculate_precision_at_k(expected, ["chunk_3", "chunk_4"], k=2) == 0.0

def test_calculate_mrr():
    expected = ["chunk_1"]
    
    # First place -> MRR = 1.0
    assert calculate_mrr(expected, ["chunk_1", "chunk_2", "chunk_3"], k=3) == 1.0
    
    # Second place -> MRR = 0.5
    assert calculate_mrr(expected, ["chunk_2", "chunk_1", "chunk_3"], k=3) == 0.5
    
    # Third place -> MRR = 0.333...
    assert calculate_mrr(expected, ["chunk_2", "chunk_3", "chunk_1"], k=3) == 1.0 / 3.0
    
    # Not found in top K
    assert calculate_mrr(expected, ["chunk_2", "chunk_3", "chunk_1"], k=2) == 0.0

def test_evaluate_citations():
    expected_policies = ["POL-WFH-01"]
    
    # Valid citation
    assert evaluate_citations(expected_policies, ["POL-WFH-01", "POL-OTHER"]) == True
    
    # Invalid citation
    assert evaluate_citations(expected_policies, ["POL-OTHER"]) == False
    
    # No citations when expected
    assert evaluate_citations(expected_policies, []) == False
    
    # No citations expected, none generated
    assert evaluate_citations([], []) == True

def test_check_no_answer():
    # Answerable -> should NOT contain fallback
    assert check_no_answer("answerable", "Here is the policy: WFH up to 2 days.") == True
    assert check_no_answer("answerable", "I'm sorry, I couldn't find sufficient approved policy evidence to answer your question.") == False
    
    # Unanswerable -> SHOULD contain fallback
    assert check_no_answer("unanswerable", "I'm sorry, I couldn't find sufficient approved policy evidence to answer your question.") == True
    assert check_no_answer("unanswerable", "You can bring dogs to Mars.") == False
