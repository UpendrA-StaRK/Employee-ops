import pytest
from app.services.policy_ingestion import PolicyIngestionPipeline
from app.schemas.rag import DocumentChunk

@pytest.fixture
def pipeline():
    return PolicyIngestionPipeline()

def test_markdown_parsing(pipeline):
    # Fixed strategy to check simple chunking
    chunks = pipeline.ingest_all(strategy="fixed")
    assert any("WFH" in c.metadata.policy_id for c in chunks)
    wfh_chunks = [c for c in chunks if c.metadata.policy_id == "POL-WFH-01"]
    assert len(wfh_chunks) > 0
    # Check metadata survived
    assert wfh_chunks[0].metadata.title == "Work From Home Policy"
    assert wfh_chunks[0].metadata.status == "active"
    assert wfh_chunks[0].source_id == "POL-WFH-01.md"

def test_docx_parsing(pipeline):
    chunks = pipeline.ingest_all(strategy="structure-aware")
    docx_chunks = [c for c in chunks if c.metadata.policy_id == "POL-TRAVEL-03"]
    assert len(docx_chunks) > 0
    # Check structure preservation
    assert any(c.section == "1. Purpose" for c in docx_chunks)

def test_pdf_parsing(pipeline):
    chunks = pipeline.ingest_all(strategy="recursive")
    pdf_chunks = [c for c in chunks if c.metadata.policy_id == "POL-EXPENSE-04"]
    assert len(pdf_chunks) > 0
    assert "reimburs" in pdf_chunks[0].content.lower()

def test_structure_aware_chunking_sections(pipeline):
    chunks = pipeline.ingest_all(strategy="structure-aware")
    wfh_chunks = [c for c in chunks if c.metadata.policy_id == "POL-WFH-01"]
    
    # We expect separate chunks for "1. Purpose", "2. Scope and Eligibility", etc.
    sections = [c.section for c in wfh_chunks]
    assert "1. Purpose" in sections
    assert "3. Remote Work Allowances and Hardware" in sections
    
    # Chunk traceability
    assert hasattr(wfh_chunks[0], "chunk_id")
    assert "POL-WFH-01.md" in wfh_chunks[0].chunk_id
    assert wfh_chunks[0].chunking_strategy == "structure-aware"
