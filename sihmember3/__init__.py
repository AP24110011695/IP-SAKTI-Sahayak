"""IP-SAKTI Sahayak — Member 3: Indian IP & Regulatory Guidance.

Standalone India specialist (M3 domain):

- Phase 1 (sources.py): small, real, traceable corpus of Indian
  statutory/regulatory source records.
- Phase 2 (routing/retrieval/citations/confidence/llm/guidance): India query
  routing, deterministic evidence retrieval, grounded guidance generation
  (hosted LLM per Plan.md Section 4.5, with a deterministic evidence-only
  fallback), citations validated against stored records, confidence scoring,
  safe abstention, and practical Hindi support — all producing the project
  RAG Result shape.

Example:
    from member3 import answer_india_question
    result = answer_india_question(
        "Can I patent a classical Ayurvedic formulation from an "
        "authoritative text?"
    )
"""

from .citations import (
    CITATION_FIELDS,
    build_citation,
    build_citations,
    validate_citation,
    validate_citations,
)
from .confidence import compute_confidence
from .guidance import (
    RAG_RESULT_FIELDS,
    answer_india_question,
    validate_rag_result,
)
from .llm import HostedLLM, LLMError, get_llm_client
from .retrieval import extract_keywords, retrieve_evidence
from .routing import ROUTES, detect_language, normalize_query, route_query
from .sources import (
    JURISDICTION,
    OUT_OF_CORPUS_TOPICS,
    SCOPE_AREAS,
    SOURCE_TYPES,
    all_sources,
    find_sources,
    validate_corpus,
    validate_source_record,
)

__all__ = [
    # Phase 1 — corpus
    "JURISDICTION",
    "OUT_OF_CORPUS_TOPICS",
    "SCOPE_AREAS",
    "SOURCE_TYPES",
    "all_sources",
    "find_sources",
    "validate_corpus",
    "validate_source_record",
    # Phase 2 — routing / retrieval
    "ROUTES",
    "detect_language",
    "normalize_query",
    "route_query",
    "extract_keywords",
    "retrieve_evidence",
    # Phase 2 — citations
    "CITATION_FIELDS",
    "build_citation",
    "build_citations",
    "validate_citation",
    "validate_citations",
    # Phase 2 — confidence
    "compute_confidence",
    # Phase 2 — generation / contract
    "RAG_RESULT_FIELDS",
    "answer_india_question",
    "validate_rag_result",
    # Phase 2 — hosted LLM client
    "HostedLLM",
    "LLMError",
    "get_llm_client",
]
