# Study Notes: Modern RAG Implementation

## 1. Vector Database: pgvector vs FAISS

Our Week 3 RAG implementation uses **`pgvector`** (an extension for PostgreSQL) as the vector database rather than FAISS, Qdrant, or Chroma.

### Evidence
- **Dependencies**: `pyproject.toml` explicitly includes `pgvector>=0.5.0` and `sqlalchemy>=2.0.36`.
- **Data Model**: `app/models/knowledge.py` maps the `Vector` type from `pgvector.sqlalchemy` to a native PostgreSQL column (`embedding = mapped_column(Vector(384))`).
- **Retrieval Logic**: `app/services/retriever.py` queries this model using native SQLAlchemy distance operators (`PolicyChunkVector.embedding.cosine_distance(query_vector)`).

### Why pgvector Was Chosen
It prioritizes **architectural simplicity and data consolidation**. By keeping vectors in PostgreSQL, the application avoids the operational overhead of a separate dedicated vector database. It seamlessly enables **hybrid retrieval**: performing semantic vector search, strict metadata filtering (e.g., `status`, `jurisdiction`), and native PostgreSQL Full-Text Search simultaneously within the same transactional boundary.

### How It Performs Vector Retrieval
The application embeds the query text (using `all-MiniLM-L6-v2`) and passes the 384-dimensional vector to PostgreSQL. `pgvector` computes the distance (e.g., cosine distance via the `<=>` operator) between the query vector and all chunk embeddings natively in the database, returning the most relevant records.

### Comparison with FAISS
- **Architecture:** FAISS (Facebook AI Similarity Search) is primarily a standalone C++ library built for ultra-fast, massive-scale nearest-neighbor search. `pgvector` is a PostgreSQL extension that integrates vectors into a relational database.
- **Relational Capabilities:** FAISS has no concept of relational schemas, ACID transactions, or robust metadata filtering. Using FAISS typically requires a "dual-store" architecture (FAISS for vectors, PostgreSQL for metadata). `pgvector` handles both, allowing SQL queries to filter on metadata alongside vector search.
- **Performance Trade-offs:** FAISS is strictly optimized for performance and is faster/more memory-efficient for hundreds of millions of vectors. For smaller, enterprise-scale RAG applications, `pgvector`'s performance is excellent and strongly favors operational simplicity.

---

## 2. Local Reranker Implementation (Cross-Encoder)

*Reference: `app/services/reranker.py`*

The cross-encoder is lazy-loaded to prevent blocking application startup and is configured to run on CPU for maximum environment compatibility.

```python
"""
Local Cross-Encoder Reranker using ms-marco-MiniLM-L-6-v2.
"""
from typing import List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            logger.info(f"Loading reranker model {self.model_name} on CPU")
            try:
                from sentence_transformers import CrossEncoder
                # Using CPU to ensure compatibility across generic environments, 
                # can be adapted to GPU if torch.cuda.is_available() is checked.
                self._model = CrossEncoder(self.model_name, device="cpu")
                logger.info("Reranker model loaded successfully.")
            except ImportError as e:
                logger.error("Failed to import sentence_transformers for reranking.")
                raise e
```

---

## 3. Evaluation & Failure Analysis (Part 6)

In this part, we implemented a custom, lightweight Python evaluation runner to benchmark retrieval strategies and compute relevance metrics without coupling to external frameworks like RAGAS.

### Work Done (Brief Definition)
- **Evaluation Runner**: Built a CLI runner (`app.evaluation.runner`) to execute predefined queries against the local `pgvector` database and the mock generator.
- **Metrics Calculated**:
  - **Recall@K**: % of expected ground-truth chunks successfully retrieved.
  - **Precision@K**: % of retrieved chunks that were actually relevant.
  - **MRR (Mean Reciprocal Rank)**: Penalizes systems that retrieve relevant evidence but bury it low in the ranking.
- **Diagnostics**: Validated that the generator's citations match the expected policy IDs and that it properly handles unanswerable questions.
- **Outputs**: Generated a `scorecard.json` containing aggregated averages and a `failure_log.json` for debugging hallucinations or retrieval misses.

### Commands to Run

**1. Run the Evaluation Runner** (Generates scorecard & log):
```bash
uv run python -m app.evaluation.runner
```

**2. Execute the Metric Unit Tests**:
```bash
uv run pytest tests/evaluation/
```
