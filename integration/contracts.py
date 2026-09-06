"""Target integration contracts for IP-SAKTI Sahayak (Plan.md §7 / MEMBER_6.md §3).

Pure stdlib — no dependency on any member workstream, so every member's dict
output can be validated mechanically at integration time.

Every ``validate_*`` function returns a list of human-readable problem
strings; an EMPTY list means the payload satisfies the contract.

Validation policy (deliberate, documented — do not "fix" without reading):

- REQUIRED fields must be present with the right type. Extra/unknown fields
  are tolerated and ignored: M2 appends additive Phase-2 fields to
  ClassificationResult and M4 appends ``tkdl_pointer`` to the RAG Result, and
  forward-compatibility beats strictness at the integration seam. (M3's own
  ``validate_rag_result`` is stricter — exact-7 keys — and stays the
  authority for M3's own output; this module is the cross-member contract.)
- ``confidence`` labels are enum-checked; ``confidence_score`` is only
  range-checked (0.0–1.0). Label↔score THRESHOLDS are member-specific
  (M2: HIGH ≥ 0.85, M5 abstains below 0.65, M1: HIGH ≥ 0.5 …) and are
  deliberately NOT harmonised here — see member_interfaces.
- A valid abstention is HTTP 200, never an error (Plan.md §7). Error codes:
  VALIDATION_ERROR → 400, PROCESSING_ERROR → 502, SERVICE_UNAVAILABLE → 503.
- ``status`` is authoritative for RAG results: a result labelled
  ``processing_error`` is never a valid answer, whatever its other fields say
  (M5 currently labels such results ``abstention: True`` — detected here,
  recorded in member_interfaces.COMPATIBILITY_FINDINGS).
- Citation URLs are shape-checked here (must be http(s)); domain
  authoritativeness is enforced by each member's own allow-list
  (e.g. sihmember1/m1/corpus.ALLOWED_SOURCE_DOMAINS) — the integration layer
  never judges which domains are authoritative.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Target vocabulary (Plan.md §7)
# ---------------------------------------------------------------------------

LANGUAGES = ("en", "hi")
JURISDICTIONS = ("India", "International")
FORMULATION_CLASSES = (
    "Classical",
    "Proprietary",
    "Phytopharmaceutical",
    "Ayurveda-Aahar",
    "Cosmetic",
    "New Drug",
    "Uncertain",
)
CONFIDENCE_LEVELS = ("HIGH", "MEDIUM", "LOW")
RAG_STATUSES = ("ok", "abstained", "processing_error")
ROLES = ("user", "assistant")
ERROR_CODES = ("VALIDATION_ERROR", "PROCESSING_ERROR", "SERVICE_UNAVAILABLE")

ERROR_HTTP_STATUS = {
    "VALIDATION_ERROR": 400,
    "PROCESSING_ERROR": 502,
    "SERVICE_UNAVAILABLE": 503,
}

# Domain vocabulary mirroring m1.routing.Domain (the routing seam M6 wires
# in Phase 2). Kept as plain strings so the harness has no M1 import.
DOMAINS = (
    "INDIA_IP",
    "ABS_TK",
    "INTERNATIONAL_IP",
    "CLASSIFICATION",
    "GENERAL",
)

QUERY_REQUEST_FIELDS = (
    "id",
    "query",
    "language",
    "jurisdiction",
    "formulation_class",
    "history",
)
QUERY_RESPONSE_FIELDS = (
    "id",
    "answer",
    "citations",
    "confidence",
    "confidence_score",
    "abstention",
    "abstention_reason",
    "escalation_available",
    "disclaimer",
)
CITATION_FIELDS = (
    "id",
    "source_name",
    "source_type",
    "section",
    "excerpt",
    "url",
    "effective_date",
)
CLASSIFICATION_RESULT_FIELDS = (
    "formulation_class",
    "description",
    "relevant_regimes",
    "tkdl_pointer",
    "confidence",
    "needs_clarification",
    "clarification_prompt",
)
RAG_RESULT_FIELDS = (
    "answer",
    "citations",
    "confidence",
    "confidence_score",
    "abstention",
    "abstention_reason",
    "status",
)

_DEFAULT_LANGUAGE = "en"
_DEFAULT_JURISDICTION = "India"


# ---------------------------------------------------------------------------
# Small type helpers
# ---------------------------------------------------------------------------

def _is_str(value) -> bool:
    return isinstance(value, str)


def _is_nonempty_str(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _is_number(value) -> bool:
    # bool is a subclass of int — exclude it explicitly.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_bool(value) -> bool:
    return isinstance(value, bool)


def _missing(payload: dict, fields) -> list:
    return [f"missing required field: {field}" for field in fields if field not in payload]


# ---------------------------------------------------------------------------
# ErrorResponse (Plan.md §7)
# ---------------------------------------------------------------------------

def validate_error_response(payload) -> list:
    """Validate an ErrorResponse body: {error, message[, detail]}."""
    if not isinstance(payload, dict):
        return ["error response must be a dict"]
    problems = _missing(payload, ("error", "message"))
    if problems:
        return problems
    if payload["error"] not in ERROR_CODES:
        problems.append(
            f"error code {payload['error']!r} is not one of {list(ERROR_CODES)}"
        )
    if not _is_nonempty_str(payload["message"]):
        problems.append("message must be a non-empty string")
    if "detail" in payload and payload["detail"] is not None and not isinstance(payload["detail"], list):
        problems.append("detail must be a list or null")
    return problems


def error_response(code: str, message: str, detail=None) -> dict:
    """Build a contract-shaped ErrorResponse body."""
    body = {"error": code, "message": message}
    if detail is not None:
        body["detail"] = detail
    return body


def http_status_for(code: str) -> int:
    """Map an ErrorResponse code to its HTTP status (Plan.md §7)."""
    if code not in ERROR_HTTP_STATUS:
        raise ValueError(f"unknown error code {code!r}")
    return ERROR_HTTP_STATUS[code]


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------

def validate_citation(citation) -> list:
    """Validate one Citation against the contract shape.

    id / source_name / source_type / excerpt are required non-empty strings;
    section / url / effective_date may be None (M1's Citation model declares
    them Optional; M3/M4/M5 always populate all seven from stored records).
    URLs are shape-checked only (http/https) — domain authority is each
    member's own allow-list responsibility.
    """
    if not isinstance(citation, dict):
        return [f"citation must be a dict, got {type(citation).__name__}"]
    problems = _missing(citation, ("id", "source_name", "source_type", "excerpt"))
    if problems:
        return problems
    for field in ("id", "source_name", "source_type", "excerpt"):
        if not _is_nonempty_str(citation[field]):
            problems.append(f"citation field {field!r} must be a non-empty string")
    for field in ("section", "url", "effective_date"):
        value = citation.get(field)
        if value is not None and not _is_str(value):
            problems.append(f"citation field {field!r} must be a string or null")
    url = citation.get("url")
    if isinstance(url, str) and not (url.startswith("http://") or url.startswith("https://")):
        problems.append(f"citation url {url!r} is not an http(s) URL")
    return problems


def validate_citation_list(citations) -> list:
    """Validate a list of citations, flagging duplicate citation ids."""
    if not isinstance(citations, list):
        return ["citations must be a list"]
    problems = []
    seen_ids = set()
    for position, citation in enumerate(citations):
        for problem in validate_citation(citation):
            problems.append(f"citations[{position}]: {problem}")
        if isinstance(citation, dict):
            cid = citation.get("id")
            if cid is not None:
                if cid in seen_ids:
                    problems.append(f"citations[{position}]: duplicate citation id {cid!r}")
                seen_ids.add(cid)
    return problems


# ---------------------------------------------------------------------------
# QueryRequest / QueryResponse
# ---------------------------------------------------------------------------

def _validate_message(message, position: int) -> list:
    prefix = f"history[{position}]"
    if not isinstance(message, dict):
        return [f"{prefix} must be a dict"]
    problems = [f"{prefix}: {problem}" for problem in _missing(message, ("role", "content"))]
    if "role" in message and message["role"] not in ROLES:
        problems.append(f"{prefix}: role {message['role']!r} must be one of {list(ROLES)}")
    if "content" in message and not _is_nonempty_str(message["content"]):
        problems.append(f"{prefix}: content must be a non-empty string")
    return problems


def validate_query_request(payload) -> list:
    """Validate a QueryRequest payload.

    id and query are required non-empty strings. language / jurisdiction /
    formulation_class / history are optional (M1 applies defaults: en, India,
    None, []), but if present they must be contract-valid — an INVALID value
    is always a problem even where omission would default.
    """
    if not isinstance(payload, dict):
        return [f"query request must be a dict, got {type(payload).__name__}"]
    problems = _missing(payload, ("id", "query"))
    if "id" in payload and not _is_nonempty_str(payload["id"]):
        problems.append("id must be a non-empty string")
    if "query" in payload and not _is_nonempty_str(payload["query"]):
        problems.append("query must be a non-empty string")
    if "language" in payload and payload["language"] not in LANGUAGES:
        problems.append(f"language {payload['language']!r} must be one of {list(LANGUAGES)}")
    if "jurisdiction" in payload and payload["jurisdiction"] not in JURISDICTIONS:
        problems.append(
            f"jurisdiction {payload['jurisdiction']!r} must be one of {list(JURISDICTIONS)}"
        )
    if "formulation_class" in payload and payload["formulation_class"] is not None:
        if payload["formulation_class"] not in FORMULATION_CLASSES:
            problems.append(
                f"formulation_class {payload['formulation_class']!r} must be one of "
                f"{list(FORMULATION_CLASSES)} or null"
            )
    if "history" in payload and payload["history"] is not None:
        history = payload["history"]
        if not isinstance(history, list):
            problems.append("history must be a list of messages")
        else:
            for position, message in enumerate(history):
                problems.extend(_validate_message(message, position))
    return problems


def validate_query_response(payload) -> list:
    """Validate a QueryResponse payload (the public /api/query body).

    Consistency rules enforced (mirroring M1's own safety guards, which
    M3/M4/M5 also satisfy):
    - abstention=True → non-empty abstention_reason, NO citations;
    - abstention=False → abstention_reason is null and the answer is non-empty;
    - every citation in the list is contract-valid, no duplicate ids.
    """
    if not isinstance(payload, dict):
        return [f"query response must be a dict, got {type(payload).__name__}"]
    problems = _missing(payload, QUERY_RESPONSE_FIELDS)
    if problems:
        return problems
    if not _is_nonempty_str(payload["id"]):
        problems.append("id must be a non-empty string")
    if not _is_str(payload["answer"]):
        problems.append("answer must be a string")
    if payload["confidence"] not in CONFIDENCE_LEVELS:
        problems.append(
            f"confidence {payload['confidence']!r} must be one of {list(CONFIDENCE_LEVELS)}"
        )
    if not _is_number(payload["confidence_score"]) or not (
        0.0 <= float(payload["confidence_score"]) <= 1.0
    ):
        problems.append("confidence_score must be a number in 0.0–1.0")
    if not _is_bool(payload["abstention"]):
        problems.append("abstention must be a boolean")
    if not _is_bool(payload["escalation_available"]):
        problems.append("escalation_available must be a boolean")
    if not _is_nonempty_str(payload["disclaimer"]):
        problems.append("disclaimer must be a non-empty string")

    abstention = payload["abstention"]
    if abstention is True:
        if not _is_nonempty_str(payload["abstention_reason"]):
            problems.append("abstention=true requires a non-empty abstention_reason")
        if payload["citations"]:
            problems.append("abstention responses must not carry citations")
    elif abstention is False:
        if payload["abstention_reason"] is not None:
            problems.append("abstention=false requires abstention_reason to be null")
        if not _is_nonempty_str(payload["answer"]):
            problems.append("abstention=false requires a non-empty answer")
    problems.extend(validate_citation_list(payload["citations"]))
    return problems


# ---------------------------------------------------------------------------
# ClassificationResult (M2)
# ---------------------------------------------------------------------------

def validate_classification_result(payload) -> list:
    """Validate a ClassificationResult (the POST /api/classify body).

    Requires the seven contract fields; tolerates and ignores M2's additive
    Phase-2 extras (confidence_score, jurisdiction, language, category_labels,
    suggested_questions, reasoning, clarification_question_ids).
    confidence_score is range-checked when present; the label↔score mapping
    is member-specific and deliberately not cross-checked.
    """
    if not isinstance(payload, dict):
        return [f"classification result must be a dict, got {type(payload).__name__}"]
    problems = _missing(payload, CLASSIFICATION_RESULT_FIELDS)
    if problems:
        return problems
    if payload["formulation_class"] not in FORMULATION_CLASSES:
        problems.append(
            f"formulation_class {payload['formulation_class']!r} must be one of "
            f"{list(FORMULATION_CLASSES)}"
        )
    if not _is_nonempty_str(payload["description"]):
        problems.append("description must be a non-empty string")
    regimes = payload["relevant_regimes"]
    if not isinstance(regimes, list) or not all(_is_nonempty_str(item) for item in regimes):
        problems.append("relevant_regimes must be a list of non-empty strings")
    pointer = payload["tkdl_pointer"]
    if pointer is not None and not _is_nonempty_str(pointer):
        problems.append("tkdl_pointer must be a non-empty string or null")
    if payload["confidence"] not in CONFIDENCE_LEVELS:
        problems.append(
            f"confidence {payload['confidence']!r} must be one of {list(CONFIDENCE_LEVELS)}"
        )
    if not _is_bool(payload["needs_clarification"]):
        problems.append("needs_clarification must be a boolean")
    prompt = payload["clarification_prompt"]
    if payload["needs_clarification"] is True and not _is_nonempty_str(prompt):
        problems.append(
            "needs_clarification=true requires a non-empty clarification_prompt"
        )
    elif payload["needs_clarification"] is False and prompt is not None:
        problems.append(
            "needs_clarification=false requires clarification_prompt to be null"
        )
    score = payload.get("confidence_score")
    if score is not None and (
        not _is_number(score) or not 0.0 <= float(score) <= 1.0
    ):
        problems.append("confidence_score must be a number in 0.0–1.0 when present")
    return problems


# ---------------------------------------------------------------------------
# Internal RAG Result (M3 / M4 / M5 — and M1's internal flow)
# ---------------------------------------------------------------------------

def validate_rag_result_structure(payload) -> list:
    """Structural check only: the seven required fields exist with the right
    types. Used by the assembler to distinguish 'specialist returned garbage'
    (→ PROCESSING_ERROR 502) from 'specialist answered unsafely' (→ abstain).
    """
    if not isinstance(payload, dict):
        return [f"RAG result must be a dict, got {type(payload).__name__}"]
    problems = _missing(payload, RAG_RESULT_FIELDS)
    if problems:
        return problems
    if not _is_str(payload["answer"]):
        problems.append("answer must be a string")
    if payload["confidence"] not in CONFIDENCE_LEVELS:
        problems.append(
            f"confidence {payload['confidence']!r} must be one of {list(CONFIDENCE_LEVELS)}"
        )
    if not _is_number(payload["confidence_score"]) or not (
        0.0 <= float(payload["confidence_score"]) <= 1.0
    ):
        problems.append("confidence_score must be a number in 0.0–1.0")
    if not _is_bool(payload["abstention"]):
        problems.append("abstention must be a boolean")
    if payload["abstention_reason"] is not None and not _is_str(payload["abstention_reason"]):
        problems.append("abstention_reason must be a string or null")
    if payload["status"] not in RAG_STATUSES:
        problems.append(
            f"status {payload['status']!r} must be one of {list(RAG_STATUSES)}"
        )
    if not isinstance(payload["citations"], list):
        problems.append("citations must be a list")
    pointer = payload.get("tkdl_pointer")
    if pointer is not None and not _is_nonempty_str(pointer):
        problems.append("tkdl_pointer (M4 additive field) must be a non-empty string or null")
    return problems


def validate_rag_result_semantics(payload) -> list:
    """Semantic/safety check: status consistency and citation content.
    Assumes validate_rag_result_structure already passed."""
    problems = []
    status = payload["status"]
    if status == "ok":
        if payload["abstention"] is not False or payload["abstention_reason"] is not None:
            problems.append("status 'ok' requires abstention=false and abstention_reason=null")
        if not _is_nonempty_str(payload["answer"]):
            problems.append("status 'ok' requires a non-empty answer")
        if not payload["citations"]:
            problems.append("status 'ok' requires at least one citation")
    elif status == "abstained":
        if payload["abstention"] is not True or not _is_nonempty_str(payload["abstention_reason"]):
            problems.append(
                "status 'abstained' requires abstention=true and a non-empty abstention_reason"
            )
        if payload["citations"]:
            problems.append("status 'abstained' must not carry citations")
    else:  # processing_error
        if payload["abstention"] is not False:
            problems.append(
                "status 'processing_error' is not an abstention (abstention must be false)"
            )
        if payload["abstention_reason"] is not None:
            problems.append("status 'processing_error' requires abstention_reason to be null")
        if payload["citations"]:
            problems.append("status 'processing_error' must not carry citations")
    if payload["citations"]:
        problems.extend(validate_citation_list(payload["citations"]))
    pointer = payload.get("tkdl_pointer")
    if pointer is not None:
        if "tkdl" not in pointer.lower() or "tkdl.res.in" not in pointer:
            problems.append(
                "tkdl_pointer must reference the TKDL portal (tkdl.res.in), "
                "never fabricated TKDL content"
            )
    return problems


def validate_rag_result(payload, allow_tkdl_pointer: bool = True) -> list:
    """Full RAG Result validation = structure + semantics.

    ``allow_tkdl_pointer`` (default True) accepts M4's additive
    ``tkdl_pointer`` field on an otherwise contract-shaped result.
    """
    problems = list(validate_rag_result_structure(payload))
    if problems:
        return problems
    problems.extend(validate_rag_result_semantics(payload))
    if not allow_tkdl_pointer and "tkdl_pointer" in payload:
        problems.append("unexpected additive field 'tkdl_pointer'")
    return problems


# ---------------------------------------------------------------------------
# QueryRequest defaulting (shared by assembler and adapters)
# ---------------------------------------------------------------------------

def normalise_query_request(payload: dict) -> dict:
    """Return a copy with the optional QueryRequest fields defaulted exactly
    as M1 defaults them (language=en, jurisdiction=India, formulation_class
    and history null/empty). Validation should run BEFORE this."""
    normalised = dict(payload)
    normalised.setdefault("language", _DEFAULT_LANGUAGE)
    normalised.setdefault("jurisdiction", _DEFAULT_JURISDICTION)
    normalised.setdefault("formulation_class", None)
    normalised.setdefault("history", [])
    return normalised
