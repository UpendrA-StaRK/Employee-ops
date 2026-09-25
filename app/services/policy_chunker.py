from typing import List
from app.schemas.rag import ParsedDocument, DocumentChunk

class PolicyChunker:
    """
    Implements three chunking strategies: Fixed, Recursive, and Structure-Aware.
    """
    
    def chunk_fixed(self, doc: ParsedDocument, chunk_size: int = 150) -> List[DocumentChunk]:
        """
        Straightforward size-based strategy.
        """
        chunks = []
        text = doc.cleaned_content
        for i in range(0, len(text), chunk_size):
            content = text[i:i+chunk_size]
            chunks.append(DocumentChunk(
                chunk_id=f"{doc.source_id}_fixed_{i}",
                content=content.strip(),
                metadata=doc.metadata,
                section="Entire Document",
                source_id=doc.source_id,
                chunking_strategy="fixed"
            ))
        return chunks

    def chunk_recursive(self, doc: ParsedDocument, chunk_size: int = 150) -> List[DocumentChunk]:
        """
        Progressively uses meaningful boundaries (paragraphs, sentences) to respect size constraints.
        """
        chunks = []
        paragraphs = doc.cleaned_content.split('\n\n')
        
        current_chunk_text = ""
        chunk_idx = 0
        
        for para in paragraphs:
            if len(current_chunk_text) + len(para) <= chunk_size:
                current_chunk_text += para + "\n\n"
            else:
                # If adding para exceeds size, save current chunk and start new
                if current_chunk_text.strip():
                    chunks.append(self._create_chunk(doc, current_chunk_text, chunk_idx, "recursive"))
                    chunk_idx += 1
                
                # If para itself is larger than chunk size, split by sentences (simplified)
                if len(para) > chunk_size:
                    sentences = para.replace(". ", ".\n").split('\n')
                    for sent in sentences:
                        chunks.append(self._create_chunk(doc, sent, chunk_idx, "recursive"))
                        chunk_idx += 1
                    current_chunk_text = ""
                else:
                    current_chunk_text = para + "\n\n"
                    
        if current_chunk_text.strip():
            chunks.append(self._create_chunk(doc, current_chunk_text, chunk_idx, "recursive"))
            
        return chunks

    def chunk_structure_aware(self, doc: ParsedDocument) -> List[DocumentChunk]:
        """
        Primary practical approach. Uses actual document structure (sections) to chunk.
        Because policy structure carries meaning.
        """
        chunks = []
        chunk_idx = 0
        
        # If no sections could be parsed, fallback to treating the whole doc as one section
        if not doc.sections:
            return [self._create_chunk(doc, doc.cleaned_content, chunk_idx, "structure-aware", section="Entire Document")]
            
        for sec in doc.sections:
            chunks.append(DocumentChunk(
                chunk_id=f"{doc.source_id}_struct_{chunk_idx}",
                content=sec.content,
                metadata=doc.metadata,
                section=sec.heading,
                source_id=doc.source_id,
                chunking_strategy="structure-aware"
            ))
            chunk_idx += 1
            
        return chunks

    def _create_chunk(self, doc: ParsedDocument, content: str, idx: int, strategy: str, section: str = "Various") -> DocumentChunk:
        return DocumentChunk(
            chunk_id=f"{doc.source_id}_{strategy[:4]}_{idx}",
            content=content.strip(),
            metadata=doc.metadata,
            section=section,
            source_id=doc.source_id,
            chunking_strategy=strategy
        )
