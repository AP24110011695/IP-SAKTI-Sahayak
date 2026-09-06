"""Real member adapters + wiring for the integrated application (M6 Phase 2).

This module connects the five COMPLETED workstreams through M1's routing
seam. It contains no domain logic of its own: each adapter is a thin call
into the real member implementation, followed by contract validation and the
smallest safe normalisation at the integration boundary.

Loaders / package naming (finding F-01, resolved without touching member
code):
    M1  import m1              (sihmember1 on sys.path)
    M2  import sihmember2      (the directory IS the package) — plus an
        optional legacy alias 'member2' so M2's own test suite can run
        unmodified (alias_legacy_member_packages()).
    M3  import sihmember3      (same alias support for 'member3')
    M4  sihmember4 dir on sys.path, then top-level modules (absolute imports)
    M5  sihmember5 dir on sys.path, then 'import member5'

Normalisation at the boundary (deliberate, minimal):
    - status is AUTHORITATIVE: a specialist result reporting
      status="processing_error" raises AdapterError → M1 → HTTP 502. This
      covers M5's and M4's failure paths, which set abstention=True on
      processing errors (finding F-04) — the 502 must not be disguised as a
      200 abstention.
    - a structurally invalid specialist result raises AdapterError → 502
      (never served, never converted into a fake answer).
    - a semantically unsafe "ok" result (e.g. a citation that fails contract
      validation) is WITHHELD: converted into a clean abstained result so
      M1 returns HTTP 200 with no citations — mirroring M1's own
      withhold-on-validation-failure behaviour.
    - URL-domain authority is NOT re-judged here (each member enforces its
      own authoritative-domain allow-list).
    - M4's additive tkdl_pointer passes through untouched (finding F-05).

Nothing here re-implements any member's citation/confidence/abstention
logic.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any, Callable

from . import contracts

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Domain keys used by m1.routing / m1.assistant.
DOMAIN_INDIA = "INDIA_IP"
DOMAIN_ABS_TK = "ABS_TK"
DOMAIN_INTERNATIONAL = "INTERNATIONAL_IP"
DOMAIN_CLASSIFICATION = "CLASSIFICATION"

_SPECIALIST_NAMES = {
    DOMAIN_INDIA: "sihmember3 — India IP & regulatory guidance",
    DOMAIN_ABS_TK: "sihmember4 — ABS / TKDL / traditional knowledge",
    DOMAIN_INTERNATIONAL: "sihmember5 — International IP guidance",
    DOMAIN_CLASSIFICATION: "sihmember2 — formulation classifier",
}

# Modules imported by _load_members(); populated once.
_members: dict[str, Any] = {}
_wired = False


class AdapterError(Exception):
    """A specialist failed or returned an unusable result. M1's dispatcher
    converts this into ProcessingError → HTTP 502 PROCESSING_ERROR."""


# ---------------------------------------------------------------------------
# Member loading (F-01 resolution lives here)
# ---------------------------------------------------------------------------

def _ensure_repo_root_on_path() -> None:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))


def _load_m1():
    m1_dir = str(_REPO_ROOT / "sihmember1")
    if m1_dir not in sys.path:
        sys.path.insert(0, m1_dir)
    import m1.routing
    import m1.assistant
    import m1.config
    import m1.models
    return {
        "routing": m1.routing,
        "assistant": m1.assistant,
        "config": m1.config,
        "models": m1.models,
    }


def _load_m2():
    _ensure_repo_root_on_path()
    return {"pkg": importlib.import_module("sihmember2")}


def _load_m3():
    _ensure_repo_root_on_path()
    return {"pkg": importlib.import_module("sihmember3")}


def _load_m4():
    """M4 uses absolute imports of generic module names: its own directory
    must be on sys.path for the lifetime of the process."""
    m4_dir = str(_REPO_ROOT / "sihmember4")
    if m4_dir not in sys.path:
        sys.path.insert(0, m4_dir)
    return {
        "guidance": importlib.import_module("guidance"),
        "corpus": importlib.import_module("corpus"),
    }


def _load_m5():
    m5_dir = str(_REPO_ROOT / "sihmember5")
    if m5_dir not in sys.path:
        sys.path.insert(0, m5_dir)
    return {"pkg": importlib.import_module("member5")}


def alias_legacy_member_packages() -> None:
    """F-01 compatibility shim: register the legacy package names
    'member2'/'member3' (used by M2's and M3's own test suites/READMEs) as
    aliases of the real sihmember2/sihmember3 packages, submodules included
    so isinstance identity is preserved. Member code is not modified."""
    _ensure_repo_root_on_path()
    import pkgutil

    for real_name, legacy_name in (("sihmember2", "member2"), ("sihmember3", "member3")):
        package = importlib.import_module(real_name)
        sys.modules.setdefault(legacy_name, package)
        for module_info in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{real_name}.{module_info.name}")
            sys.modules.setdefault(f"{legacy_name}.{module_info.name}", module)


def load_members(refresh: bool = False) -> dict[str, Any]:
    """Import every member workstream once and return the module handles."""
    global _members
    if _members and not refresh:
        return _members
    _members = {
        "m1": _load_m1(),
        "m2": _load_m2(),
        "m3": _load_m3(),
        "m4": _load_m4(),
        "m5": _load_m5(),
    }
    return _members


# ---------------------------------------------------------------------------
# Result validation / normalisation at the integration boundary
# ---------------------------------------------------------------------------


def _validated_rag_result(result: Any, member: str) -> dict:
    """Validate a specialist's RAG Result and apply the minimal boundary
    normalisation (see module docstring). Returns a result whose status is
    'ok' or 'abstained' only."""
    structural = contracts.validate_rag_result_structure(result)
    if structural:
        raise AdapterError(
            f"{member} returned a structurally invalid RAG result: "
            + "; ".join(structural)
        )
    # Status is authoritative (finding F-04 — M5 and M4 both set
    # abstention=True on their processing_error paths): never disguise a
    # processing error as a 200 abstention or a valid answer.
    if result["status"] == "processing_error":
        detail = result["abstention_reason"] or result["answer"] or "specialist reported a processing error"
        raise AdapterError(f"{member} processing error: {detail}")
    semantic = contracts.validate_rag_result_semantics(result)
    if semantic:
        # The specialist "answered" but unsafely — withhold (safe abstention).
        return {
            "answer": "",
            "citations": [],
            "confidence": "LOW",
            "confidence_score": 0.0,
            "abstention": True,
            "abstention_reason": (
                f"{member} result failed semantic validation ("
                + "; ".join(semantic) + "); response withheld"
            ),
            "status": "abstained",
        }
    # F-05 normalisation: the QueryResponse contract has no tkdl_pointer
    # field, so M4's additive pointer is surfaced through the answer text
    # (it is M4's own public-level pointer naming tkdl.res.in — never TKDL
    # content). For an abstention the pointer becomes the abstention answer;
    # the reason field still explains the abstention itself.
    pointer = result.get("tkdl_pointer")
    if pointer and pointer not in result["answer"]:
        result["answer"] = (
            result["answer"] + "\n\n" + pointer if result["answer"].strip() else pointer
        )
    return result


def _validated_classification_result(result: Any, member: str) -> dict:
    problems = contracts.validate_classification_result(result)
    if problems:
        raise AdapterError(
            f"{member} returned an invalid ClassificationResult: " + "; ".join(problems)
        )
    return result


# ---------------------------------------------------------------------------
# The four real adapters
# ---------------------------------------------------------------------------

def india_adapter(request) -> dict:
    """M3 — India IP & regulatory guidance (7-field RAG Result).
    ``request`` is M1's QueryRequest (or a model copy with follow-up-resolved
    query). M3 remains India-only: it abstains on international-only and
    deep-ABS questions by its own routing."""
    m3 = load_members()["m3"]["pkg"]
    result = m3.answer_india_question(
        request.query,
        language=request.language,
        jurisdiction=request.jurisdiction,
    )
    return _validated_rag_result(result, "M3")


def abs_tk_adapter(request) -> dict:
    """M4 — ABS / TKDL / traditional knowledge (8-field RAG Result; the
    additive tkdl_pointer passes through, finding F-05)."""
    guidance = load_members()["m4"]["guidance"]
    result = guidance.answer(request.query, language=request.language)
    return _validated_rag_result(result, "M4")


def international_adapter(request) -> dict:
    """M5 — International IP guidance (7-field RAG Result)."""
    m5 = load_members()["m5"]["pkg"]
    result = m5.guide(
        request.query,
        language=request.language,
        jurisdiction=request.jurisdiction,
    )
    return _validated_rag_result(result, "M5")


def classifier_adapter(payload: dict) -> dict:
    """M2 — formulation classifier (ClassificationResult). ``payload`` is the
    /api/classify body: {answers, jurisdiction, language}."""
    m2 = load_members()["m2"]["pkg"]
    result = m2.classify(
        payload.get("answers") or {},
        jurisdiction=payload.get("jurisdiction", "India"),
        language=payload.get("language", "en"),
    )
    return _validated_classification_result(result, "M2")


# ---------------------------------------------------------------------------
# Wiring into M1's seams
# ---------------------------------------------------------------------------

def wire_m1() -> dict[str, Any]:
    """Register the real specialists with M1 and flip specialists_wired ON.

    Idempotent. After wiring, m1.assistant.handle_query dispatches routed
    specialist domains to the real M3/M4/M5 (query flow) and m1.api's
    POST /api/classify serves the real M2. GENERAL-domain queries fall
    through to M1's own corpus (its standalone fallback scope).
    """
    global _wired
    members = load_members()
    routing = members["m1"]["routing"]
    assistant = members["m1"]["assistant"]
    config = members["m1"]["config"]

    handlers = {
        DOMAIN_INDIA: india_adapter,
        DOMAIN_ABS_TK: abs_tk_adapter,
        DOMAIN_INTERNATIONAL: international_adapter,
        DOMAIN_CLASSIFICATION: classifier_adapter,
    }
    for domain_key, handler in handlers.items():
        domain = routing.Domain(domain_key)
        routing.register_specialist(domain, _SPECIALIST_NAMES[domain_key])
        assistant.register_specialist_handler(domain, handler)

    # Wiring the specialists IS the act the flag describes (m1.config
    # docstring: "M6 flips it when M2–M5 are wired in"). Forcing it here
    # prevents the dangerous misconfiguration of wired handlers with the
    # corpus silently answering specialist-domain queries.
    cfg = config.get_config()
    if not cfg.specialists_wired:
        cfg.specialists_wired = True
        config.set_config(cfg)

    _wired = True
    return members


def is_wired() -> bool:
    return _wired


# ---------------------------------------------------------------------------
# Combined application entry point
# ---------------------------------------------------------------------------

def build_app():
    """Wire the real specialists and return the combined FastAPI app
    (M1's app with POST /api/query, POST /api/classify, GET /api/health)."""
    wire_m1()
    from m1.api import app as m1_app
    _attach_frontend(m1_app)
    return m1_app


def _attach_frontend(app) -> None:
    """Serve the demo frontend from the same process (integration-owned).

    Adds one read-only adapter endpoint — GET /api/classify/questions — that
    exposes Member 2's own public get_questions() (M2's README: "render the
    guided UI from get_questions(), never from hardcoded text"), and mounts
    the static frontend at "/". The /api routes are registered before the
    mount, so they take precedence; no CORS setup is needed because the UI
    is same-origin. M1–M5 logic is untouched.
    """
    from fastapi.staticfiles import StaticFiles

    @app.get("/api/classify/questions", include_in_schema=True)
    def classify_questions() -> dict:
        m2 = load_members()["m2"]["pkg"]
        questions = m2.get_questions()
        return {
            "jurisdictions": list(m2.JURISDICTIONS),
            "languages": list(m2.LANGUAGES),
            "categories": list(m2.ALL_CATEGORIES),
            "questions": questions,
        }

    frontend_dir = _REPO_ROOT / "frontend"
    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True),
                  name="frontend")


# uvicorn target:  python -m uvicorn integration.app:app --port 8000
app = build_app()
