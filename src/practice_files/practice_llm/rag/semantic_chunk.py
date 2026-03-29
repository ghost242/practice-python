from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from practice_files.practice_llm.rag.types import (
    ChunkDecision,
    PrimitiveUnit,
    RetrievalView,
    SemanticChunk,
)

logger = logging.getLogger(__name__)


def normalize_text_for_chunking(text: str) -> str:
    """
    Normalize prose text before sentence segmentation.

    Intended for text extracted from PDFs or OCR pipelines where line breaks may
    appear inside sentences and sometimes inside words.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n\s*\n+", "<PARA_BREAK>", text)
    text = re.sub(r"([A-Za-z])-\n([A-Za-z])", r"\1\2", text)
    text = re.sub(r"\n+", " ", text)
    text = text.replace("<PARA_BREAK>", "\n\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n\n *", "\n\n", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    """
    Split normalized prose into sentence-like segments.

    This is a lightweight heuristic splitter rather than a linguistically exact
    segmenter.
    """
    parts = re.split(r'(?<=[.!?])\s+(?=[“"\'(\[]*[A-Z0-9])', text)
    return [part.strip() for part in parts if part.strip()]


def sanitize_metadata_for_storage(
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert metadata into a flat JSON-safe dictionary.

    Rules:
    - drop None
    - drop empty lists/dicts
    - keep scalar values directly
    - convert lists/tuples/dicts to JSON strings
    - convert everything else to string
    """
    out: Dict[str, Any] = {}

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


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def has_strong_boundary_marker(text: str) -> bool:
    """
    Check whether text begins with a discourse marker that may imply a boundary.
    """
    lowered = text.strip().lower()
    markers = [
        "however",
        "on the other hand",
        "in contrast",
        "meanwhile",
        "nevertheless",
        "nonetheless",
    ]
    return any(lowered.startswith(marker) for marker in markers)


class LocalEmbedder:
    """
    Embedding wrapper around a local Ollama embedding model.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text-v2-moe:latest",
        base_url: str = "http://localhost:11434",
        document_prefix: str = "search_document: ",
        query_prefix: str = "search_query: ",
        include_metadata_header: bool = False,
        metadata_keys: Optional[List[str]] = None,
    ) -> None:
        self.document_prefix = document_prefix
        self.query_prefix = query_prefix
        self.include_metadata_header = include_metadata_header
        self.metadata_keys = metadata_keys or [
            "source",
            "page",
            "title",
            "section",
        ]
        self.client = OllamaEmbeddings(model=model, base_url=base_url)

    def _build_document_text(self, document: Document) -> str:
        content = document.page_content or ""
        if not self.include_metadata_header or not document.metadata:
            return content

        header_parts: List[str] = []
        for key in self.metadata_keys:
            if key in document.metadata:
                header_parts.append(f"{key}: {document.metadata[key]}")

        if not header_parts:
            return content

        return "\n".join(header_parts) + "\n\n" + content

    def embed_text(self, text: str) -> np.ndarray:
        vec = self.client.embed_query(f"{self.document_prefix}{text}")
        return np.asarray(vec, dtype=np.float32)

    def embed_query_text(self, text: str) -> np.ndarray:
        vec = self.client.embed_query(f"{self.query_prefix}{text}")
        return np.asarray(vec, dtype=np.float32)

    def embed_document(self, document: Document) -> np.ndarray:
        return self.embed_text(self._build_document_text(document))

    def embed_documents(
        self,
        documents: Iterable[Document],
    ) -> List[np.ndarray]:
        return [self.embed_document(doc) for doc in documents]


class IncrementalSemanticChunker:
    """
    Incremental semantic chunker using embeddings and threshold/hysteresis logic.

    Decision variable:
        sim(current_chunk, next_unit)
    """

    def __init__(
        self,
        embedder: LocalEmbedder,
        *,
        low_threshold: float = 0.62,
        high_threshold: float = 0.82,
        max_chunk_chars: int = 900,
        min_chunk_units: int = 1,
        max_chunk_units: int = 5,
        max_score_drop: float = 0.12,
    ) -> None:
        if low_threshold > high_threshold:
            raise ValueError("low_threshold must be <= high_threshold")

        self.embedder = embedder
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_units = min_chunk_units
        self.max_chunk_units = max_chunk_units
        self.max_score_drop = max_score_drop

    def chunk_text(
        self,
        text: str,
        *,
        return_decisions: bool = False,
    ) -> Union[
        List[SemanticChunk],
        Tuple[List[SemanticChunk], List[ChunkDecision]],
    ]:
        units = self._make_units(text)
        return self._chunk_units(units, return_decisions=return_decisions)

    def chunk_documents(
        self,
        documents: Iterable[Document],
        *,
        return_decisions: bool = False,
    ) -> Union[
        List[SemanticChunk],
        Tuple[List[SemanticChunk], List[ChunkDecision]],
    ]:
        docs = list(documents)
        units = self._make_units_from_documents(docs)
        return self._chunk_units(units, return_decisions=return_decisions)

    def _make_units(self, text: str) -> List[PrimitiveUnit]:
        normalized = normalize_text_for_chunking(text)
        sentences = split_sentences(normalized)
        return [
            PrimitiveUnit(unit_id=index, text=sentence)
            for index, sentence in enumerate(sentences)
        ]

    def _make_units_from_documents(
        self,
        documents: List[Document],
    ) -> List[PrimitiveUnit]:
        units: List[PrimitiveUnit] = []
        next_unit_id = 0

        for doc_index, doc in enumerate(documents):
            raw_text = doc.page_content or ""
            normalized = normalize_text_for_chunking(raw_text)
            sentences = split_sentences(normalized)

            for sent_index, sentence in enumerate(sentences):
                metadata = dict(doc.metadata) if doc.metadata else {}
                metadata.update(
                    {
                        "document_index": doc_index,
                        "sentence_index_in_document": sent_index,
                    }
                )
                units.append(
                    PrimitiveUnit(
                        unit_id=next_unit_id,
                        text=sentence,
                        metadata=metadata,
                    )
                )
                next_unit_id += 1

        return units

    def _embed_cached(
        self,
        text: str,
        cache: Dict[str, np.ndarray],
    ) -> np.ndarray:
        if text not in cache:
            cache[text] = self.embedder.embed_text(text)
        return cache[text]

    def _score_extension(
        self,
        current_chunk: SemanticChunk,
        next_unit: PrimitiveUnit,
        cache: Dict[str, np.ndarray],
    ) -> float:
        current_vec = self._embed_cached(current_chunk.text, cache)
        next_vec = self._embed_cached(next_unit.text, cache)
        return cosine_similarity(current_vec, next_vec)

    def _aggregate_unit_metadata(
        self,
        units: Sequence[PrimitiveUnit],
    ) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}

        for unit in units:
            for key, value in unit.metadata.items():
                if key not in merged:
                    merged[key] = value
                    continue

                existing = merged[key]
                if existing == value:
                    continue

                if not isinstance(existing, list):
                    existing = [existing]

                if value not in existing:
                    existing.append(value)

                merged[key] = existing

        if units:
            merged["first_unit_id"] = units[0].unit_id
            merged["last_unit_id"] = units[-1].unit_id

        merged["unit_count"] = len(units)
        return merged

    def _finalize_chunk(self, chunk: SemanticChunk) -> SemanticChunk:
        chunk.metadata = self._aggregate_unit_metadata(chunk.units)
        return chunk

    def _chunk_units(
        self,
        units: List[PrimitiveUnit],
        *,
        return_decisions: bool = False,
    ) -> Union[
        List[SemanticChunk],
        Tuple[List[SemanticChunk], List[ChunkDecision]],
    ]:
        if not units:
            return ([], []) if return_decisions else []

        cache: Dict[str, np.ndarray] = {}
        chunks: List[SemanticChunk] = []
        decisions: List[ChunkDecision] = []

        next_chunk_id = 1
        current = SemanticChunk(chunk_id=next_chunk_id, units=[units[0]])
        next_chunk_id += 1
        prev_score: Optional[float] = None

        for next_unit in units[1:]:
            score = self._score_extension(current, next_unit, cache)

            candidate_text = f"{current.text} {next_unit.text}".strip()
            would_exceed_chars = len(candidate_text) > self.max_chunk_chars
            would_exceed_units = current.size_units + 1 > self.max_chunk_units

            if would_exceed_chars or would_exceed_units:
                action = "split"
                reason = "max_size_limit"
            elif score >= self.high_threshold:
                action = "merge"
                reason = "high_similarity"
            elif score < self.low_threshold:
                action = "split"
                reason = "low_similarity"
            else:
                score_drop = (
                    0.0 if prev_score is None else (prev_score - score)
                )

                if (
                    has_strong_boundary_marker(next_unit.text)
                    and score_drop > 0.08
                ):
                    action = "split"
                    reason = "uncertain_zone_marker_plus_drop"
                elif (
                    prev_score is not None and score_drop > self.max_score_drop
                ):
                    action = "split"
                    reason = "uncertain_zone_large_score_drop"
                elif current.size_units < self.min_chunk_units:
                    action = "merge"
                    reason = "uncertain_zone_force_min_chunk"
                else:
                    action = "merge"
                    reason = "uncertain_zone_default_merge"

            decisions.append(
                ChunkDecision(
                    current_chunk_id=current.chunk_id,
                    next_unit_id=next_unit.unit_id,
                    score=score,
                    action=action,
                    reason=reason,
                )
            )

            if action == "merge":
                current.append_unit(next_unit)
                prev_score = score
            else:
                chunks.append(self._finalize_chunk(current))
                current = SemanticChunk(
                    chunk_id=next_chunk_id,
                    units=[next_unit],
                )
                next_chunk_id += 1
                prev_score = None

        chunks.append(self._finalize_chunk(current))

        if return_decisions:
            return chunks, decisions

        return chunks


def build_retrieval_views(
    semantic_chunks: List[SemanticChunk],
    *,
    include_prev: bool = True,
    include_next: bool = False,
) -> List[RetrievalView]:
    """
    Build retrieval-time context views around semantic chunks.
    """
    views: List[RetrievalView] = []

    for index, chunk in enumerate(semantic_chunks):
        prefix_text = ""
        suffix_text = ""
        prefix_span = None
        suffix_span = None

        if include_prev and index > 0:
            prev_chunk = semantic_chunks[index - 1]
            prefix_text = prev_chunk.text + " "
            prefix_span = prev_chunk.span_label

        if include_next and index + 1 < len(semantic_chunks):
            next_chunk = semantic_chunks[index + 1]
            suffix_text = " " + next_chunk.text
            suffix_span = next_chunk.span_label

        views.append(
            RetrievalView(
                chunk_id=chunk.chunk_id,
                center_span=chunk.span_label,
                prefix_context_span=prefix_span,
                suffix_context_span=suffix_span,
                text=f"{prefix_text}{chunk.text}{suffix_text}".strip(),
                metadata=dict(chunk.metadata),
            )
        )

    return views


def semantic_chunks_to_documents(
    chunks: Sequence[SemanticChunk],
    *,
    include_keywords: bool,
    sanitize_metadata: bool = True,
) -> List[Document]:
    """
    Convert semantic chunks into LangChain Document objects.
    """
    docs: List[Document] = []

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

        if sanitize_metadata:
            metadata = sanitize_metadata_for_storage(metadata)

        docs.append(
            Document(
                page_content=chunk.text,
                metadata=metadata,
            )
        )

    return docs


def semantic_chunks_to_metadata_updates(
    chunks: Sequence[SemanticChunk],
    *,
    sanitize_metadata: bool = True,
) -> List[Dict[str, Any]]:
    """
    Build metadata payloads from semantic chunks.

    This is DB-agnostic. Caller code may store these payloads in any backend.
    """
    updates: List[Dict[str, Any]] = []

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

        if sanitize_metadata:
            metadata = sanitize_metadata_for_storage(metadata)

        updates.append(metadata)

    return updates


def print_decisions_report(decisions: List[ChunkDecision]) -> None:
    """
    Print a compact report of merge/split decisions.
    """
    print("=== decisions ===")
    for decision in decisions:
        print(
            f"chunk=C{decision.current_chunk_id} "
            f"next_unit=U{decision.next_unit_id} "
            f"score={decision.score:.4f} "
            f"action={decision.action} "
            f"reason={decision.reason}"
        )


def print_split_chunk_report_from_chunks(chunks: List[SemanticChunk]) -> None:
    """
    Print primitive units reconstructed from semantic chunks.
    """
    print("=== split chunks (primitive units) ===")
    for chunk in chunks:
        for unit in chunk.units:
            print(f"\n--- U{unit.unit_id} ---")
            print("type: split_chunk")
            print("unit_id:", f"U{unit.unit_id}")
            print("size_chars:", len(unit.text))
            print(unit.text)


def print_semantic_chunk_report(chunks: List[SemanticChunk]) -> None:
    """
    Print semantic chunks after merge.
    """
    print("\n=== semantic chunks (concatenated split chunks) ===")
    for chunk in chunks:
        print(f"\n--- C{chunk.chunk_id} ---")
        print("type: semantic_chunk")
        print("chunk_id:", f"C{chunk.chunk_id}")
        print("owned_span:", chunk.span_label)
        print("owned_unit_ids:", [f"U{x}" for x in chunk.unit_ids])
        print("size_units:", chunk.size_units)
        print("size_chars:", chunk.size_chars)
        if chunk.metadata:
            print("metadata:", chunk.metadata)
        print("concatenated_text:")
        print(chunk.text)


def print_retrieval_view_report(views: List[RetrievalView]) -> None:
    """
    Print retrieval views built around semantic chunks.
    """
    print("\n=== retrieval views ===")
    for view in views:
        print(f"\n--- retrieval view for C{view.chunk_id} ---")
        print("center_span:", view.center_span)
        print("prefix_context_span:", view.prefix_context_span)
        print("suffix_context_span:", view.suffix_context_span)
        print(view.text)


def print_full_pipeline_report(
    chunks: List[SemanticChunk],
    *,
    decisions: Optional[List[ChunkDecision]] = None,
    show_split_chunks: bool = True,
) -> None:
    """
    Print a compact chunking pipeline report.
    """
    if decisions is not None:
        print_decisions_report(decisions)

    if show_split_chunks:
        print_split_chunk_report_from_chunks(chunks)

    print_semantic_chunk_report(chunks)
