import logging
from pathlib import Path
from typing import Any, Sequence, TypeVar

import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.documents import Document

from practice_files.practice_llm.semantic_chunk import (
    SemanticChunk,
    LocalEmbedder,
    IncrementalSemanticChunker,
    LocalKeywordExtractor,
    extract_keywords_for_chunks,
    sanitize_metadata_for_chroma,
    print_full_pipeline_report,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure console logging for the ingestion pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    # Silence noisy dependency logs that do not help pipeline monitoring.
    for name in ("httpx", "httpcore", "urllib3", "chromadb"):
        logging.getLogger(name).setLevel(logging.WARNING)


def batched(items: Sequence[T], batch_size: int):
    """Yield consecutive slices of ``items`` with at most ``batch_size`` elements."""
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
    """Add documents to Chroma in batches small enough for Chroma limits."""
    if len(documents) != len(ids):
        raise ValueError("documents and ids must have the same length")

    total = len(documents)
    logger.info(
        "Uploading %d documents to Chroma in batches of %d", total, batch_size
    )

    for start, end, batch_docs in batched(documents, batch_size):
        batch_ids = list(ids[start:end])
        logger.info(
            "Uploading batch %d:%d (%d documents)", start, end, len(batch_docs)
        )
        vector_store.add_documents(list(batch_docs), ids=batch_ids)

    logger.info("Completed initial Chroma upload")


def update_metadatas_in_batches(
    collection,
    metadatas: Sequence[dict[str, Any]],
    ids: Sequence[str],
    *,
    batch_size: int = 5000,
) -> None:
    """Update existing Chroma records in batches using metadata only.

    This is used after keyword extraction so that the pipeline becomes:

        semantic chunking -> initial storage -> keyword extraction -> metadata update

    The document text and ids remain unchanged; only metadata is updated.
    """
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


def semantic_chunks_to_documents(
    chunks: Sequence[SemanticChunk],
    *,
    include_keywords: bool,
) -> list[Document]:
    """Convert semantic chunks into LangChain ``Document`` objects.

    Args:
        chunks:
            Semantic chunks produced by the chunker.
        include_keywords:
            Whether keyword fields should be included in metadata.
            Use ``False`` for the initial storage step, then update metadata after
            keyword extraction completes.
    """
    docs: list[Document] = []

    for chunk in chunks:
        metadata = dict(chunk.metadata) if chunk.metadata else {}
        metadata.update(
            {
                "chunk_id": chunk.chunk_id,
                "owned_span": chunk.span_label,
                "unit_ids": chunk.unit_ids,
                "size_units": chunk.size_units,
                "size_chars": chunk.size_chars,
            }
        )

        if include_keywords:
            metadata["main_keyword"] = chunk.main_keyword
            metadata["keywords"] = chunk.keywords

        docs.append(
            Document(
                page_content=chunk.text,
                metadata=sanitize_metadata_for_chroma(metadata),
            )
        )

    return docs


def semantic_chunks_to_metadata_updates(
    chunks: Sequence[SemanticChunk],
) -> list[dict[str, Any]]:
    """Build metadata-only update payloads for already-stored semantic chunks."""
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
                "keywords": chunk.keywords,
            }
        )
        updates.append(sanitize_metadata_for_chroma(metadata))

    return updates


if __name__ == "__main__":
    configure_logging()

    pdf_path = Path("./resources/Introduction_to_Philosophy.pdf")
    page_range = (16, 412)
    base_url = "http://ollama:11434"
    persist_dir = "./philosophy_db"
    collection_name = "intro_to_philosophy"
    enable_keywords = False
    print_report = False

    logger.info("Starting PDF ingestion pipeline")
    logger.info("PDF path: %s", pdf_path)
    logger.info("Target page range: [%d, %d)", page_range[0], page_range[1])

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info("Loading PDF pages...")
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    logger.info("Loaded %d total PDF pages", len(docs))

    logger.info("Filtering content pages...")
    content_pages = [
        doc
        for doc in docs
        if page_range[0] <= doc.metadata.get("page", -1) < page_range[1]
    ]
    logger.info("Kept %d content pages after filtering", len(content_pages))

    logger.info(
        "Initializing embedding model: %s", "nomic-embed-text-v2-moe:latest"
    )
    embedder = LocalEmbedder(
        model="nomic-embed-text-v2-moe:latest",
        base_url=base_url,
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

    logger.info("Running semantic chunking over filtered PDF pages...")
    chunks, decisions = chunker.chunk_documents(
        content_pages, return_decisions=True
    )
    logger.info(
        "Built %d semantic chunks from %d pages",
        len(chunks),
        len(content_pages),
    )
    logger.info("Recorded %d merge/split decisions", len(decisions))

    if print_report:
        logger.info("Printing pipeline report...")
        print_full_pipeline_report(
            chunks,
            decisions=decisions,
            show_split_chunks=True,
            show_keywords=False,
        )

    logger.info(
        "Converting semantic chunks into LangChain Document objects (without keywords)..."
    )
    chunk_docs = semantic_chunks_to_documents(chunks, include_keywords=False)
    ids = [f"chunk-{chunk.chunk_id}" for chunk in chunks]
    logger.info(
        "Prepared %d chunk documents for initial vector storage",
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

    logger.info(
        "Adding semantic chunks to Chroma before keyword extraction..."
    )
    add_documents_in_batches(
        vector_store,
        chunk_docs,
        ids,
        batch_size=5000,
    )
    logger.info(
        "Stored %d semantic chunks in Chroma collection '%s'",
        len(chunk_docs),
        collection_name,
    )

    if enable_keywords:
        logger.info("Initializing keyword extractor: %s", "llama3.2:3b")
        keyword_extractor = LocalKeywordExtractor(
            model="llama3.2:3b",
            base_url=base_url,
            temperature=0.0,
        )
        logger.info(
            "Extracting keywords for %d semantic chunks...", len(chunks)
        )
        extract_keywords_for_chunks(chunks, keyword_extractor, max_keywords=6)
        logger.info("Keyword extraction completed")

        logger.info("Preparing metadata updates with extracted keywords...")
        metadata_updates = semantic_chunks_to_metadata_updates(chunks)

        logger.info(
            "Updating stored Chroma metadata with extracted keywords..."
        )
        update_metadatas_in_batches(
            vector_store._collection,
            metadata_updates,
            ids,
            batch_size=5000,
        )
        logger.info(
            "Updated Chroma metadata for %d semantic chunks",
            len(metadata_updates),
        )
    else:
        logger.info("Keyword extraction is disabled")

    logger.info("PDF ingestion pipeline completed successfully")
