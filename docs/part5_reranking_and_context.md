# Part 5: Reranking + Context Assembly + OKF / Provenance

## Architecture

The policy evidence retrieval pipeline has been updated to include a cross-encoder reranking step and context assembly process. The complete end-to-end pipeline is:

```text
User Question
    ↓
Hybrid retrieval (Vector + FTS merged via RRF)
    ↓
Cross-encoder reranking (Local)
    ↓
Conservative Deduplication
    ↓
Evidence selection
    ↓
Context budget enforcement
    ↓
Controlled context assembly
    ↓
Existing Generation provider
```

## Reranker

- **Exact Model ID**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Model-loading mechanism**: Lazy loaded on the first request and cached as a singleton in memory within the `Reranker` class. 
- **Runtime/device behavior**: Hardcoded to use `device="cpu"` to guarantee compatibility across diverse environments without requiring CUDA.
- **Required dependencies**: `sentence-transformers`, `torch`.
- **Configuration**: The retrieval service passes up to `max(top_k * 3, 20)` candidates to the reranker to ensure sufficient scope for reranking without unbounded memory usage.
- **Meaning and limitations of reranker scores**: The cross-encoder outputs raw logits indicating semantic relevance between the query and candidate chunk. These are not calibrated probabilities (0-1). They are strictly used for sorting candidate chunks descending by relevance.

## Context Assembly

- **Deduplication rules**: 
  - Duplicate `chunk_id`s are dropped to prevent multiple identical chunks from being processed.
  - Exact duplicate `content` is dropped to prevent identical text from appearing multiple times.
  - Complementary sections (distinct chunks belonging to the same policy) are intentionally retained to preserve broader context.
- **Evidence-selection behavior**: Candidates are selected strictly in their reranked order until the context budget is exhausted.
- **Context-budget configuration**: Defaults to 3000 tokens per request. Configurable when instantiating the `ContextAssembler`.
- **Token-counting method**: Since an exact LLM tokenizer may not be available or consistent across generative models, a simple proxy is used (`len(text.split()) * 1.3`).
- **Handling of current and historical policies**: The underlying metadata for versioning, status, and effective dates is preserved and passed to the generation layer, ensuring it can reason correctly about historical versus current policies. The retrieval mechanism relies on filters to omit historical documents unless implicitly needed.

## Provenance and OKF

- **How source identity is preserved**: The `PolicyEvidence` model acts as a carrier through the entire pipeline. Properties like `policy_id`, `version`, `section`, and `source_id` are maintained seamlessly.
- **How policy versions and sections are represented**: Explicitly via properties in `PolicyEvidence`. The `section` column from the vector database is surfaced directly to the generative LLM.
- **Which relationships are supported**: 
  - `policy_id`, `version`, `jurisdiction`, `status`
  - Explicit OKF relations `supersedes` (Optional[str]) and `related_policies` (List[str]) added to `PolicyMetadata` schemas.
- **How relationships are grounded in source data**: Using the existing `metadata_json` column within `PolicyChunkVector`.
- **Which relationships or capabilities remain out of scope**: Graph databases, multi-agent frameworks, ontology representations, and GraphRAG pipelines have been deliberately excluded to prioritize a small, highly effective architecture.
