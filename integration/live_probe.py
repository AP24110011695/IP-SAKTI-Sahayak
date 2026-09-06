"""Read-only compatibility probes against the REAL member workstreams.

Task 6 deliverable: import each member exactly as its own code expects,
exercise its public entry points OFFLINE (no network, no LLM keys — every
member's unconfigured mode is deterministic), and record what the real code
actually produces vs the target contract.

This module never modifies member files. Import errors are reported as
findings, never raised (except where noted).

Finding status values:
    pass            check satisfied
    fail            contract violation or import failure (blocks Phase 2)
    known_mismatch  recorded in member_interfaces.COMPATIBILITY_FINDINGS;
                    expected to still fail until Phase 2 resolves it
    info            informational
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

from . import contracts

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _findings():
    return []


def _record(findings, member, check, status, detail=""):
    findings.append(
        {"member": member, "check": check, "status": status, "detail": detail}
    )


# ---------------------------------------------------------------------------
# Import helpers (per member_interfaces.IMPORT_MECHANICS), with cleanup
# ---------------------------------------------------------------------------

def _import_m1():
    sys.path.insert(0, str(_REPO_ROOT / "sihmember1"))
    try:
        return importlib.import_module("m1.models"), importlib.import_module("m1.routing"), \
            importlib.import_module("m1.config")
    finally:
        sys.path.remove(str(_REPO_ROOT / "sihmember1"))


def _import_m2():
    sys.path.insert(0, str(_REPO_ROOT))
    try:
        return importlib.import_module("sihmember2")
    finally:
        sys.path.remove(str(_REPO_ROOT))


def _import_m3():
    sys.path.insert(0, str(_REPO_ROOT))
    try:
        return importlib.import_module("sihmember3")
    finally:
        sys.path.remove(str(_REPO_ROOT))


_M4_MODULES = ("corpus", "guidance", "hindi", "llm_client", "retrieval")


def _import_m4():
    """M4 uses absolute imports of generic module names — add its directory,
    import, then remove the directory AND its top-level module entries from
    sys.modules so nothing else is shadowed."""
    member4_dir = str(_REPO_ROOT / "sihmember4")
    sys.path.insert(0, member4_dir)
    imported = {}
    try:
        for name in _M4_MODULES:
            imported[name] = importlib.import_module(name)
        return imported
    finally:
        sys.path.remove(member4_dir)
        for name in _M4_MODULES:
            sys.modules.pop(name, None)


def _import_m5():
    member5_dir = str(_REPO_ROOT / "sihmember5")
    sys.path.insert(0, member5_dir)
    try:
        return importlib.import_module("member5")
    finally:
        sys.path.remove(member5_dir)


def _import_member3_with_alias():
    """Run a member package's public API under its legacy name (F-01) by
    aliasing package AND submodules in sys.modules (submodule identity
    matters for isinstance checks in their test suites)."""
    sys.path.insert(0, str(_REPO_ROOT))
    try:
        package = importlib.import_module("sihmember3")
        sys.modules["member3"] = package
        for module_info in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"sihmember3.{module_info.name}")
            sys.modules[f"member3.{module_info.name}"] = module
        return package
    finally:
        sys.path.remove(str(_REPO_ROOT))


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

def probe_m1(findings):
    member = "M1"
    try:
        models, routing, config = _import_m1()
    except Exception as exc:
        _record(findings, member, "import", "fail", f"{type(exc).__name__}: {exc}")
        return
    _record(findings, member, "import", "pass")

    # Enum values
    class_values = [c.value for c in models.FormulationClass]
    if sorted(class_values) == sorted(contracts.FORMULATION_CLASSES):
        _record(findings, member, "formulation_class enum", "pass")
    else:
        _record(findings, member, "formulation_class enum", "fail",
                f"{class_values} != {list(contracts.FORMULATION_CLASSES)}")
    if models.Language == __import__("typing").Literal["en", "hi"]:
        _record(findings, member, "language enum", "pass")
    else:
        _record(findings, member, "language enum", "fail", repr(models.Language))
    if models.Jurisdiction == __import__("typing").Literal["India", "International"]:
        _record(findings, member, "jurisdiction enum", "pass")
    else:
        _record(findings, member, "jurisdiction enum", "fail", repr(models.Jurisdiction))

    # Contract field sets
    request_fields = set(models.QueryRequest.model_fields)
    if request_fields == set(contracts.QUERY_REQUEST_FIELDS):
        _record(findings, member, "QueryRequest fields", "pass")
    else:
        _record(findings, member, "QueryRequest fields", "fail",
                f"{sorted(request_fields)}")
    response_fields = set(models.QueryResponse.model_fields)
    if response_fields == set(contracts.QUERY_RESPONSE_FIELDS):
        _record(findings, member, "QueryResponse fields", "pass")
    else:
        _record(findings, member, "QueryResponse fields", "fail",
                f"{sorted(response_fields)}")
    citation_fields = set(models.Citation.model_fields)
    if citation_fields == set(contracts.CITATION_FIELDS):
        _record(findings, member, "Citation fields", "pass")
    else:
        _record(findings, member, "Citation fields", "fail", f"{sorted(citation_fields)}")

    # Routing seam
    domain_values = sorted(d.value for d in routing.Domain)
    if domain_values == sorted(contracts.DOMAINS):
        _record(findings, member, "routing Domain enum", "pass")
    else:
        _record(findings, member, "routing Domain enum", "fail", f"{domain_values}")
    if callable(routing.register_specialist):
        _record(findings, member, "register_specialist seam", "pass")
    else:
        _record(findings, member, "register_specialist seam", "fail", "not callable")
    if hasattr(config.Config, "specialists_wired"):
        _record(findings, member, "specialists_wired flag", "pass")
    else:
        _record(findings, member, "specialists_wired flag", "fail", "missing")


def probe_m2(findings):
    member = "M2"
    try:
        m2 = _import_m2()
    except Exception as exc:
        _record(findings, member, "import", "fail", f"{type(exc).__name__}: {exc}")
        return
    _record(findings, member, "import", "pass")

    if sorted(m2.ALL_CATEGORIES) == sorted(contracts.FORMULATION_CLASSES):
        _record(findings, member, "formulation_class enum", "pass")
    else:
        _record(findings, member, "formulation_class enum", "fail",
                f"{list(m2.ALL_CATEGORIES)}")
    if tuple(m2.LANGUAGES) == contracts.LANGUAGES:
        _record(findings, member, "language enum", "pass")
    else:
        _record(findings, member, "language enum", "fail", repr(m2.LANGUAGES))
    if tuple(m2.JURISDICTIONS) == contracts.JURISDICTIONS:
        _record(findings, member, "jurisdiction enum", "pass")
    else:
        _record(findings, member, "jurisdiction enum", "fail", repr(m2.JURISDICTIONS))

    # Uncertain + clarification behavior
    try:
        result = m2.classify({})
        problems = m2.validate_classification_result(result)
        contract_problems = contracts.validate_classification_result(result)
        if result["formulation_class"] == "Uncertain" and result["needs_clarification"] \
                and result["clarification_prompt"] and not problems and not contract_problems:
            _record(findings, member, "Uncertain + clarification", "pass")
        else:
            _record(findings, member, "Uncertain + clarification", "fail",
                    f"m2 problems={problems} contract problems={contract_problems}")
    except Exception as exc:
        _record(findings, member, "Uncertain + clarification", "fail",
                f"{type(exc).__name__}: {exc}")

    # Classical → tkdl_pointer
    try:
        result = m2.classify({
            "primary_purpose": "therapeutic", "text_source": "yes",
            "standardised_fraction": "no", "ingredients_known": "yes",
            "new_indication": "no",
        })
        pointer = result.get("tkdl_pointer") or ""
        if result["formulation_class"] == "Classical" and "tkdl.res.in" in pointer \
                and "restricted" in pointer:
            _record(findings, member, "tkdl_pointer (Classical)", "pass",
                    "pointer names tkdl.res.in and the access restriction")
        else:
            _record(findings, member, "tkdl_pointer (Classical)", "fail",
                    f"class={result['formulation_class']} pointer={pointer[:60]!r}")
    except Exception as exc:
        _record(findings, member, "tkdl_pointer (Classical)", "fail",
                f"{type(exc).__name__}: {exc}")


def probe_m3(findings):
    member = "M3"
    try:
        m3 = _import_m3()
    except Exception as exc:
        _record(findings, member, "import", "fail", f"{type(exc).__name__}: {exc}")
        return
    _record(findings, member, "import", "pass")

    if sorted(m3.RAG_RESULT_FIELDS) == sorted(contracts.RAG_RESULT_FIELDS):
        _record(findings, member, "RAG Result fields", "pass")
    else:
        _record(findings, member, "RAG Result fields", "fail", f"{list(m3.RAG_RESULT_FIELDS)}")

    # Golden scenario 1 (offline template mode)
    try:
        result = m3.answer_india_question(
            "Can I patent a classical Ayurvedic formulation from an authoritative text?"
        )
        problems = m3.validate_rag_result(result)
        contract_problems = contracts.validate_rag_result(result)
        answer = result["answer"]
        if (result["status"] == "ok" and result["citations"] and not problems
                and not contract_problems and "3(p)" in answer and "tkdl" in answer.lower()):
            _record(findings, member, "golden: classical patent question", "pass",
                    f"status=ok, {len(result['citations'])} citations, "
                    "answer names Section 3(p) and TKDL")
        else:
            _record(findings, member, "golden: classical patent question", "fail",
                    f"status={result['status']} problems={problems or contract_problems}")
    except Exception as exc:
        _record(findings, member, "golden: classical patent question", "fail",
                f"{type(exc).__name__}: {exc}")

    # Cross-domain refusal (India/International separation)
    try:
        result = m3.answer_india_question("How do I file a patent under the PCT internationally?")
        if result["status"] == "abstained" and result["abstention"] \
                and result["abstention_reason"].startswith("out_of_scope_international") \
                and not result["citations"]:
            _record(findings, member, "international query refusal", "pass")
        else:
            _record(findings, member, "international query refusal", "fail",
                    f"status={result['status']} reason={result['abstention_reason']!r}")
    except Exception as exc:
        _record(findings, member, "international query refusal", "fail",
                f"{type(exc).__name__}: {exc}")

    # Golden scenario 4 (GI)
    try:
        result = m3.answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a region?"
        )
        if result["status"] == "ok" and result["citations"] \
                and "geographical indication" in result["answer"].lower():
            _record(findings, member, "golden: GI registration question", "pass")
        else:
            _record(findings, member, "golden: GI registration question", "fail",
                    f"status={result['status']}")
    except Exception as exc:
        _record(findings, member, "golden: GI registration question", "fail",
                f"{type(exc).__name__}: {exc}")


def probe_m4(findings):
    member = "M4"
    try:
        modules = _import_m4()
        guidance = modules["guidance"]
    except Exception as exc:
        _record(findings, member, "import", "fail", f"{type(exc).__name__}: {exc}")
        return
    _record(findings, member, "import", "pass",
            "absolute-import modules (corpus/guidance/hindi/llm_client/retrieval); "
            "sys.modules cleaned up")

    # Golden ABS scenario
    try:
        result = guidance.answer(
            "I want to commercialise a formulation using a plant collected in India "
            "- what approvals do I need?"
        )
        expected_fields = set(contracts.RAG_RESULT_FIELDS) | {"tkdl_pointer"}
        if (set(result) == expected_fields and result["status"] == "ok"
                and result["citations"]
                and "Biological Diversity Act" in result["answer"]
                and not contracts.validate_rag_result(result)):
            _record(findings, member, "golden: ABS commercialisation question", "pass",
                    "8-field result (adds tkdl_pointer), BD Act named")
        else:
            _record(findings, member, "golden: ABS commercialisation question", "fail",
                    f"fields={sorted(result)} status={result.get('status')} "
                    f"problems={contracts.validate_rag_result(result)}")
    except Exception as exc:
        _record(findings, member, "golden: ABS commercialisation question", "fail",
                f"{type(exc).__name__}: {exc}")

    # False-positive protection: trademark question is NOT ABS
    try:
        result = guidance.answer("How do I register a trademark for my Ayurvedic brand?")
        if result["status"] == "abstained" and "not classified as abs/tk" \
                in result["abstention_reason"].lower():
            _record(findings, member, "trademark question not flagged ABS", "pass")
        else:
            _record(findings, member, "trademark question not flagged ABS", "fail",
                    f"status={result['status']} reason={result['abstention_reason']!r}")
    except Exception as exc:
        _record(findings, member, "trademark question not flagged ABS", "fail",
                f"{type(exc).__name__}: {exc}")

    # TKDL pointer on a TK query
    try:
        result = guidance.answer(
            "My classical ayurvedic formulation is traditional knowledge - how is "
            "prior art checked?"
        )
        pointer = result.get("tkdl_pointer")
        if result["status"] in ("ok", "abstained") and isinstance(pointer, str) \
                and "tkdl.res.in" in pointer:
            _record(findings, member, "tkdl_pointer on TK query", "pass",
                    "pointer names tkdl.res.in (description only)")
        else:
            _record(findings, member, "tkdl_pointer on TK query", "fail",
                    f"status={result['status']} pointer={pointer!r}")
    except Exception as exc:
        _record(findings, member, "tkdl_pointer on TK query", "fail",
                f"{type(exc).__name__}: {exc}")


def probe_m5(findings):
    member = "M5"
    try:
        m5 = _import_m5()
    except Exception as exc:
        _record(findings, member, "import", "fail", f"{type(exc).__name__}: {exc}")
        return
    _record(findings, member, "import", "pass",
            "package 'member5' inside sihmember5 (no package at the repo dir level)")

    # Golden scenario 5: patent outside India → PCT, never Madrid/Hague
    try:
        result = m5.guide(
            "I want to file a patent for a new Ayurvedic drug outside India - "
            "what route do I use?"
        )
        answer = result["answer"]
        if (result["status"] == "ok" and result["citations"] and "PCT" in answer
                and "Madrid" not in answer and "Hague" not in answer
                and not contracts.validate_rag_result(result)):
            _record(findings, member, "golden: international patent → PCT", "pass",
                    "PCT named; Madrid/Hague absent")
        else:
            _record(findings, member, "golden: international patent → PCT", "fail",
                    f"status={result['status']} PCT={'PCT' in answer} "
                    f"Madrid={'Madrid' in answer} Hague={'Hague' in answer}")
    except Exception as exc:
        _record(findings, member, "golden: international patent → PCT", "fail",
                f"{type(exc).__name__}: {exc}")

    # Trademark self-check: Madrid not PCT
    try:
        result = m5.guide("I want to register my Ayurvedic brand name internationally")
        if (result["status"] == "ok" and "Madrid" in result["answer"]
                and "PCT" not in result["answer"]):
            _record(findings, member, "trademark → Madrid (not PCT)", "pass")
        else:
            _record(findings, member, "trademark → Madrid (not PCT)", "fail",
                    f"status={result['status']}")
    except Exception as exc:
        _record(findings, member, "trademark → Madrid (not PCT)", "fail",
                f"{type(exc).__name__}: {exc}")

    # Jurisdiction separation: India query refuses
    try:
        result = m5.guide("How do I register a GI tag for an Ayurvedic product in India?",
                          jurisdiction="India")
        if result["status"] == "abstained" and result["abstention"] is True:
            _record(findings, member, "India-jurisdiction query refused", "pass")
        else:
            _record(findings, member, "India-jurisdiction query refused", "fail",
                    f"status={result['status']}")
    except Exception as exc:
        _record(findings, member, "India-jurisdiction query refused", "fail",
                f"{type(exc).__name__}: {exc}")

    # F-06: abstention answer text is empty. An unsupported language always
    # abstains deterministically (and F-09 notes weak topical queries often
    # get answered, so language is the reliable trigger here).
    result = m5.guide("How do I renew a trademark?", language="fr",
                      jurisdiction="International")
    if result["status"] == "abstained" and result["answer"] == "":
        _record(findings, member, "abstention answer='' (F-06)", "known_mismatch",
                "M5 abstentions carry an empty answer; the assembler substitutes "
                "fallback text. Recorded in member_interfaces F-06.")
    else:
        _record(findings, member, "abstention answer='' (F-06)", "info",
                f"status={result['status']} answer_len={len(result['answer'])}")

    # F-04: generation failure → processing_error with abstention=True
    class _FailingClient:
        def generate(self, **kwargs):
            from member5.llm import GenerationError  # already importable in this process
            raise GenerationError("probe: simulated provider failure")

    try:
        result = m5.guide(
            "I want to file a patent for a new Ayurvedic drug outside India",
            client=_FailingClient(),
        )
        if result["status"] == "processing_error" and result["abstention"] is True:
            _record(findings, member, "processing_error shape (F-04)", "known_mismatch",
                    "M5 labels generation failures processing_error yet sets "
                    "abstention=True; Plan.md/M3 semantics require abstention=False. "
                    "Assembler treats status as authoritative (→ 502). Recorded as F-04.")
        else:
            _record(findings, member, "processing_error shape (F-04)", "pass",
                    f"status={result['status']} abstention={result['abstention']}")
    except Exception as exc:
        _record(findings, member, "processing_error shape (F-04)", "fail",
                f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def probe_all() -> list:
    """Run all member probes; returns the findings list (never raises for
    member-side problems — import errors are findings)."""
    findings = _findings()
    for probe in (probe_m1, probe_m2, probe_m3, probe_m4, probe_m5):
        try:
            probe(findings)
        except Exception as exc:  # probe framework failure — surface it
            _record(findings, probe.__name__, "probe crashed", "fail",
                    f"{type(exc).__name__}: {exc}")
    return findings


def summarise(findings) -> str:
    """Human-readable one-line-per-finding summary for reports."""
    lines = []
    for f in findings:
        lines.append(f"[{f['status'].upper():14s}] {f['member']:3s} {f['check']}"
                     + (f" — {f['detail']}" if f["detail"] else ""))
    return "\n".join(lines)


if __name__ == "__main__":
    results = probe_all()
    print(summarise(results))
    hard_failures = [f for f in results if f["status"] == "fail"]
    print(f"\n{len(results)} checks: "
          f"{sum(1 for f in results if f['status'] == 'pass')} pass, "
          f"{len(hard_failures)} fail, "
          f"{sum(1 for f in results if f['status'] == 'known_mismatch')} known_mismatch, "
          f"{sum(1 for f in results if f['status'] == 'info')} info")
    raise SystemExit(1 if hard_failures else 0)
