from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import chromadb
import numpy as np
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class KeywordCandidate:
    text: str
    normalized: str
    start: int
    end: int
    occurrences: int


class KeywordExtractor:
    """
    Accuracy-oriented keyword extractor for chunk-sized documents.

    Strategy:
    1. Build phrase candidates from noun phrases + filtered n-grams.
    2. Score each candidate by semantic similarity to the whole chunk.
    3. Add light lexical priors: repetition, acronym/title bonus, position bonus.
    4. Select top phrases with MMR to avoid duplicates.

    This is intentionally heavier than YAKE/RAKE-style extraction.
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

    def _try_load_spacy(self) -> None:
        try:
            import spacy

            try:
                self._nlp = spacy.load(self._spacy_model_name)
            except Exception:
                # Fallback to smaller English model if transformer model is unavailable.
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

    def extract(
        self, text: str, *, top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        text = self._normalize_whitespace(text)
        if not text:
            return []

        candidates = self._generate_candidates(text)
        if not candidates:
            return []

        scored = self._score_candidates(text, candidates)
        selected = self._select_with_mmr(scored, top_k=top_k or self.top_k)

        return [
            {
                "keyword": item["candidate"].text,
                "score": round(float(item["final_score"]), 6),
                "similarity": round(float(item["semantic_score"]), 6),
                "occurrences": item["candidate"].occurrences,
                "start": item["candidate"].start,
                "end": item["candidate"].end,
            }
            for item in selected
        ]

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _generate_candidates(self, text: str) -> List[KeywordCandidate]:
        candidates: List[KeywordCandidate] = []

        if self._nlp is not None:
            candidates.extend(self._generate_spacy_candidates(text))

        # Fallback or supplement with filtered n-grams.
        candidates.extend(self._generate_ngram_candidates(text))

        deduped = self._dedupe_candidates(candidates)
        deduped.sort(key=lambda c: (-c.occurrences, c.start, len(c.text)))

        return deduped[: self.max_candidates]

    def _generate_spacy_candidates(self, text: str) -> List[KeywordCandidate]:
        doc = self._nlp(text)
        collected: List[KeywordCandidate] = []

        # Noun chunks are generally strong candidates for semantic keywords.
        for chunk in getattr(doc, "noun_chunks", []):
            phrase = self._clean_phrase(chunk.text)
            if not self._is_good_phrase(phrase):
                continue
            occurrences = self._count_occurrences(text, phrase)
            collected.append(
                KeywordCandidate(
                    text=phrase,
                    normalized=self._normalize_phrase(phrase),
                    start=chunk.start_char,
                    end=chunk.end_char,
                    occurrences=occurrences,
                )
            )

        # Named entities can be important even when noun chunk parsing misses them.
        for ent in getattr(doc, "ents", []):
            phrase = self._clean_phrase(ent.text)
            if not self._is_good_phrase(phrase):
                continue
            occurrences = self._count_occurrences(text, phrase)
            collected.append(
                KeywordCandidate(
                    text=phrase,
                    normalized=self._normalize_phrase(phrase),
                    start=ent.start_char,
                    end=ent.end_char,
                    occurrences=occurrences,
                )
            )

        return collected

    def _generate_ngram_candidates(self, text: str) -> List[KeywordCandidate]:
        tokens = self._simple_tokenize(text)
        collected: List[KeywordCandidate] = []

        for n in range(1, self.max_phrase_words + 1):
            for i in range(0, len(tokens) - n + 1):
                window = tokens[i : i + n]
                phrase = " ".join(window)
                phrase = self._clean_phrase(phrase)
                if not self._is_good_phrase(phrase):
                    continue

                match = re.search(re.escape(phrase), text, flags=re.IGNORECASE)
                if match is None:
                    continue

                occurrences = self._count_occurrences(text, phrase)
                collected.append(
                    KeywordCandidate(
                        text=phrase,
                        normalized=self._normalize_phrase(phrase),
                        start=match.start(),
                        end=match.end(),
                        occurrences=occurrences,
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

        # Reject phrases that are almost entirely stopwords.
        content_words = [
            w for w in normalized.split() if w not in self._stopwords
        ]
        if not content_words:
            return False

        # Reject single too-short generic token.
        if len(words) == 1:
            token = words[0]
            if len(token) < self.min_phrase_len:
                return False
            if normalized in self._stopwords:
                return False

        # Reject phrases with too much punctuation noise.
        if re.fullmatch(r"[-_/\.]+", phrase):
            return False

        # Reject phrases starting/ending with stopwords.
        if normalized.split()[0] in self._stopwords:
            return False
        if normalized.split()[-1] in self._stopwords:
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
        self, candidates: Sequence[KeywordCandidate]
    ) -> List[KeywordCandidate]:
        best: Dict[str, KeywordCandidate] = {}

        for cand in candidates:
            key = cand.normalized
            existing = best.get(key)

            if existing is None:
                best[key] = cand
                continue

            # Prefer higher occurrence, earlier appearance, then longer phrase.
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

        # Remove candidates fully contained in a better longer candidate.
        values = list(best.values())
        values.sort(
            key=lambda c: (-len(c.normalized), -c.occurrences, c.start)
        )

        filtered: List[KeywordCandidate] = []
        normalized_seen: List[str] = []

        for cand in values:
            if any(
                cand.normalized != s and cand.normalized in s
                for s in normalized_seen
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
        phrases = [c.text for c in candidates]

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

        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored

    @staticmethod
    def _looks_like_acronym_or_term(text: str) -> bool:
        return bool(
            re.search(r"\b[A-Z]{2,}\b", text)
            or re.search(r"[A-Za-z]+[-_/][A-Za-z0-9]+", text)
            or re.search(r"\b[A-Za-z]+\d+\b", text)
        )

    def _length_bonus(self, text: str) -> float:
        words = text.split()
        # Best range for chunk keywords is often 2-4 words.
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
        stop_count = sum(1 for w in words if w in self._stopwords)
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
                best = remaining.pop(0)
                selected.append(best)
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


class ChromaKeywordIndexer:
    """
    Run keyword extraction chunk by chunk on a ChromaDB collection.

    By default, it updates each document's metadata with:
      - "keywords": list[str]
      - "keyword_scores": dict[str, float]

    This works one chunk at a time for accuracy and inspectability.
    """

    def __init__(
        self,
        collection: Collection,
        extractor: KeywordExtractor,
        *,
        text_field: str = "document",
        keyword_field: str = "keywords",
        score_field: str = "keyword_scores",
    ) -> None:
        self.collection = collection
        self.extractor = extractor
        self.text_field = text_field
        self.keyword_field = keyword_field
        self.score_field = score_field

    def process_all(
        self,
        *,
        batch_size: int = 32,
        where: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ) -> None:
        total = self.collection.count()
        offset = 0

        while offset < total:
            batch = self.collection.get(
                limit=batch_size,
                offset=offset,
                where=where,
                include=["documents", "metadatas"],
            )

            ids = batch.get("ids", [])
            docs = batch.get("documents", [])
            metas = batch.get("metadatas", [])

            for doc_id, text, metadata in zip(ids, docs, metas):
                metadata = metadata or {}

                if not overwrite and self.keyword_field in metadata:
                    continue

                if not text or not text.strip():
                    continue

                extracted = self.extractor.extract(text)
                keywords = [item["keyword"] for item in extracted]
                keyword_scores = {
                    item["keyword"]: item["score"] for item in extracted
                }

                new_metadata = dict(metadata)
                new_metadata[self.keyword_field] = keywords
                new_metadata[self.score_field] = keyword_scores

                self.collection.update(
                    ids=[doc_id],
                    metadatas=[new_metadata],
                )

            offset += batch_size

    def process_ids(
        self,
        ids: Sequence[str],
        *,
        overwrite: bool = False,
    ) -> None:
        batch = self.collection.get(
            ids=list(ids),
            include=["documents", "metadatas"],
        )

        docs = batch.get("documents", [])
        metas = batch.get("metadatas", [])
        actual_ids = batch.get("ids", [])

        for doc_id, text, metadata in zip(actual_ids, docs, metas):
            metadata = metadata or {}

            if not overwrite and self.keyword_field in metadata:
                continue

            if not text or not text.strip():
                continue

            extracted = self.extractor.extract(text)
            keywords = [item["keyword"] for item in extracted]
            keyword_scores = {
                item["keyword"]: item["score"] for item in extracted
            }

            new_metadata = dict(metadata)
            new_metadata[self.keyword_field] = keywords
            new_metadata[self.score_field] = keyword_scores

            self.collection.update(
                ids=[doc_id],
                metadatas=[new_metadata],
            )


def build_chroma_collection(
    *,
    persist_directory: str,
    collection_name: str,
) -> Collection:
    client = chromadb.PersistentClient(path=persist_directory)
    return client.get_collection(collection_name)


def main() -> None:
    """
    Example usage:

    python keyword_extractor.py

    Before running:
      pip install chromadb sentence-transformers spacy numpy
      python -m spacy download en_core_web_trf

    If en_core_web_trf is too heavy:
      python -m spacy download en_core_web_sm
    """
    collection = build_chroma_collection(
        persist_directory="./philosophy_db",
        collection_name="intro_to_philosophy",
    )

    extractor = KeywordExtractor(
        embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        top_k=8,
        max_candidates=150,
        mmr_lambda=0.72,
        max_phrase_words=6,
        spacy_model_name="en_core_web_trf",
    )

    indexer = ChromaKeywordIndexer(
        collection=collection,
        extractor=extractor,
        keyword_field="keywords",
        score_field="keyword_scores",
    )

    indexer.process_all(batch_size=16, overwrite=True)


if __name__ == "__main__":
    main()
