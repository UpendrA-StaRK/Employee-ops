from typing import List
from sqlalchemy.orm import Session
from app.models.knowledge import PolicyChunkVector
from app.services.embedding import embedding_provider
from app.services.policy_ingestion import PROCESSED_KNOWLEDGE
from app.schemas.rag import DocumentChunk

def index_policy_corpus(db: Session, chunks: List[DocumentChunk] = PROCESSED_KNOWLEDGE):
    """
    Takes the processed chunks from Part 2, embeds them, and saves them to PostgreSQL via pgvector.
    This separates the indexing phase from the query phase.
    """
    # 1. Clear existing vectors for simplicity (in a real app, you'd upsert based on chunk_id)
    db.query(PolicyChunkVector).delete()
    db.commit()

    # 2. Extract texts to embed
    texts_to_embed = [chunk.content for chunk in chunks]
    
    # 3. Generate embeddings in a batch
    embeddings = embedding_provider.embed_batch(texts_to_embed)
    
    # 4. Create and persist PolicyChunkVector records
    vector_records = []
    for chunk, emb in zip(chunks, embeddings):
        record = PolicyChunkVector(
            chunk_id=chunk.chunk_id,
            policy_id=chunk.metadata.policy_id,
            source_id=chunk.source_id,
            section=chunk.section,
            content=chunk.content,
            embedding=emb,
            metadata_json=chunk.metadata.model_dump()
        )
        vector_records.append(record)
        
    db.bulk_save_objects(vector_records)
    db.commit()
    
    return len(vector_records)
