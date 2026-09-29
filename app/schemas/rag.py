from typing import List, Optional, Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Part 2: Processed Knowledge / Corpus Structures
# ---------------------------------------------------------

class PolicyMetadata(BaseModel):
    policy_id: str
    title: str
    policy_type: str
    version: str
    status: str
    source: str
    jurisdiction: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    provenance: Optional[str] = None

class ParsedSection(BaseModel):
    heading: str
    level: int
    content: str
    subsections: List["ParsedSection"] = []

class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: PolicyMetadata
    section: str
    source_id: str
    chunking_strategy: str = "fixed" # 'fixed', 'recursive', or 'structure-aware'

class ParsedDocument(BaseModel):
    source_id: str
    metadata: PolicyMetadata
    cleaned_content: str
    sections: List[ParsedSection]
    chunks: List[DocumentChunk] = []

# ---------------------------------------------------------
# Part 1 Integration / Compatibility
# ---------------------------------------------------------

class PolicyEvidence(BaseModel):
    """
    Representation of retrieved policy evidence with preserved identity.
    (Kept for Part 1 compatibility)
    """
    content: str
    source_id: str
    policy_id: str
    version: str
    section: str

    @classmethod
    def from_chunk(cls, chunk: DocumentChunk) -> "PolicyEvidence":
        return cls(
            content=chunk.content,
            source_id=chunk.source_id,
            policy_id=chunk.metadata.policy_id,
            version=chunk.metadata.version,
            section=chunk.section
        )

class Citation(BaseModel):
    """
    Citation linking an answer to a specific policy source.
    """
    source_id: str
    policy_id: str
    section: str
    snippet: Optional[str] = None

class MetadataFilters(BaseModel):
    """Optional filters to apply during retrieval."""
    jurisdiction: Optional[str] = None
    status: Optional[str] = None
    policy_type: Optional[str] = None
    policy_id: Optional[str] = None
    version: Optional[str] = None

class RagRequest(BaseModel):
    """
    Request payload for asking a policy question.
    """
    question: str = Field(..., description="The policy question to answer.")
    filters: Optional[MetadataFilters] = Field(None, description="Optional metadata constraints for retrieval.")

class RagResponse(BaseModel):
    """
    Response payload containing the generated answer and supporting citations.
    """
    answer: str
    citations: List[Citation]
