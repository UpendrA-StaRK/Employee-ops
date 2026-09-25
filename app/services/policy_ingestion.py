import os
from typing import List
from app.schemas.rag import ParsedDocument, DocumentChunk
from app.services.policy_parser import PolicyParser
from app.services.policy_chunker import PolicyChunker

class PolicyIngestionPipeline:
    """
    Ingestion pipeline for Part 2.
    Discovers source documents, passes them to parser, and applies chunking strategy.
    """
    
    def __init__(self, corpus_dir: str = "data/policies"):
        self.corpus_dir = corpus_dir
        self.parser = PolicyParser()
        self.chunker = PolicyChunker()

    def ingest_all(self, strategy: str = "structure-aware") -> List[DocumentChunk]:
        """
        Ingest all supported documents and return the final processed chunks.
        """
        all_chunks = []
        if not os.path.exists(self.corpus_dir):
            return all_chunks

        for filename in os.listdir(self.corpus_dir):
            if filename.endswith((".md", ".docx", ".pdf")):
                filepath = os.path.join(self.corpus_dir, filename)
                try:
                    # 1. Parse
                    parsed_doc = self.parser.parse_file(filepath)
                    
                    # 2. Chunk
                    if strategy == "fixed":
                        chunks = self.chunker.chunk_fixed(parsed_doc)
                    elif strategy == "recursive":
                        chunks = self.chunker.chunk_recursive(parsed_doc)
                    else:
                        chunks = self.chunker.chunk_structure_aware(parsed_doc)
                        
                    parsed_doc.chunks = chunks
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Failed to ingest {filename}: {e}")
                    
        return all_chunks

# Global instance for the retriever to use
ingestion_pipeline = PolicyIngestionPipeline()
# Load knowledge into memory for Part 2
PROCESSED_KNOWLEDGE = ingestion_pipeline.ingest_all(strategy="structure-aware")
