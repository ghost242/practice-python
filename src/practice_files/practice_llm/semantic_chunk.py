from __future__ import annotations

"""Semantic chunking utilities for prose and PDF-derived documents.

This module provides a compact pipeline for:

1. normalizing raw text extracted from sources such as PDFs,
2. splitting text into primitive sentence-like units,
3. incrementally merging those units into semantic chunks using embeddings,
4. extracting a central keyword / keyphrase for each semantic chunk,
5. converting semantic chunks into LangChain ``Document`` objects for storage
   in a vector database such as Chroma,
6. printing inspection reports for debugging and evaluation.

Design notes
------------
The previous versions of this module mixed several parallel representations of a
chunk, such as ``unit_ids`` and ``texts``. That makes it easy for those fields
to drift out of sync.

This refactored version keeps a single source of truth:

- a :class:`SemanticChunk` owns a list of :class:`PrimitiveUnit` objects.

All derived views such as chunk text, unit ids, spans, and source metadata are
computed from that list. This removes representation conflicts and makes the
module safer when processing many items from PDFs or other document sources.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import json
import logging
import re

import numpy as np
from langchain_core.documents import Document
from langchain_ollama import ChatOllama, OllamaEmbeddings

logger = logging.getLogger(__name__)

# ============================================================
# Text normalization / sentence splitting
# ============================================================


def normalize_text_for_chunking(text: str) -> str:
    """Normalize prose text before sentence segmentation.

    This function is aimed at text copied from PDFs or OCR pipelines where line
    breaks often appear inside sentences and sometimes inside words.

    Behavior:
    - normalizes line endings,
    - preserves paragraph breaks temporarily,
    - joins hyphenated line-wraps such as ``astro-\nnomy`` -> ``astronomy``,
    - converts ordinary line wraps into spaces,
    - collapses repeated horizontal whitespace.

    Args:
        text: Raw input text.

    Returns:
        A normalized string that is safer for sentence splitting.
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
    """Split normalized prose into sentence-like segments.

    This splitter is intentionally lightweight. It works well enough for many
    prose documents, but it is still heuristic rather than linguistically exact.
    For more demanding corpora, replace it with a dedicated sentence segmenter
    such as spaCy.

    Args:
        text: Normalized input text.

    Returns:
        A list of sentence-like strings in source order.
    """
    parts = re.split(r'(?<=[.!?])\s+(?=[“"\'(\[]*[A-Z0-9])', text)
    return [p.strip() for p in parts if p.strip()]


def sanitize_metadata_for_chroma(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Convert metadata into a Chroma-safe flat dictionary.

    Rules:
    - drop None
    - drop empty lists
    - keep scalar values directly
    - convert non-empty lists/tuples to JSON strings
    - convert dicts to JSON strings
    - convert everything else to string
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


# ============================================================
# Core data structures
# ============================================================


@dataclass(frozen=True)
class PrimitiveUnit:
    """Smallest text unit used by the semantic chunker.

    In the current implementation this is usually one sentence. Primitive units
    are the atomic elements considered for semantic merge decisions.

    Attributes:
        unit_id: Stable integer identity in document order.
        text: Raw text content for the unit.
        metadata: Optional lineage metadata inherited from the source document.
    """

    unit_id: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticChunk:
    """Semantic chunk built from one or more primitive units.

    A chunk stores only one primary representation: an ordered list of
    :class:`PrimitiveUnit` objects. Any other views such as ``unit_ids`` or the
    concatenated text are derived from that list.

    Attributes:
        chunk_id: Stable semantic chunk identifier.
        units: Ordered primitive units owned by this semantic chunk.
        metadata: Aggregated metadata such as page numbers or source file name.
        main_keyword: Single most important keyword / keyphrase for the chunk.
        keywords: Ranked supporting keywords or keyphrases.
    """

    chunk_id: int
    units: List[PrimitiveUnit]
    metadata: Dict[str, Any] = field(default_factory=dict)
    main_keyword: Optional[str] = None
    keywords: List[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Return the full concatenated chunk text."""
        return " ".join(unit.text for unit in self.units).strip()

    @property
    def unit_ids(self) -> List[int]:
        """Return primitive unit ids owned by this chunk."""
        return [unit.unit_id for unit in self.units]

    @property
    def texts(self) -> List[str]:
        """Return primitive unit texts owned by this chunk."""
        return [unit.text for unit in self.units]

    @property
    def size_units(self) -> int:
        """Return the number of primitive units contained in the chunk."""
        return len(self.units)

    @property
    def size_chars(self) -> int:
        """Return the chunk size measured in characters."""
        return len(self.text)

    @property
    def span_label(self) -> str:
        """Return a compact human-readable span label.

        Examples:
            ``U7``
            ``U13-U15``
        """
        ids = self.unit_ids
        if not ids:
            return "U?"
        if len(ids) == 1:
            return f"U{ids[0]}"
        return f"U{ids[0]}-U{ids[-1]}"

    def append_unit(self, unit: PrimitiveUnit) -> None:
        """Append one primitive unit to the chunk in source order."""
        self.units.append(unit)


@dataclass
class RetrievalView:
    """Retrieval-time view centered on one semantic chunk.

    This object does *not* represent a new semantic chunk. It is only a
    retrieval assembly that may include neighboring chunk text to provide more
    context to downstream consumers.

    Attributes:
        chunk_id: Semantic chunk id at the center of this retrieval view.
        center_span: True owned span of the center semantic chunk.
        prefix_context_span: Optional neighboring span from the previous chunk.
        suffix_context_span: Optional neighboring span from the next chunk.
        text: Retrieval-time text assembled from context and center chunk.
        metadata: Optional metadata carried over from the center chunk.
    """

    chunk_id: int
    center_span: str
    prefix_context_span: Optional[str]
    suffix_context_span: Optional[str]
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkDecision:
    """Record of one incremental merge or split decision.

    Attributes:
        current_chunk_id: Semantic chunk currently being grown.
        next_unit_id: Incoming primitive unit being evaluated.
        score: Cosine similarity used for the decision.
        action: Either ``"merge"`` or ``"split"``.
        reason: Short explanation for the action.
    """

    current_chunk_id: int
    next_unit_id: int
    score: float
    action: str
    reason: str


# ============================================================
# Numeric / heuristic utilities
# ============================================================


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two embedding vectors.

    Args:
        a: First embedding vector.
        b: Second embedding vector.

    Returns:
        Cosine similarity in the range ``[-1, 1]``. If either vector has zero
        norm, ``0.0`` is returned.
    """
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def has_strong_boundary_marker(text: str) -> bool:
    """Check whether text begins with a discourse marker suggesting a boundary.

    This is intentionally weak. For argumentative or philosophical prose,
    markers such as ``however`` may still continue the same argument, so this
    function should only be used as a secondary signal.

    Args:
        text: Candidate primitive unit text.

    Returns:
        ``True`` if the text begins with one of a small set of discourse markers.
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
    return any(lowered.startswith(m) for m in markers)


# ============================================================
# Embedding layer
# ============================================================


class LocalEmbedder:
    """Embedding wrapper around a local Ollama embedding model.

    The wrapper supports raw strings as well as LangChain ``Document`` objects.
    It is intended for semantic similarity, not for text generation.

    Attributes:
        document_prefix: Prefix attached to embedded documents.
        query_prefix: Prefix attached to query text.
        include_metadata_header: Whether to prepend selected metadata fields to
            embedded ``Document`` text.
        metadata_keys: Ordered metadata keys to include when building that
            optional metadata header.
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
        logger.info(
            "Initializing LocalEmbedder with model=%s base_url=%s",
            model,
            base_url,
        )
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
        """Build text to embed for one LangChain ``Document``."""
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
        """Embed raw document-like text."""
        logger.debug("Embedding text of length %d", len(text))
        vec = self.client.embed_query(f"{self.document_prefix}{text}")
        return np.asarray(vec, dtype=np.float32)

    def embed_query_text(self, text: str) -> np.ndarray:
        """Embed query text for retrieval or diagnostics."""
        logger.debug("Embedding query text of length %d", len(text))
        vec = self.client.embed_query(f"{self.query_prefix}{text}")
        return np.asarray(vec, dtype=np.float32)

    def embed_document(self, document: Document) -> np.ndarray:
        """Embed one LangChain ``Document``."""
        return self.embed_text(self._build_document_text(document))

    def embed_documents(
        self, documents: Iterable[Document]
    ) -> List[np.ndarray]:
        """Embed many LangChain ``Document`` objects."""
        return [self.embed_document(doc) for doc in documents]

    def embed_items(
        self, items: Iterable[Union[str, Document]]
    ) -> List[np.ndarray]:
        """Embed a heterogeneous sequence of strings and ``Document`` objects."""
        out: List[np.ndarray] = []
        for item in items:
            if isinstance(item, Document):
                out.append(self.embed_document(item))
            else:
                out.append(self.embed_text(item))
        return out


# ============================================================
# Keyword extraction layer
# ============================================================


class LocalKeywordExtractor:
    """Extract the central concept from a semantic chunk using a local LLM.

    The extractor returns:
    - ``main_keyword``: the single most important concept, and
    - ``keywords``: a short ranked list of supporting keyphrases.
    """

    def __init__(
        self,
        model: str = "ministral-3:8b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.0,
    ) -> None:
        logger.info(
            "Initializing LocalKeywordExtractor with model=%s base_url=%s",
            model,
            base_url,
        )
        self.llm = ChatOllama(
            model=model, base_url=base_url, temperature=temperature
        )

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Remove common markdown code-fence wrappers from model output."""
        stripped = text.strip()
        stripped = re.sub(
            r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE
        )
        stripped = re.sub(r"\s*```$", "", stripped)
        return stripped.strip()

    @staticmethod
    def _extract_first_json_object(text: str) -> Optional[str]:
        """Extract the first balanced JSON object substring if present."""
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(text)):
            ch = text[idx]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]
        return None

    @staticmethod
    def _clean_keyword_list(
        items: Iterable[str], max_keywords: int
    ) -> List[str]:
        """Normalize, deduplicate, and trim a keyword sequence."""
        cleaned: List[str] = []
        seen = set()
        junk_patterns = [
            r"^```",
            r"^\{$",
            r"^\}$",
            r'^"?main_keyword"?\s*:',
            r'^"?keywords"?\s*:',
            r"^\[$",
            r"^\]$",
        ]

        for item in items:
            kw = item.strip().strip(",").strip().strip('"').strip("'").strip()
            if not kw:
                continue
            if any(
                re.match(pattern, kw, flags=re.IGNORECASE)
                for pattern in junk_patterns
            ):
                continue
            key = kw.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(kw)
            if len(cleaned) >= max_keywords:
                break
        return cleaned

    def extract_keyword_summary(
        self, text: str, *, max_keywords: int = 5
    ) -> Dict[str, Any]:
        """Return a structured keyword summary for one text chunk.

        Expected JSON schema:
            {
              "main_keyword": "...",
              "keywords": ["...", "...", "..."]
            }
        """
        logger.debug(
            "Extracting keyword summary for chunk of length %d", len(text)
        )
        # system_prompt = (
        #     "You extract the central concept from a text chunk.\n"
        #     "Return ONLY valid JSON.\n"
        #     "Schema:\n"
        #     '{"main_keyword": "<single most important keyword or keyphrase>", '
        #     '"keywords": ["<ranked keyword 1>", "<ranked keyword 2>", "..."]}\n'
        #     "Rules:\n"
        #     "- main_keyword must be the single most important semantic concept.\n"
        #     "- Prefer noun phrases or technical/philosophical concepts.\n"
        #     "- If the text is argumentative or philosophical, prefer the governing concept over incidental nouns.\n"
        #     "- Avoid generic words such as 'thing', 'idea', 'text', 'argument'.\n"
        #     "- keywords must be ranked from most important to less important.\n"
        #     "- main_keyword should normally also appear in keywords.\n"
        #     f"- Return at most {max_keywords} keywords.\n"
        #     "- No explanation.\n"
        #     "- No markdown.\n"
        # )
        system_prompt = """You extract the central concept from one text chunk.

Return ONLY valid JSON.
Do not add markdown.
Do not add explanation.
Do not add code fences.

Output schema:
{
  "main_keyword": "string",
  "keywords": ["string", "string", "string"]
}

Rules:
- "main_keyword" must be the single most important concept in the chunk.
- Prefer a short noun phrase or technical/philosophical keyphrase.
- Do not use vague words like "idea", "discussion", "text", "argument", "concept", "thing".
- "keywords" must contain 3 to 5 short keyphrases ranked by importance.
- Include "main_keyword" as the first item in "keywords".
- Avoid duplicates.
- Keep phrases concise.
- If the chunk is philosophical or argumentative, prefer the governing concept over incidental nouns."""

        user_prompt = """Extract the central concept and the most important supporting keywords from this text chunk.

Text chunk:
{{chunk_text}}"""

        raw = self.llm.invoke(
            [("system", system_prompt), ("human", user_prompt)]
        ).content
        raw = self._strip_code_fences(raw)
        candidate_json = self._extract_first_json_object(raw) or raw

        try:
            data = json.loads(candidate_json)
            if not isinstance(data, dict):
                raise ValueError("Output is not a JSON object")

            main_keyword = data.get("main_keyword")
            if not isinstance(main_keyword, str):
                main_keyword = None
            else:
                main_keyword = main_keyword.strip() or None

            keywords = data.get("keywords", [])
            if not isinstance(keywords, list):
                keywords = []
            cleaned_keywords = self._clean_keyword_list(
                [item for item in keywords if isinstance(item, str)],
                max_keywords=max_keywords,
            )

            if main_keyword:
                if main_keyword.lower() not in {
                    kw.lower() for kw in cleaned_keywords
                }:
                    cleaned_keywords.insert(0, main_keyword)
                cleaned_keywords = self._clean_keyword_list(
                    cleaned_keywords, max_keywords=max_keywords
                )

            logger.debug(
                "Keyword extraction succeeded with main_keyword=%r",
                main_keyword,
            )
            return {
                "main_keyword": main_keyword,
                "keywords": cleaned_keywords[:max_keywords],
            }

        except Exception:
            logger.debug(
                "Keyword extraction JSON parse failed; using fallback parser"
            )
            parts = re.split(r"[\n,;]+", raw)
            fallback_keywords = self._clean_keyword_list(
                parts, max_keywords=max_keywords
            )
            main_keyword = fallback_keywords[0] if fallback_keywords else None
            return {
                "main_keyword": main_keyword,
                "keywords": fallback_keywords[:max_keywords],
            }


# ============================================================
# Semantic chunker
# ============================================================


class IncrementalSemanticChunker:
    """Incremental semantic chunker using embeddings and hysteresis thresholds.

    The decision variable is:
        ``sim(current_chunk, next_unit)``

    not:
        ``sim((p1,p2), (p2,p3))``

    This avoids overlap contamination during semantic segmentation.
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

        logger.info(
            "Initializing IncrementalSemanticChunker low=%.3f high=%.3f max_chars=%d max_units=%d",
            low_threshold,
            high_threshold,
            max_chunk_chars,
            max_chunk_units,
        )
        self.embedder = embedder
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_units = min_chunk_units
        self.max_chunk_units = max_chunk_units
        self.max_score_drop = max_score_drop

    def _make_units(self, text: str) -> List[PrimitiveUnit]:
        """Build primitive units from raw text."""
        normalized = normalize_text_for_chunking(text)
        sentences = split_sentences(normalized)
        units = [
            PrimitiveUnit(unit_id=i, text=s) for i, s in enumerate(sentences)
        ]
        logger.info("Built %d primitive units from raw text", len(units))
        return units

    def _make_units_from_documents(
        self, documents: List[Document]
    ) -> List[PrimitiveUnit]:
        """Build primitive sentence units from LangChain ``Document`` objects."""
        units: List[PrimitiveUnit] = []
        next_unit_id = 0
        for doc_index, doc in enumerate(documents):
            raw_text = doc.page_content or ""
            normalized = normalize_text_for_chunking(raw_text)
            sentences = split_sentences(normalized)
            for sent_index, sent in enumerate(sentences):
                metadata = dict(doc.metadata) if doc.metadata else {}
                metadata.update(
                    {
                        "document_index": doc_index,
                        "sentence_index_in_document": sent_index,
                    }
                )
                units.append(
                    PrimitiveUnit(
                        unit_id=next_unit_id, text=sent, metadata=metadata
                    )
                )
                next_unit_id += 1
        logger.info(
            "Built %d primitive units from %d documents",
            len(units),
            len(documents),
        )
        return units

    def _embed_cached(
        self, text: str, cache: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Embed text with simple memoization to avoid repeated calls."""
        if text not in cache:
            cache[text] = self.embedder.embed_text(text)
        return cache[text]

    def _score_extension(
        self,
        current_chunk: SemanticChunk,
        next_unit: PrimitiveUnit,
        cache: Dict[str, np.ndarray],
    ) -> float:
        """Score whether ``next_unit`` belongs to ``current_chunk``."""
        current_vec = self._embed_cached(current_chunk.text, cache)
        next_vec = self._embed_cached(next_unit.text, cache)
        return cosine_similarity(current_vec, next_vec)

    @staticmethod
    def _aggregate_unit_metadata(
        units: Sequence[PrimitiveUnit],
    ) -> Dict[str, Any]:
        """Aggregate metadata from many primitive units into one chunk-level map."""
        merged: Dict[str, Any] = {}
        for unit in units:
            for key, value in unit.metadata.items():
                if key not in merged:
                    merged[key] = value
                else:
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
        """Populate aggregated metadata on a completed chunk."""
        chunk.metadata = self._aggregate_unit_metadata(chunk.units)
        return chunk

    def _chunk_units(
        self,
        units: List[PrimitiveUnit],
        *,
        return_decisions: bool = False,
    ) -> Union[
        List[SemanticChunk], Tuple[List[SemanticChunk], List[ChunkDecision]]
    ]:
        """Core chunking routine shared by text and document entrypoints."""
        if not units:
            logger.info("No primitive units to chunk")
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
                    chunk_id=next_chunk_id, units=[next_unit]
                )
                next_chunk_id += 1
                prev_score = None

        chunks.append(self._finalize_chunk(current))
        logger.info(
            "Built %d semantic chunks from %d primitive units",
            len(chunks),
            len(units),
        )
        if return_decisions:
            return chunks, decisions
        return chunks

    def chunk_text(
        self,
        text: str,
        *,
        return_decisions: bool = False,
    ) -> Union[
        List[SemanticChunk], Tuple[List[SemanticChunk], List[ChunkDecision]]
    ]:
        """Chunk raw string input into semantic chunks."""
        logger.info("Chunking raw text input")
        units = self._make_units(text)
        return self._chunk_units(units, return_decisions=return_decisions)

    def chunk_documents(
        self,
        documents: Iterable[Document],
        *,
        return_decisions: bool = False,
    ) -> Union[
        List[SemanticChunk], Tuple[List[SemanticChunk], List[ChunkDecision]]
    ]:
        """Chunk LangChain ``Document`` objects into semantic chunks."""
        docs = list(documents)
        logger.info("Chunking %d documents", len(docs))
        units = self._make_units_from_documents(docs)
        return self._chunk_units(units, return_decisions=return_decisions)


# ============================================================
# Post-processing helpers
# ============================================================


def extract_keywords_for_chunks(
    chunks: List[SemanticChunk],
    extractor: LocalKeywordExtractor,
    *,
    max_keywords: int = 5,
) -> List[SemanticChunk]:
    """Populate ``main_keyword`` and ``keywords`` on each semantic chunk."""
    logger.info("Extracting keywords for %d semantic chunks", len(chunks))
    for chunk in chunks:
        result = extractor.extract_keyword_summary(
            chunk.text, max_keywords=max_keywords
        )
        chunk.main_keyword = result.get("main_keyword")
        chunk.keywords = result.get("keywords", [])
    return chunks


def build_retrieval_views(
    semantic_chunks: List[SemanticChunk],
    *,
    include_prev: bool = True,
    include_next: bool = False,
) -> List[RetrievalView]:
    """Build retrieval-time views around semantic chunks.

    These views do not modify chunk ownership. They are only convenient
    assemblies for retrieval or display.
    """
    logger.info(
        "Building retrieval views for %d semantic chunks", len(semantic_chunks)
    )
    views: List[RetrievalView] = []

    for i, chunk in enumerate(semantic_chunks):
        prefix_text = ""
        suffix_text = ""
        prefix_span = None
        suffix_span = None

        if include_prev and i > 0:
            prev_chunk = semantic_chunks[i - 1]
            prefix_text = prev_chunk.text + " "
            prefix_span = prev_chunk.span_label

        if include_next and i + 1 < len(semantic_chunks):
            next_chunk = semantic_chunks[i + 1]
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
    chunks: List[SemanticChunk],
) -> List[Document]:
    """Convert semantic chunks into LangChain ``Document`` objects for storage."""
    logger.info("Converting %d semantic chunks to Documents", len(chunks))
    docs: List[Document] = []
    for chunk in chunks:
        metadata = dict(chunk.metadata) if chunk.metadata else {}
        metadata.update(
            {
                "chunk_id": chunk.chunk_id,
                "owned_span": chunk.span_label,
                "unit_ids": chunk.unit_ids,
                "main_keyword": chunk.main_keyword,
                "keywords": chunk.keywords,
                "size_units": chunk.size_units,
                "size_chars": chunk.size_chars,
            }
        )
        docs.append(Document(page_content=chunk.text, metadata=metadata))
    return docs


# ============================================================
# Reporting helpers
# ============================================================


def print_decisions_report(decisions: List[ChunkDecision]) -> None:
    """Print a compact report of merge / split decisions."""
    print("=== decisions ===")
    for d in decisions:
        print(
            f"chunk=C{d.current_chunk_id} "
            f"next_unit=U{d.next_unit_id} "
            f"score={d.score:.4f} "
            f"action={d.action} "
            f"reason={d.reason}"
        )


def print_split_chunk_report_from_chunks(chunks: List[SemanticChunk]) -> None:
    """Print primitive split units reconstructed from semantic chunks."""
    print("=== split chunks (primitive units) ===")
    for chunk in chunks:
        for unit in chunk.units:
            print(f"\n--- U{unit.unit_id} ---")
            print("type: split_chunk")
            print("unit_id:", f"U{unit.unit_id}")
            print("size_chars:", len(unit.text))
            print(unit.text)


def print_semantic_chunk_report(chunks: List[SemanticChunk]) -> None:
    """Print semantic chunks after merge."""
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


def print_semantic_chunk_keyword_report(chunks: List[SemanticChunk]) -> None:
    """Print semantic chunks together with extracted keywords."""
    print("\n=== semantic chunks with important keywords ===")
    for chunk in chunks:
        print(f"\n--- C{chunk.chunk_id} ---")
        print("type: semantic_chunk_with_keywords")
        print("chunk_id:", f"C{chunk.chunk_id}")
        print("owned_span:", chunk.span_label)
        print("owned_unit_ids:", [f"U{x}" for x in chunk.unit_ids])
        print("size_units:", chunk.size_units)
        print("size_chars:", chunk.size_chars)
        print("main_keyword:", chunk.main_keyword)
        print("keywords:", chunk.keywords if chunk.keywords else [])
        if chunk.metadata:
            print("metadata:", chunk.metadata)
        print("concatenated_text:")
        print(chunk.text)


def print_retrieval_view_report(views: List[RetrievalView]) -> None:
    """Print retrieval views built around semantic chunks."""
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
    show_keywords: bool = True,
) -> None:
    """Print the chunking pipeline with a single clean entrypoint.

    Args:
        chunks: Final semantic chunks.
        decisions: Optional merge / split decision log.
        show_split_chunks: Whether to reconstruct and print primitive units.
        show_keywords: Whether to print keyword-enriched chunk reports.
    """
    if decisions is not None:
        print_decisions_report(decisions)

    if show_split_chunks:
        print_split_chunk_report_from_chunks(chunks)

    print_semantic_chunk_report(chunks)

    if show_keywords:
        print_semantic_chunk_keyword_report(chunks)
