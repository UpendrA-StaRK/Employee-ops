from typing import List

def calculate_recall_at_k(expected_ids: List[str], retrieved_ids: List[str], k: int) -> float:
    if not expected_ids:
        return 1.0  # If nothing expected, and we retrieved anything/nothing, recall is nominally 1.0 (or undefined; we treat as 1.0)
    retrieved_k = retrieved_ids[:k]
    matches = set(expected_ids).intersection(set(retrieved_k))
    return len(matches) / len(expected_ids)

def calculate_precision_at_k(expected_ids: List[str], retrieved_ids: List[str], k: int) -> float:
    retrieved_k = retrieved_ids[:k]
    if not retrieved_k:
        return 1.0 if not expected_ids else 0.0
    matches = set(expected_ids).intersection(set(retrieved_k))
    return len(matches) / len(retrieved_k)

def calculate_mrr(expected_ids: List[str], retrieved_ids: List[str], k: int) -> float:
    if not expected_ids:
        return 1.0 if not retrieved_ids else 0.0
    
    retrieved_k = retrieved_ids[:k]
    for i, r_id in enumerate(retrieved_k):
        if r_id in expected_ids:
            return 1.0 / (i + 1)
    return 0.0

def evaluate_citations(expected_policy_ids: List[str], generated_citations: List[str]) -> bool:
    """
    Checks if the generated citations match the expected policies.
    """
    if not expected_policy_ids and not generated_citations:
        return True
    if expected_policy_ids and not generated_citations:
        return False
    # Check if any generated citation points to an expected policy
    return any(cit in expected_policy_ids for cit in generated_citations)

def check_no_answer(answerability: str, answer_text: str) -> bool:
    """
    Checks if an unanswerable question yields a no-answer fallback.
    The mock generator says: "I'm sorry, I couldn't find sufficient approved policy evidence to answer your question."
    """
    fallback_phrase = "couldn't find sufficient approved policy evidence"
    if answerability == "unanswerable":
        return fallback_phrase in answer_text
    elif answerability == "answerable":
        return fallback_phrase not in answer_text
    return True
