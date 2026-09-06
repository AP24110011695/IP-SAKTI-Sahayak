"""Member 4 Phase 1 — minimal deterministic retrieval seam over the ABS/TK corpus.

Deliberately simple (MEMBER_4.md section 6): token/keyword scoring over the
curated records. No vector database, no rerankers, no LLM, no network.

Behaviour:
- A query is tokenised (lowercase, stopwords removed).
- A record's score is the sum, over distinct query tokens, of the token's
  strongest field hit (keywords x3, section x2, source_name x2, excerpt x1,
  scope x1). Field echoes of the same word do not stack.
- A token matches when one is a prefix of the other with at least
  MIN_PREFIX_LEN characters (light morphology: plant~plants,
  commercialise~commercialisation).
- A query is only eligible for ABS/TK evidence if it contains at least one
  token from the ABS/TK domain lexicon (DOMAIN_LEXICON). This keeps clearly
  unrelated queries (e.g. trademark-only) from ever being answered here.
- Records with score below MIN_SCORE are not returned; a query whose best
  score is below the threshold yields no evidence (Phase 2 abstains on that
  basis). All scoring is deterministic; ties are broken by record id.
"""

from corpus import SOURCE_RECORDS

MIN_PREFIX_LEN = 5
# Requires evidence from at least two distinct query tokens (3+3) or one
# keyword hit plus another token's field hit, so a single incidental word
# (even when echoed across fields) cannot surface evidence.
MIN_SCORE = 4.5

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "can", "do",
    "does", "for", "from", "had", "has", "have", "how", "i", "if", "in",
    "into", "is", "it", "its", "me", "my", "need", "of", "on", "or", "our",
    "shall", "should", "so", "such", "that", "the", "their", "them", "there",
    "these", "they", "this", "to", "under", "want", "was", "we", "were",
    "what", "when", "which", "who", "will", "with", "would", "you", "your",
    # Jurisdiction context ("collected in India") is carried in record
    # metadata (jurisdiction field), not treated as evidence text; keeping it
    # as a query token would falsely surface India-law excerpts for queries
    # merely mentioning the country (e.g. "trademark registration in India").
    "india",
}

# ABS/TK domain gate: at least one of these tokens must appear in the query
# before any evidence is returned. Kept deliberately domain-specific; note
# that matching the gate alone is not sufficient - records must still score
# at or above MIN_SCORE for evidence to be returned.
DOMAIN_LEXICON = {
    "abs", "access", "biodiversity", "biological", "biopiracy", "bio-survey",
    "bio-utilisation", "benefit", "benefits", "cbd", "codified", "commercialisation",
    "commercialization", "commercialise", "commercialize", "consent", "cultivated",
    "derivatives", "equitable", "formulation", "formulations", "genetic",
    "herbal", "indigenous", "knowledge", "medicinal", "nagoya", "nba", "pic",
    "plant", "plants", "protocol", "resource", "resources", "sovereign",
    "tk", "tkdl", "traditional",
}


def _tokenize(text):
    tokens = []
    for raw in text.lower().replace("-", " ").replace("_", " ").split():
        raw = "".join(ch for ch in raw if ch.isalnum())
        if len(raw) >= 2 and raw not in STOPWORDS:
            tokens.append(raw)
    return tokens


def _matches(query_token, corpus_token):
    if query_token == corpus_token:
        return True
    if len(query_token) >= MIN_PREFIX_LEN and corpus_token.startswith(query_token):
        return True
    if len(corpus_token) >= MIN_PREFIX_LEN and query_token.startswith(corpus_token):
        return True
    return False


def _hits(query_tokens, text):
    """Count distinct query tokens that hit a text field."""
    if not text:
        return 0
    field_tokens = _tokenize(text)
    return sum(
        1
        for qt in query_tokens
        if any(_matches(qt, ft) for ft in field_tokens)
    )


def score_record(query_tokens, record):
    """Deterministic score of a record for the given query tokens.

    Each distinct query token contributes its *strongest* field hit only
    (keywords 3, section 2, source_name 2, excerpt 1, scope 1). Counting
    every field echo of the same word would let one incidental term (e.g.
    "register" in a trademark question) masquerade as evidence.
    """
    total = 0.0
    seen = set()
    for token in query_tokens:
        if token in seen:
            continue
        seen.add(token)
        candidates = [0.0]
        if any(
            _matches(token, joined)
            or any(_matches(token, kw_token) for kw_token in _tokenize(keyword))
            for keyword in record.get("keywords", [])
            for joined in ["".join(_tokenize(keyword))]
            if joined
        ):
            candidates.append(3.0)
        if _hits([token], record.get("section")):
            candidates.append(2.0)
        if _hits([token], record.get("source_name")):
            candidates.append(2.0)
        if _hits([token], record.get("excerpt")):
            candidates.append(1.0)
        if _hits([token], record.get("scope")):
            candidates.append(1.0)
        total += max(candidates)
    return total


def is_domain_query(query):
    """True when the query touches the ABS/TK domain at all (gate check only)."""
    tokens = _tokenize(query)
    return any(
        any(_matches(t, d) for d in DOMAIN_LEXICON)
        for t in tokens
    )


def retrieve(query, top_k=5, min_score=MIN_SCORE):
    """Return the most relevant corpus records for the query.

    Returns a list of dicts: {"record", "score"} sorted by (-score, id).
    Empty list means "no evidence in this corpus" - the caller (Phase 2)
    must abstain rather than answer from general knowledge.
    """
    query_tokens = _tokenize(query)
    if not query_tokens or not is_domain_query(query):
        return []

    scored = []
    for record in SOURCE_RECORDS:
        s = score_record(query_tokens, record)
        if s >= min_score:
            scored.append((s, record))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    return [{"record": record, "score": score} for score, record in scored[:top_k]]


def retrieved_ids(results):
    """Helper for tests/callers: ids of retrieved records in ranked order."""
    return [item["record"]["id"] for item in results]
