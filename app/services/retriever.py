"""
Deterministic retrieval mechanism to demonstrate Part 2 RAG flow.
"""
from typing import List
from app.schemas.rag import PolicyEvidence
from app.services.policy_ingestion import PROCESSED_KNOWLEDGE

def retrieve_evidence(question: str) -> List[PolicyEvidence]:
    """
    Simplest deterministic retrieval mechanism.
    Returns relevant approved evidence based on simple keyword matching.
    """
    q_lower = question.lower()
    evidence = []
    
    # Case A: Work from home policy
    if "work from home" in q_lower or "remote" in q_lower or "wfh" in q_lower:
        # Match chunks from the WFH policy
        for chunk in PROCESSED_KNOWLEDGE:
            if "WFH" in chunk.metadata.policy_id:
                evidence.append(PolicyEvidence.from_chunk(chunk))
    
    # Case B: Sick leave policy
    if "sick" in q_lower or "leave" in q_lower:
        # Match chunks from the active leave policy
        for chunk in PROCESSED_KNOWLEDGE:
            if "LEAVE" in chunk.metadata.policy_id and chunk.metadata.status == "active":
                evidence.append(PolicyEvidence.from_chunk(chunk))
                
    # Case C: Expense policy
    if "expense" in q_lower or "reimbursement" in q_lower or "receipt" in q_lower:
        for chunk in PROCESSED_KNOWLEDGE:
            if "EXPENSE" in chunk.metadata.policy_id:
                evidence.append(PolicyEvidence.from_chunk(chunk))
                
    # Deduplicate by section/content just in case
    seen = set()
    unique_evidence = []
    for e in evidence:
        key = f"{e.policy_id}_{e.section}"
        if key not in seen:
            seen.add(key)
            unique_evidence.append(e)
            
    return unique_evidence
