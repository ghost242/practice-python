from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence

import numpy as np
from langchain_ollama import ChatOllama
from sentence_transformers import SentenceTransformer

from practice_files.practice_llm.types import (
    KeywordCandidate,
    KeywordResult,
    SemanticChunk,
)


class BaseKeywordExtractor(Protocol):
    """
    Common interface for keyword extractors.

    Every implementation returns KeywordResult so the caller does not need to
    care whether extraction is LLM-based or embedding/scoring-based.
    """

    def extract(
        self,
        text: str,
        *,
        top_k: Optional[int] = None,
    ) -> KeywordResult: ...


class LLMKeywordExtractor:
    """
    LLM-based keyword extractor.

    Good for finding a governing concept and a short ranked keyword list.
    """

    def __init__(
        self,
        *,
        model: str = "ministral-3:8b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.0,
    ) -> None:
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )

    def extract(
        self,
        text: str,
        *,
        top_k: Optional[int] = None,
    ) -> KeywordResult:
        max_keywords = top_k or 5
        raw = self.llm.invoke(
            [
                ("system", self._build_system_prompt(max_keywords)),
                ("human", self._build_user_prompt(text)),
            ]
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
                if main_keyword.casefold() not in {
                    kw.casefold() for kw in cleaned_keywords
                }:
                    cleaned_keywords.insert(0, main_keyword)
                cleaned_keywords = self._clean_keyword_list(
                    cleaned_keywords,
                    max_keywords=max_keywords,
                )

            return KeywordResult(
                main_keyword=main_keyword,
                keywords=cleaned_keywords[:max_keywords],
                scores={},
            )

        except Exception:
            parts = re.split(r"[\n,;]+", raw)
            fallback_keywords = self._clean_keyword_list(
                parts,
                max_keywords=max_keywords,
            )
            main_keyword = fallback_keywords[0] if fallback_keywords else None

            return KeywordResult(
                main_keyword=main_keyword,
                keywords=fallback_keywords[:max_keywords],
                scores={},
            )

    @staticmethod
    def _build_system_prompt(max_keywords: int) -> str:
        return f"""You extract the central concept from one text chunk.

Return ONLY valid JSON.
Do not add markdown.
Do not add explanation.
Do not add code fences.

Output schema:
{{
  "main_keyword": "string",
  "keywords": ["string", "string", "string"]
}}

Rules:
- "main_keyword" must be the single most important concept in the chunk.
- Prefer a short noun phrase or technical/philosophical keyphrase.
- Do not use vague words like "idea", "discussion", "text", "argument", "concept", "thing".
- "keywords" must contain 3 to {max_keywords} short keyphrases ranked by importance.
- Include "main_keyword" as the first item in "keywords".
- Avoid duplicates.
- Keep phrases concise.
- If the chunk is philosophical or argumentative, prefer the governing concept over incidental nouns."""

    @staticmethod
    def _build_user_prompt(text: str) -> str:
        return f"""Extract the central concept and the most important supporting keywords from this text chunk.

Text chunk:
{text}"""

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        stripped = text.strip()
        stripped = re.sub(
            r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE
        )
        stripped = re.sub(r"\s*```$", "", stripped)
        return stripped.strip()

    @staticmethod
    def _extract_first_json_object(text: str) -> Optional[str]:
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
        items: Iterable[str],
        *,
        max_keywords: int,
    ) -> List[str]:
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

            key = kw.casefold()
            if key in seen:
                continue

            seen.add(key)
            cleaned.append(kw)

            if len(cleaned) >= max_keywords:
                break

        return cleaned


class SemanticKeywordExtractor:
    """
    Accuracy-oriented keyword extractor based on candidate generation,
    embedding similarity, and MMR selection.
    """

    def __init__(
        self,
        *,
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        top_k: int = 8,
        max_candidates: int = 120,
        mmr_lambda: float = 0.72,
        min_phrase_len: int = 2,
        max_phrase_words: int = 6,
        spacy_model_name: str = "en_core_web_trf",
        keyword_reference_path: Optional[str] = None,
    ) -> None:
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.top_k = top_k
        self.max_candidates = max_candidates
        self.mmr_lambda = mmr_lambda
        self.min_phrase_len = min_phrase_len
        self.max_phrase_words = max_phrase_words

        self._nlp = None
        self._spacy_model_name = spacy_model_name
        self._try_load_spacy()

        self._stopwords = self._build_stopwords()
        self._reference = self._load_keyword_reference(keyword_reference_path)

    def extract(
        self,
        text: str,
        *,
        top_k: Optional[int] = None,
    ) -> KeywordResult:
        text = self._normalize_whitespace(text)
        if not text:
            return KeywordResult(main_keyword=None, keywords=[], scores={})

        candidates = self._generate_candidates(text)
        if not candidates:
            return KeywordResult(main_keyword=None, keywords=[], scores={})

        scored = self._score_candidates(text, candidates)
        selected = self._select_with_mmr(
            scored_candidates=scored,
            top_k=top_k or self.top_k,
        )

        keywords = [item["candidate"].text for item in selected]
        keywords = [
            self._canonicalize_keyword(keyword) for keyword in keywords
        ]
        keywords = self._dedupe_preserve_order(keywords)

        score_map: Dict[str, float] = {}
        for item in selected:
            key = self._canonicalize_keyword(item["candidate"].text)
            if key not in score_map:
                score_map[key] = float(item["final_score"])

        main_keyword = keywords[0] if keywords else None

        return KeywordResult(
            main_keyword=main_keyword,
            keywords=keywords,
            scores=score_map,
        )

    def _try_load_spacy(self) -> None:
        try:
            import spacy

            try:
                self._nlp = spacy.load(self._spacy_model_name)
            except Exception:
                try:
                    self._nlp = spacy.load("en_core_web_sm")
                except Exception:
                    self._nlp = None
        except Exception:
            self._nlp = None

    @staticmethod
    def _build_stopwords() -> set[str]:
        return {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "then",
            "else",
            "for",
            "to",
            "of",
            "in",
            "on",
            "at",
            "by",
            "with",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "their",
            "there",
            "here",
            "into",
            "about",
            "over",
            "under",
            "between",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "we",
            "you",
            "they",
            "he",
            "she",
            "i",
            "my",
            "our",
            "your",
            "his",
            "her",
            "them",
            "us",
            "also",
            "can",
            "could",
            "should",
            "would",
            "may",
            "might",
            "must",
            "will",
            "shall",
            "do",
            "does",
            "did",
            "done",
            "than",
            "such",
            "other",
            "more",
            "most",
            "some",
            "any",
            "each",
            "many",
            "much",
            "very",
            "just",
            "not",
            "no",
            "yes",
        }

    @staticmethod
    def _load_keyword_reference(path: Optional[str]) -> Dict[str, Any]:
        if not path:
            return {}

        ref_path = Path(path)
        if not ref_path.exists():
            return {}

        text = ref_path.read_text(encoding="utf-8").strip()
        if not text:
            return {}

        try:
            suffix = ref_path.suffix.lower()
            if suffix == ".json":
                return json.loads(text)
        except Exception:
            return {}

        return {}

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _generate_candidates(self, text: str) -> List[KeywordCandidate]:
        candidates: List[KeywordCandidate] = []

        if self._nlp is not None:
            candidates.extend(self._generate_spacy_candidates(text))

        candidates.extend(self._generate_ngram_candidates(text))

        deduped = self._dedupe_candidates(candidates)
        deduped.sort(key=lambda c: (-c.occurrences, c.start, len(c.text)))
        return deduped[: self.max_candidates]

    def _generate_spacy_candidates(self, text: str) -> List[KeywordCandidate]:
        if self._nlp is None:
            return []

        doc = self._nlp(text)
        collected: List[KeywordCandidate] = []

        for chunk in getattr(doc, "noun_chunks", []):
            phrase = self._clean_phrase(chunk.text)
            if not self._is_good_phrase(phrase):
                continue

            collected.append(
                KeywordCandidate(
                    text=phrase,
                    normalized=self._normalize_phrase(phrase),
                    start=chunk.start_char,
                    end=chunk.end_char,
                    occurrences=self._count_occurrences(text, phrase),
                )
            )

        for ent in getattr(doc, "ents", []):
            phrase = self._clean_phrase(ent.text)
            if not self._is_good_phrase(phrase):
                continue

            collected.append(
                KeywordCandidate(
                    text=phrase,
                    normalized=self._normalize_phrase(phrase),
                    start=ent.start_char,
                    end=ent.end_char,
                    occurrences=self._count_occurrences(text, phrase),
                )
            )

        return collected

    def _generate_ngram_candidates(self, text: str) -> List[KeywordCandidate]:
        tokens = self._simple_tokenize(text)
        collected: List[KeywordCandidate] = []

        for n in range(1, self.max_phrase_words + 1):
            for i in range(0, len(tokens) - n + 1):
                phrase = " ".join(tokens[i : i + n])
                phrase = self._clean_phrase(phrase)

                if not self._is_good_phrase(phrase):
                    continue

                match = re.search(re.escape(phrase), text, flags=re.IGNORECASE)
                if match is None:
                    continue

                collected.append(
                    KeywordCandidate(
                        text=phrase,
                        normalized=self._normalize_phrase(phrase),
                        start=match.start(),
                        end=match.end(),
                        occurrences=self._count_occurrences(text, phrase),
                    )
                )

        return collected

    @staticmethod
    def _simple_tokenize(text: str) -> List[str]:
        return re.findall(r"[A-Za-z0-9][A-Za-z0-9\-_/\.]*", text)

    @staticmethod
    def _clean_phrase(phrase: str) -> str:
        phrase = phrase.strip(" \t\n\r.,;:!?()[]{}\"'`")
        phrase = re.sub(r"\s+", " ", phrase)
        return phrase

    def _is_good_phrase(self, phrase: str) -> bool:
        if not phrase:
            return False

        words = phrase.split()
        if len(words) > self.max_phrase_words:
            return False

        normalized = self._normalize_phrase(phrase)
        if not normalized:
            return False

        normalized_words = normalized.split()
        content_words = [
            word for word in normalized_words if word not in self._stopwords
        ]
        if not content_words:
            return False

        forbidden_keywords = {
            str(word).casefold()
            for word in self._reference.get("forbidden_keywords", [])
        }
        if normalized in forbidden_keywords:
            return False

        if len(words) == 1:
            token = words[0]
            if len(token) < self.min_phrase_len:
                return False
            if normalized in self._stopwords:
                return False

        if re.fullmatch(r"[-_/\.]+", phrase):
            return False

        if normalized_words[0] in self._stopwords:
            return False
        if normalized_words[-1] in self._stopwords:
            return False

        return True

    @staticmethod
    def _normalize_phrase(phrase: str) -> str:
        phrase = phrase.casefold().strip()
        phrase = re.sub(r"\s+", " ", phrase)
        return phrase

    @staticmethod
    def _count_occurrences(text: str, phrase: str) -> int:
        return len(re.findall(re.escape(phrase), text, flags=re.IGNORECASE))

    def _dedupe_candidates(
        self,
        candidates: Sequence[KeywordCandidate],
    ) -> List[KeywordCandidate]:
        best: Dict[str, KeywordCandidate] = {}

        for cand in candidates:
            key = cand.normalized
            existing = best.get(key)

            if existing is None:
                best[key] = cand
                continue

            if (
                cand.occurrences > existing.occurrences
                or (
                    cand.occurrences == existing.occurrences
                    and cand.start < existing.start
                )
                or (
                    cand.occurrences == existing.occurrences
                    and cand.start == existing.start
                    and len(cand.text) > len(existing.text)
                )
            ):
                best[key] = cand

        values = list(best.values())
        values.sort(
            key=lambda c: (-len(c.normalized), -c.occurrences, c.start)
        )

        filtered: List[KeywordCandidate] = []
        normalized_seen: List[str] = []

        for cand in values:
            if any(
                cand.normalized != seen and cand.normalized in seen
                for seen in normalized_seen
            ):
                continue
            filtered.append(cand)
            normalized_seen.append(cand.normalized)

        filtered.sort(key=lambda c: (c.start, -len(c.text)))
        return filtered

    def _score_candidates(
        self,
        text: str,
        candidates: Sequence[KeywordCandidate],
    ) -> List[Dict[str, Any]]:
        phrases = [candidate.text for candidate in candidates]

        doc_embedding = self.embedding_model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

        candidate_embeddings = self.embedding_model.encode(
            phrases,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        scored: List[Dict[str, Any]] = []
        text_len = max(len(text), 1)

        for cand, emb in zip(candidates, candidate_embeddings):
            semantic = float(np.dot(doc_embedding, emb))
            occurrence_bonus = min(math.log1p(cand.occurrences) / 3.0, 0.35)
            early_bonus = max(0.0, 0.12 * (1.0 - (cand.start / text_len)))
            acronym_bonus = (
                0.08 if self._looks_like_acronym_or_term(cand.text) else 0.0
            )
            length_bonus = self._length_bonus(cand.text)
            stopword_penalty = self._stopword_ratio_penalty(cand.normalized)

            final_score = (
                0.72 * semantic
                + 0.12 * occurrence_bonus
                + 0.06 * early_bonus
                + 0.05 * acronym_bonus
                + 0.05 * length_bonus
                - 0.08 * stopword_penalty
            )

            scored.append(
                {
                    "candidate": cand,
                    "embedding": emb,
                    "semantic_score": semantic,
                    "final_score": final_score,
                }
            )

        scored.sort(key=lambda item: item["final_score"], reverse=True)
        return scored

    @staticmethod
    def _looks_like_acronym_or_term(text: str) -> bool:
        return bool(
            re.search(r"\b[A-Z]{2,}\b", text)
            or re.search(r"[A-Za-z]+[-_/][A-Za-z0-9]+", text)
            or re.search(r"\b[A-Za-z]+\d+\b", text)
        )

    @staticmethod
    def _length_bonus(text: str) -> float:
        words = text.split()
        if len(words) == 1:
            return 0.04
        if 2 <= len(words) <= 4:
            return 0.12
        if len(words) == 5:
            return 0.08
        return 0.02

    def _stopword_ratio_penalty(self, normalized_phrase: str) -> float:
        words = normalized_phrase.split()
        if not words:
            return 1.0
        stop_count = sum(1 for word in words if word in self._stopwords)
        return stop_count / len(words)

    def _select_with_mmr(
        self,
        scored_candidates: Sequence[Dict[str, Any]],
        *,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        if not scored_candidates:
            return []

        selected: List[Dict[str, Any]] = []
        remaining = list(scored_candidates)

        while remaining and len(selected) < top_k:
            if not selected:
                selected.append(remaining.pop(0))
                continue

            best_idx = -1
            best_mmr = -1e9

            for idx, item in enumerate(remaining):
                relevance = float(item["final_score"])
                similarity_to_selected = max(
                    float(np.dot(item["embedding"], chosen["embedding"]))
                    for chosen in selected
                )

                mmr_score = (
                    self.mmr_lambda * relevance
                    - (1.0 - self.mmr_lambda) * similarity_to_selected
                )

                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = idx

            selected.append(remaining.pop(best_idx))

        return selected

    def _canonicalize_keyword(self, keyword: str) -> str:
        preferred_terms = self._reference.get("preferred_terms", {})
        normalized = keyword.casefold().strip()

        for alias, canonical in preferred_terms.items():
            if normalized == str(alias).casefold():
                return str(canonical)

        return keyword

    @staticmethod
    def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
        out: List[str] = []
        seen = set()

        for value in values:
            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(value)

        return out


def enrich_chunks_with_keywords(
    chunks: Sequence[SemanticChunk],
    *,
    extractor: BaseKeywordExtractor,
    top_k: int = 5,
) -> List[SemanticChunk]:
    """
    Apply keyword extraction to each semantic chunk in memory.
    """
    enriched = list(chunks)

    for chunk in enriched:
        result = extractor.extract(chunk.text, top_k=top_k)
        chunk.main_keyword = result.main_keyword
        chunk.keywords = result.keywords

    return enriched


def build_keyword_metadata(
    chunk: SemanticChunk,
    *,
    extractor: BaseKeywordExtractor,
    top_k: int = 5,
    include_scores: bool = True,
) -> Dict[str, Any]:
    """
    Build DB-agnostic keyword metadata for one chunk by running extraction now.
    """
    result = extractor.extract(chunk.text, top_k=top_k)

    metadata: Dict[str, Any] = {
        "chunk_id": chunk.chunk_id,
        "main_keyword": result.main_keyword,
        "keywords": result.keywords,
    }

    if include_scores and result.scores:
        metadata["keyword_scores"] = result.scores

    return metadata


def build_keyword_metadata_updates(
    chunks: Sequence[SemanticChunk],
    *,
    extractor: BaseKeywordExtractor,
    top_k: int = 5,
    include_scores: bool = True,
) -> List[Dict[str, Any]]:
    """
    Build DB-agnostic keyword metadata payloads for many chunks by running
    extraction on each chunk.
    """
    updates: List[Dict[str, Any]] = []

    for chunk in chunks:
        updates.append(
            build_keyword_metadata(
                chunk,
                extractor=extractor,
                top_k=top_k,
                include_scores=include_scores,
            )
        )

    return updates


def build_keyword_metadata_from_enriched_chunks(
    chunks: Sequence[SemanticChunk],
    *,
    include_scores: bool = False,
) -> List[Dict[str, Any]]:
    """
    Build DB-agnostic keyword metadata payloads from already-enriched chunks.

    Use this after enrich_chunks_with_keywords() to avoid running extraction
    twice. Scores are omitted by default because SemanticChunk usually stores
    only main_keyword and keywords.
    """
    updates: List[Dict[str, Any]] = []

    for chunk in chunks:
        update: Dict[str, Any] = {
            "chunk_id": chunk.chunk_id,
            "main_keyword": chunk.main_keyword,
            "keywords": list(chunk.keywords),
        }

        if include_scores:
            update["keyword_scores"] = {}

        updates.append(update)

    return updates
