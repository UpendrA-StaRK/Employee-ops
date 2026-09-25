"""
Mock generator simulating an LLM generating a grounded answer.
"""
from typing import List
from app.schemas.rag import PolicyEvidence, RagResponse, Citation

def generate_answer(question: str, evidence: List[PolicyEvidence]) -> RagResponse:
    """
    The generator receives:
    - system instructions (implicit in this mock logic)
    - user question
    - retrieved policy evidence
    """
    if not evidence:
        # Controlled no-answer behavior
        return RagResponse(
            answer="I'm sorry, I couldn't find sufficient approved policy evidence to answer your question.",
            citations=[]
        )
    
    # Simulate LLM answering solely based on context
    answer = f"Based on the provided policy evidence, here is the answer to your question regarding '{question}':\n\n"
    citations = []
    
    for doc in evidence:
        answer += f"- {doc.content}\n"
        citations.append(Citation(
            source_id=doc.source_id,
            policy_id=doc.policy_id,
            section=doc.section,
            snippet=doc.content[:50] + "..."
        ))
        
    return RagResponse(
        answer=answer.strip(),
        citations=citations
    )
