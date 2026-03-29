from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PrimitiveUnit:
    """
    Smallest text unit used during semantic chunking.

    Usually one sentence or sentence-like segment.
    """

    unit_id: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticChunk:
    """
    Semantic chunk built from one or more primitive units.

    Shared mutable fields `main_keyword` and `keywords` are intentionally kept
    here so chunking and keyword modules can cooperate on the same object.
    """

    chunk_id: int
    units: List[PrimitiveUnit]
    metadata: Dict[str, Any] = field(default_factory=dict)
    main_keyword: Optional[str] = None
    keywords: List[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(unit.text for unit in self.units).strip()

    @property
    def unit_ids(self) -> List[int]:
        return [unit.unit_id for unit in self.units]

    @property
    def texts(self) -> List[str]:
        return [unit.text for unit in self.units]

    @property
    def size_units(self) -> int:
        return len(self.units)

    @property
    def size_chars(self) -> int:
        return len(self.text)

    @property
    def span_label(self) -> str:
        ids = self.unit_ids
        if not ids:
            return "U?"
        if len(ids) == 1:
            return f"U{ids[0]}"
        return f"U{ids[0]}-U{ids[-1]}"

    def append_unit(self, unit: PrimitiveUnit) -> None:
        self.units.append(unit)


@dataclass
class RetrievalView:
    """
    Retrieval-time assembled view centered on one semantic chunk.

    This is not a new chunk. It is only a context-expanded representation for
    retrieval or display.
    """

    chunk_id: int
    center_span: str
    prefix_context_span: Optional[str]
    suffix_context_span: Optional[str]
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChunkDecision:
    """
    One merge/split decision made during incremental chunk construction.
    """

    current_chunk_id: int
    next_unit_id: int
    score: float
    action: str
    reason: str


@dataclass(frozen=True)
class KeywordCandidate:
    """
    Intermediate keyword candidate used by semantic keyword extraction.
    """

    text: str
    normalized: str
    start: int
    end: int
    occurrences: int


@dataclass(frozen=True)
class KeywordResult:
    """
    Unified keyword extraction result.

    Both LLM-based and scoring-based keyword extractors should return this type.
    """

    main_keyword: Optional[str]
    keywords: List[str]
    scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChunkingResult:
    """
    Facade-friendly result for chunk construction.
    """

    chunks: List[SemanticChunk]
    decisions: Optional[List[ChunkDecision]] = None


@dataclass
class ProcessResult:
    """
    Facade-friendly result for end-to-end processing.

    `documents` is typed loosely here to avoid forcing `_types.py` to depend on
    LangChain. That keeps this module purely domain-oriented.
    """

    chunks: List[SemanticChunk]
    decisions: Optional[List[ChunkDecision]] = None
    retrieval_views: Optional[List[RetrievalView]] = None
    documents: Optional[List[Any]] = None
