"""Lexical retrieval and evidence ranking over M1's standalone corpus.

Simplest reliable approach for a 2-day MVP: hard jurisdiction filtering plus
IDF-weighted token overlap with a keyword boost, including Hindi keyword
aliases so Devanagari queries can match entries. No vector database or
reranker (Plan.md scope: avoid unnecessary infrastructure).

The jurisdiction from the QueryRequest is a hard filter: India queries can
only retrieve India-tagged evidence and International queries can only
retrieve International-tagged evidence, so the two answer-sets stay visibly
separate.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple

from .corpus import Evidence
from .models import QueryRequest

# \w does not match Devanagari combining marks (vowel signs, anusvara), which
# would shatter Hindi words into consonant fragments; extend the pattern with
# the Devanagari block (U+0900–U+097F) so Hindi queries tokenize whole.
_TOKEN_RE = re.compile(r"[\w\u0900-\u097F]+", re.UNICODE)

# Small English stopword list — keep minimal; Hindi queries rely on keywords_hi.
_STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "for", "with",
    "on", "at", "by", "from", "as", "is", "are", "was", "were", "be", "been",
    "being", "do", "does", "did", "can", "could", "should", "would", "will",
    "shall", "may", "might", "must", "have", "has", "had", "i", "me", "my",
    "we", "our", "you", "your", "he", "she", "it", "its", "they", "them",
    "their", "this", "that", "these", "those", "what", "which", "who", "whom",
    "how", "when", "where", "why", "not", "no", "yes", "in", "out", "up",
    "down", "about", "into", "over", "under", "want", "wanted", "need",
    "new", "use", "get", "got", "give",
}

# Keyword-hit weight: a query token matching a curated keyword is a much
# stronger relevance signal than plain text overlap.
KEYWORD_BOOST = 2.5


@dataclass
class ScoredEvidence:
    evidence: Evidence
    score: float


def tokenize(text: str) -> List[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def _tokens_match(token: str, target: str) -> bool:
    """Exact match, or prefix match between tokens that are both at least 4
    characters long (a light stand-in for a stemmer, e.g. 'patent' matches
    keyword 'patentability'). Short tokens (years, form numbers) match only
    exactly, so '1996' cannot prefix-match keyword '1' from 'form 1'."""
    if token == target:
        return True
    if min(len(token), len(target)) >= 4:
        return target.startswith(token) or token.startswith(target)
    return False


def _keyword_hit(token: str, keyword_tokens: Set[str]) -> bool:
    return any(_tokens_match(token, kw) for kw in keyword_tokens)


def _entry_text_tokens(entry: Evidence) -> List[str]:
    return tokenize(f"{entry.title} {entry.section} {entry.text}")


def compute_idf(entries: Sequence[Evidence]) -> Dict[str, float]:
    """Smoothed IDF over the corpus: rare terms matter more. Deterministic."""
    n = len(entries)
    df: Dict[str, int] = {}
    for e in entries:
        for t in set(_entry_text_tokens(e)):
            df[t] = df.get(t, 0) + 1
    return {t: math.log(1.0 + n / (1.0 + c)) for t, c in df.items()}


def score_entry(
    entry: Evidence,
    query_tokens: List[str],
    entry_text_token_set: Set[str],
    entry_keyword_tokens: Set[str],
    entry_keyword_hi: Set[str],
    idf: Dict[str, float],
) -> float:
    score = 0.0
    for t in set(query_tokens):
        if t in entry_text_token_set:
            score += idf.get(t, 1.0)
        if _keyword_hit(t, entry_keyword_tokens):
            score += KEYWORD_BOOST
        if _keyword_hit(t, entry_keyword_hi):
            # Hindi aliases are curated per entry; a Devanagari keyword hit is
            # a strong signal regardless of the request's language setting.
            score += KEYWORD_BOOST
    return round(score, 4)


def retrieve(
    request: QueryRequest,
    corpus: Sequence[Evidence],
    top_k: int = 3,
    min_score: float = 0.5,
) -> List[ScoredEvidence]:
    """Rank corpus entries for a request. Jurisdiction is a hard filter.
    Returns at most top_k entries with score >= min_score, sorted descending."""
    idf = compute_idf(corpus)
    query_tokens = tokenize(request.query)

    scored: List[Tuple[float, Evidence]] = []
    for entry in corpus:
        # Hard jurisdiction filter keeps India and International separate.
        if entry.jurisdiction != request.jurisdiction:
            continue
        text_tokens = set(_entry_text_tokens(entry))
        kw_tokens = set()
        for kw in entry.keywords:
            kw_tokens.update(_TOKEN_RE.findall(kw.lower()))
        kw_hi = set(entry.keywords_hi)
        s = score_entry(entry, query_tokens, text_tokens, kw_tokens, kw_hi, idf)
        if s >= min_score:
            scored.append((s, entry))

    scored.sort(key=lambda pair: (-pair[0], pair[1].id))
    return [ScoredEvidence(evidence=e, score=s) for s, e in scored[:top_k]]


def keep_relevant(scored: List[ScoredEvidence], ratio: float = 0.45) -> List[ScoredEvidence]:
    """Trim a ranked list to entries scoring at least `ratio` of the top score,
    so weakly-related evidence does not dilute grounded answers. The top entry
    always survives."""
    if not scored:
        return []
    threshold = ratio * scored[0].score
    kept = [s for s in scored if s.score >= threshold]
    return kept or scored[:1]
