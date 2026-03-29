from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Sequence, TypeVar, Tuple

import chromadb
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from practice_files.practice_llm.rag.extract_keywords import (
    LLMKeywordExtractor,
)
from practice_files.practice_llm.rag.semantic_chunk import (
    IncrementalSemanticChunker,
    LocalEmbedder,
    print_full_pipeline_report,
)
from practice_files.practice_llm.rag.text_processor import (
    build_chunks,
    build_chunks_with_keywords,
    build_documents,
)
from practice_files.practice_llm.rag.types import (
    ChunkingResult,
    ProcessResult,
    SemanticChunk,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


def batched(items: Sequence[T], batch_size: int):
    for start in range(0, len(items), batch_size):
        end = min(start + batch_size, len(items))
        yield start, end, items[start:end]


def add_documents_in_batches(
    vector_store: Chroma,
    documents: Sequence[Document],
    ids: Sequence[str],
    *,
    batch_size: int = 5000,
) -> None:
    if len(documents) != len(ids):
        raise ValueError("documents and ids must have the same length")

    total = len(documents)
    logger.info(
        "Uploading %d documents to Chroma in batches of %d",
        total,
        batch_size,
    )

    for start, end, batch_docs in batched(documents, batch_size):
        batch_ids = list(ids[start:end])
        logger.info(
            "Uploading batch %d:%d (%d documents)",
            start,
            end,
            len(batch_docs),
        )
        vector_store.add_documents(list(batch_docs), ids=batch_ids)

    logger.info("Completed initial Chroma upload")


def update_metadatas_in_batches(
    collection: Any,
    metadatas: Sequence[dict[str, Any]],
    ids: Sequence[str],
    *,
    batch_size: int = 5000,
) -> None:
    if len(metadatas) != len(ids):
        raise ValueError("metadatas and ids must have the same length")

    total = len(metadatas)
    logger.info(
        "Updating metadata for %d Chroma records in batches of %d",
        total,
        batch_size,
    )

    for start, end, batch_metadatas in batched(metadatas, batch_size):
        batch_ids = list(ids[start:end])
        logger.info(
            "Updating metadata batch %d:%d (%d records)",
            start,
            end,
            len(batch_metadatas),
        )
        collection.update(ids=batch_ids, metadatas=list(batch_metadatas))

    logger.info("Completed Chroma metadata updates")


def load_pdf_pages(
    pdf_path: Path,
    *,
    page_range: tuple[int, int] | None = None,
) -> list[Document]:
    logger.info("Loading PDF pages from %s", pdf_path)
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    logger.info("Loaded %d total PDF pages", len(docs))

    if page_range is None:
        return docs

    start_page, end_page = page_range
    filtered = [
        doc
        for doc in docs
        if start_page <= doc.metadata.get("page", -1) < end_page
    ]
    logger.info(
        "Kept %d content pages after filtering with range [%d, %d)",
        len(filtered),
        start_page,
        end_page,
    )
    return filtered


def build_chunk_ids(prefix: str, size: int) -> list[str]:
    return [f"{prefix}-{index}" for index in range(1, size + 1)]


def sanitize_metadata_for_chroma(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Keep this DB-specific helper in the ingestion script, not in the facade.
    """
    out: dict[str, Any] = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            out[key] = value
            continue

        if isinstance(value, (list, tuple)):
            if len(value) == 0:
                continue
            out[key] = json.dumps(value, ensure_ascii=False)
            continue

        if isinstance(value, dict):
            if len(value) == 0:
                continue
            out[key] = json.dumps(value, ensure_ascii=False)
            continue

        out[key] = str(value)

    return out


def build_chroma_metadata_updates(
    chunks: Sequence[SemanticChunk],
) -> list[dict[str, Any]]:
    """
    Build Chroma update payloads from facade result objects.

    This stays in load_pdf.py because it is DB-specific behavior.
    """
    updates: list[dict[str, Any]] = []

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
        updates.append(sanitize_metadata_for_chroma(metadata))

    return updates


def build_pdf(
    pdf_path,
    *,
    page_range: Tuple[int, int] | None = None,
    persist_dir="",
    collection_name="",
    provider_url="",
    enable_keywords=False,
    print_report=False,
) -> None:
    if page_range is None:
        page_range = (0, -1)

    batch_size = 5000

    logger.info("Starting PDF ingestion pipeline")
    logger.info("PDF path: %s", pdf_path)
    logger.info("Target page range: [%d, %d)", page_range[0], page_range[1])

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    content_pages = load_pdf_pages(pdf_path, page_range=page_range)

    logger.info(
        "Initializing embedding model: %s",
        "nomic-embed-text-v2-moe:latest",
    )
    embedder = LocalEmbedder(
        model="nomic-embed-text-v2-moe:latest",
        base_url=provider_url,
    )

    logger.info("Initializing semantic chunker")
    chunker = IncrementalSemanticChunker(
        embedder,
        low_threshold=0.62,
        high_threshold=0.82,
        max_chunk_chars=900,
        max_chunk_units=4,
        max_score_drop=0.12,
    )

    if enable_keywords:
        logger.info("Initializing keyword extractor: %s", "llama3.2:3b")
        keyword_extractor = LLMKeywordExtractor(
            model="llama3.2:3b",
            base_url=provider_url,
            temperature=0.0,
        )

        logger.info("Running text processor with keyword enrichment")
        process_result: ProcessResult = build_chunks_with_keywords(
            documents=content_pages,
            chunker=chunker,
            extractor=keyword_extractor,
            return_decisions=True,
            top_k=6,
            include_documents=True,
            include_keyword_metadata_in_documents=True,
        )

        chunks = process_result.chunks
        decisions = process_result.decisions or []
        chunk_docs = list(process_result.documents or [])

    else:
        logger.info("Running text processor without keyword enrichment")
        chunking_result: ChunkingResult = build_chunks(
            documents=content_pages,
            chunker=chunker,
            return_decisions=True,
        )

        chunks = chunking_result.chunks
        decisions = chunking_result.decisions or []
        chunk_docs = build_documents(
            chunks,
            include_keywords=False,
        )

    logger.info(
        "Built %d semantic chunks from %d pages",
        len(chunks),
        len(content_pages),
    )
    logger.info("Recorded %d merge/split decisions", len(decisions))

    if print_report:
        logger.info("Printing pipeline report")
        print_full_pipeline_report(
            chunks,
            decisions=decisions,
            show_split_chunks=True,
        )

    ids = build_chunk_ids("chunk", len(chunks))
    logger.info(
        "Prepared %d chunk documents for vector storage",
        len(chunk_docs),
    )

    logger.info("Opening persistent Chroma client at %s", persist_dir)
    client = chromadb.PersistentClient(path=persist_dir)

    logger.info("Opening Chroma collection: %s", collection_name)
    vector_store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embedder.client,
    )

    logger.info("Adding semantic chunks to Chroma")
    add_documents_in_batches(
        vector_store,
        chunk_docs,
        ids,
        batch_size=batch_size,
    )
    logger.info(
        "Stored %d semantic chunks in Chroma collection '%s'",
        len(chunk_docs),
        collection_name,
    )

    if enable_keywords:
        logger.info("Preparing Chroma metadata updates from processed chunks")
        metadata_updates = build_chroma_metadata_updates(chunks)

        logger.info("Updating stored Chroma metadata with extracted keywords")
        update_metadatas_in_batches(
            vector_store._collection,
            metadata_updates,
            ids,
            batch_size=batch_size,
        )
        logger.info(
            "Updated Chroma metadata for %d semantic chunks",
            len(metadata_updates),
        )
    else:
        logger.info("Keyword extraction is disabled")

    logger.info("PDF ingestion pipeline completed successfully")
