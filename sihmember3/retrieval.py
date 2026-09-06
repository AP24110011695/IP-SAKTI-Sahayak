"""Member 3 Phase 2 — India evidence retrieval.

Deterministic evidence selection over the Phase 1 verified corpus. Builds on
the Phase 1 retrieval seam (sources.find_sources) without changing it:

- queries are normalised through routing.normalize_query so Hindi questions
  retrieve the same evidence as their English equivalents;
- curated record tags are the primary signal (+2), section/section_title/
  source_name the secondary signal (+1), and the routed scope area gives a
  +1 alignment boost — all deterministic, all explainable;
- a sufficiency rule decides whether the retrieved evidence is strong enough
  to ground guidance; weak retrieval returns sufficient=False so the guidance
  layer abstains instead of generating a thin answer.

No vectors, no rerankers, no LLM — keyword matching over a 14-record corpus
is deliberately simple and fully testable (MEMBER_3.md Section 6).
"""

import re

from . import routing
from .sources import all_sources

# Minimum score for a record to count as a retrieval hit at all.
HIT_MIN_SCORE = 2
# Default number of evidence records passed to generation.
DEFAULT_TOP_K = 3

# Small synonym map for genuine retrieval gaps (query word → corpus word).
# Kept deliberately tiny; tags already cover most vocabulary. A synonym-
# mapped token emits ONLY its synonym, so semantic mappings (medicine →
# drug) cannot leak their original token into unrelated areas.
_SYNONYMS = {
    "register": "registration",
    "registering": "registration",
    "registered": "registration",
    "license": "licence",
    "licensing": "licence",
    "medicine": "drug",
    "medicines": "drug",
    "patented": "patent",
    "patenting": "patent",
    "patents": "patent",
    "ayurved": "ayurveda",
    "ayurvedic": "ayurveda",
    "formulations": "formulation",
    "advertisement": "advertising",
    "advertisements": "advertising",
    "advertise": "advertising",
    "copyrights": "copyright",
    "designs": "design",
    "varieties": "variety",
    "tags": "tag",
    "claim": "claims",
}

_STOPWORDS = {
    "the", "and", "for", "with", "under", "from", "that", "this", "any",
    "are", "was", "has", "its", "his", "her", "can", "how", "what", "when",
    "not", "per", "via", "all", "new", "act", "law", "shall", "such",
    "which", "who", "whom", "may", "will", "would", "should", "their",
    "there", "been", "have", "into", "onto", "about", "after", "before",
    "does", "did", "doing", "need", "want", "get", "got", "make", "made",
    "use", "used", "using", "product", "products", "item", "items",
    # jurisdiction words appear in almost every source_name — never a signal
    "india", "indian",
}


def extract_keywords(query):
    """Extract match keywords from a (possibly Hindi) query: lowercase
    tokens, Hindi-mapped, minus stopwords. A token with a synonym mapping
    emits ONLY the synonym (so "medicine" matches drug records without
    leaking "medicine" into other areas). Returns a deterministic list
    (original order, deduplicated)."""
    normalised = routing.normalize_query(query)
    tokens = routing._TOKEN_RE.findall(normalised)
    keywords = []
    for token in tokens:
        token = token.strip("()")
        if len(token) < 2:
            continue
        if len(token) == 2 and token not in ("gi", "tk"):
            continue
        if token in _STOPWORDS:
            continue
        variant = _SYNONYMS.get(token, token)
        if variant not in keywords:
            keywords.append(variant)
    return keywords


def score_record(record, keywords, scope_area=None):
    """Deterministic relevance score for one record against the keywords.

    +2 per keyword found in the curated tags; +1 per keyword found in
    section/section_title/source_name; +1 scope alignment with the routed
    area. Matching is word-boundary aware (a two-letter keyword like "gi"
    must not match inside "biological"). Returns (score, matched_keywords)."""
    tags_text = " ".join(record.get("tags", [])).lower()
    meta_text = " ".join([
        record.get("section", ""),
        record.get("section_title", ""),
        record.get("source_name", ""),
    ]).lower()
    score = 0
    matched = []
    for keyword in keywords:
        pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"
        if re.search(pattern, tags_text):
            score += 2
            matched.append(keyword)
        elif re.search(pattern, meta_text):
            score += 1
            matched.append(keyword)
    if scope_area and record.get("scope_area") == scope_area and score > 0:
        score += 1
    return score, matched


def retrieve_evidence(query, routing_decision=None, top_k=None,
                      sources=None):
    """Retrieve evidence for a query. Returns (hits, sufficiency).

    hits: list of dicts {record, score, matched} sorted deterministically
          (score desc, then record id), restricted to the effective top_k.
    sufficiency: {sufficient, reason, best_score, n_hits, in_scope_hit}.

    The effective top_k is DEFAULT_TOP_K for single-scope questions. When the
    routing decision implicates several scope areas at once (a multi-regime
    question, e.g. a product that is both a GI candidate and a
    classical-medicine patent question), it widens to 2 + len(matched_areas)
    (capped at 5) so the best evidence of every implicated regime survives
    the cut; without this the cap could silently drop one regime's provisions.

    Sufficiency rule (deterministic, deliberately conservative):
      sufficient = best_score >= 4 AND the best-scoring evidence includes at
      least one record from the routed scope area.
    A best score of 3 or less means only single-keyword matches were found —
    that is weak evidence regardless of how many records matched, so the
    guidance layer abstains instead of presenting tangential provisions as
    an answer.
    """
    decision = routing_decision or routing.route_query(query)
    scope_area = decision.get("scope_area") if decision.get("route") == "india_ip" else None
    matched_areas = decision.get("matched_areas") or ([scope_area] if scope_area else [])
    keywords = extract_keywords(query)
    corpus = sources if sources is not None else all_sources()

    if top_k is None:
        top_k = (
            min(5, 2 + len(matched_areas))
            if len(matched_areas) >= 2
            else DEFAULT_TOP_K
        )

    hits = []
    for record in corpus:
        score, matched = score_record(record, keywords, scope_area)
        if score >= HIT_MIN_SCORE:
            hits.append({"record": record, "score": score, "matched": matched})
    hits.sort(key=lambda hit: (-hit["score"], hit["record"]["id"]))
    hits = hits[:top_k]

    best_score = hits[0]["score"] if hits else 0
    scope_hits = [
        h for h in hits
        if matched_areas and h["record"]["scope_area"] in matched_areas
    ]

    if not hits:
        sufficient = False
        reason = "no corpus record matched the query keywords"
    elif best_score >= 4 and scope_hits:
        sufficient = True
        reason = (
            "best evidence score %d with in-scope record(s) %s"
            % (best_score, [h["record"]["id"] for h in scope_hits])
        )
    else:
        sufficient = False
        reason = (
            "evidence too weak: best score %d, %d in-scope hit(s) of %d hit(s)"
            % (best_score, len(scope_hits), len(hits))
        )

    sufficiency = {
        "sufficient": sufficient,
        "reason": reason,
        "best_score": best_score,
        "n_hits": len(hits),
        "in_scope_hit": bool(scope_hits),
    }
    return hits, sufficiency
