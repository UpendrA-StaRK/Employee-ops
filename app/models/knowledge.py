"""Knowledge models for pgvector."""
from sqlalchemy import String, Text, JSON, Computed
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.db.session import Base

class PolicyChunkVector(Base):
    """
    SQLAlchemy model for storing policy chunks and their vector embeddings.
    """
    __tablename__ = "policy_chunk_vectors"

    chunk_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    section: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Store the actual text content used for generating the embedding
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # We use 384 dimensions for all-MiniLM-L6-v2
    embedding: Mapped[Vector] = mapped_column(Vector(384), nullable=False)
    
    # Preserve Part 2 metadata in a JSON column for traceability and future filtering
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Full-Text Search Vector (Part 4)
    # Computed column combining policy_id, title, section, and content.
    fts_document = mapped_column(
        postgresql.TSVECTOR,
        Computed(
            "to_tsvector('english', "
            "coalesce(policy_id, '') || ' ' || "
            "coalesce(metadata_json->>'title', '') || ' ' || "
            "coalesce(section, '') || ' ' || "
            "coalesce(content, ''))",
            persisted=True
        ),
        nullable=True
    )
