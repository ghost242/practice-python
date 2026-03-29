from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence

from langchain_core.documents import Document

from practice_files.practice_llm.rag.types import (
    ChunkingResult,
    ProcessResult,
    SemanticChunk,
)
from practice_files.practice_llm.rag.extract_keywords import (
    BaseKeywordExtractor,
    enrich_chunks_with_keywords,
)
from practice_files.practice_llm.rag.semantic_chunk import (
    IncrementalSemanticChunker,
    build_retrieval_views,
    semantic_chunks_to_documents,
)


def build_chunks(
    *,
    text: Optional[str] = None,
    documents: Optional[Iterable[Document]] = None,
    chunker: IncrementalSemanticChunker,
    return_decisions: bool = False,
) -> ChunkingResult:
    """
    Build semantic chunks from raw text or LangChain documents.

    Exactly one of `text` or `documents` must be provided.
    """
    _validate_exactly_one_source(text=text, documents=documents)

    if text is not None:
        result = chunker.chunk_text(text, return_decisions=return_decisions)
    else:
        result = chunker.chunk_documents(
            list(documents or []),
            return_decisions=return_decisions,
        )

    if return_decisions:
        chunks, decisions = result
        return ChunkingResult(
            chunks=list(chunks),
            decisions=list(decisions),
        )

    return ChunkingResult(
        chunks=list(result),
        decisions=None,
    )


def add_keywords(
    chunks: Sequence[SemanticChunk],
    *,
    extractor: BaseKeywordExtractor,
    top_k: int = 5,
) -> List[SemanticChunk]:
    """
    Enrich existing semantic chunks with keywords.
    """
    return enrich_chunks_with_keywords(
        list(chunks),
        extractor=extractor,
        top_k=top_k,
    )


def build_chunks_with_keywords(
    *,
    text: Optional[str] = None,
    documents: Optional[Iterable[Document]] = None,
    chunker: IncrementalSemanticChunker,
    extractor: BaseKeywordExtractor,
    return_decisions: bool = False,
    top_k: int = 5,
    include_retrieval_views: bool = False,
    include_prev_context: bool = True,
    include_next_context: bool = False,
    include_documents: bool = False,
    include_keyword_metadata_in_documents: bool = True,
) -> ProcessResult:
    """
    Run the common end-to-end pipeline:

        source -> semantic chunks -> keyword enrichment -> optional derived outputs

    Exactly one of `text` or `documents` must be provided.
    """
    chunking_result = build_chunks(
        text=text,
        documents=documents,
        chunker=chunker,
        return_decisions=return_decisions,
    )

    chunks = add_keywords(
        chunking_result.chunks,
        extractor=extractor,
        top_k=top_k,
    )

    retrieval_views = None
    if include_retrieval_views:
        retrieval_views = build_retrieval_views(
            chunks,
            include_prev=include_prev_context,
            include_next=include_next_context,
        )

    out_documents = None
    if include_documents:
        out_documents = build_documents(
            chunks,
            include_keywords=include_keyword_metadata_in_documents,
        )

    return ProcessResult(
        chunks=chunks,
        decisions=chunking_result.decisions,
        retrieval_views=retrieval_views,
        documents=out_documents,
    )


def build_retrieval_ready_chunks(
    *,
    text: Optional[str] = None,
    documents: Optional[Iterable[Document]] = None,
    chunker: IncrementalSemanticChunker,
    extractor: BaseKeywordExtractor,
    return_decisions: bool = False,
    top_k: int = 5,
    include_prev_context: bool = True,
    include_next_context: bool = False,
    include_keyword_metadata_in_documents: bool = True,
) -> ProcessResult:
    """
    Convenience facade for retrieval-oriented processing.
    """
    return build_chunks_with_keywords(
        text=text,
        documents=documents,
        chunker=chunker,
        extractor=extractor,
        return_decisions=return_decisions,
        top_k=top_k,
        include_retrieval_views=True,
        include_prev_context=include_prev_context,
        include_next_context=include_next_context,
        include_documents=True,
        include_keyword_metadata_in_documents=include_keyword_metadata_in_documents,
    )


def build_documents(
    chunks: Sequence[SemanticChunk],
    *,
    include_keywords: bool = True,
) -> List[Document]:
    """
    Convert semantic chunks into LangChain documents.

    This helper exists so facade users do not need to import semantic_chunk.py
    directly for a common conversion step.
    """
    return semantic_chunks_to_documents(
        list(chunks),
        include_keywords=include_keywords,
    )


def build_metadata_updates(
    chunks: Sequence[SemanticChunk],
) -> List[dict[str, Any]]:
    """
    Build DB-agnostic metadata payloads from already-processed chunks.

    This stays generic on purpose. Caller code may sanitize or reshape the
    payload for a specific backend such as Chroma, pgvector, or another store.
    """
    updates: List[dict[str, Any]] = []

    for chunk in chunks:
        metadata = dict(chunk.metadata) if chunk.metadata else {}
        metadata.update(
            {
                "chunk_id": chunk.chunk_id,
                "owned_span": chunk.span_label,
                "unit_ids": chunk.unit_ids,
                "size_units": chunk.size_units,
                "size_chars": chunk.size_chars,
                "main_keyword": chunk.main_keyword,
                "keywords": list(chunk.keywords),
            }
        )
        updates.append(metadata)

    return updates


def _validate_exactly_one_source(
    *,
    text: Optional[str],
    documents: Optional[Iterable[Document]],
) -> None:
    has_text = text is not None
    has_documents = documents is not None

    if has_text == has_documents:
        raise ValueError(
            "Exactly one of `text` or `documents` must be provided."
        )
