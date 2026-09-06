"""Minimal integration flow: QueryRequest → route → specialist → response.

This is the mechanical foundation Phase 2 wires the real M1–M5
implementations into. It is deliberately small (~150 lines) and owns no
domain knowledge:

    1. validate the QueryRequest           → 400 VALIDATION_ERROR
    2. route to a domain (injected router; the stub router mirrors M1's
       documented heuristic — Phase 2 replaces it with M1's real routing)
    3. dispatch to the registered specialist callable
       - no specialist registered for a specialist domain → safe abstention
         (HTTP 200), mirroring M1's corpus-safety rule (never silently
         substitute unrelated corpus evidence)
       - specialist raises SpecialistUnavailable           → 503
       - specialist raises SpecialistProcessingError/other → 502
    4. validate the specialist's result
       - structurally invalid → 502 PROCESSING_ERROR (never disguised)
       - semantically unsafe (e.g. tampered citation) → safe abstention,
         mirroring M1's own withhold-on-validation-failure behavior
    5. assemble the contract-shaped QueryResponse (id echoed, standing
       disclaimer, abstention-as-200) or ClassificationResult body.

Classification flow: the contract's POST /api/classify is served by
``handle_classify``. A free-text /api/query that ROUTES to the
CLASSIFICATION domain abstains with a pointer to the guided flow — M2 is
answers-driven (its classification is made from guided answers, not free
text), so a bare query cannot honestly produce a ClassificationResult.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from . import contracts
from .stubs import DISCLAIMERS, FALLBACKS
from .stubs import SpecialistProcessingError, SpecialistUnavailable

__all__ = ["Assembler", "Outcome"]


@dataclass
class Outcome:
    """Everything the caller (and the tests) need to see."""
    status_code: int
    body: dict
    domain: Optional[str] = None
    rationale: Optional[str] = None
    notes: list = field(default_factory=list)


class Assembler:
    """Wires router + specialist registry into the public API behavior.

    router:          callable(request_dict) -> (domain, rationale)
    specialists:     {domain: callable(request_dict) -> result dict}
                     RAG Result for INDIA_IP / ABS_TK / INTERNATIONAL_IP;
                     ClassificationResult for CLASSIFICATION (via
                     handle_classify only — see module docstring).
    general_handler: optional callable for the GENERAL domain; when absent,
                     GENERAL queries abstain (the integrated app's GENERAL
                     path is M1's own corpus — M6 Phase 2 wires it).
    disclaimers / fallbacks: {"en": ..., "hi": ...} texts owned by the
                     assembling member (M1). Defaults are the Phase 1 copies
                     from stubs.py.
    """

    def __init__(
        self,
        router: Callable,
        specialists: Dict[str, Callable],
        general_handler: Optional[Callable] = None,
        disclaimers: Optional[dict] = None,
        fallbacks: Optional[dict] = None,
        escalation_available: bool = False,
    ):
        self.router = router
        self.specialists = specialists
        self.general_handler = general_handler
        self.disclaimers = disclaimers or DISCLAIMERS
        self.fallbacks = fallbacks or FALLBACKS
        self.escalation_available = escalation_available

    # -- response builders --------------------------------------------------

    def _query_response(self, request: dict, answer: str, citations: list,
                        confidence: str, confidence_score: float,
                        abstention: bool, abstention_reason: Optional[str]) -> dict:
        return {
            "id": request["id"],
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "confidence_score": confidence_score,
            "abstention": abstention,
            "abstention_reason": abstention_reason,
            "escalation_available": self.escalation_available,
            "disclaimer": self.disclaimers.get(
                request.get("language", "en"), self.disclaimers["en"]
            ),
        }

    def _abstention(self, request: dict, reason: str, answer: Optional[str] = None) -> dict:
        language = request.get("language", "en")
        text = answer if (answer is not None and answer.strip()) else self.fallbacks.get(
            language, self.fallbacks["en"]
        )
        return self._query_response(
            request,
            answer=text,
            citations=[],
            confidence="LOW",
            confidence_score=0.0,
            abstention=True,
            abstention_reason=reason,
        )

    # -- public entry points --------------------------------------------------

    def handle_query(self, request) -> Outcome:
        """POST /api/query: returns Outcome(status_code, QueryResponse|ErrorResponse)."""
        problems = contracts.validate_query_request(request)
        if problems:
            return Outcome(
                status_code=contracts.http_status_for("VALIDATION_ERROR"),
                body=contracts.error_response(
                    "VALIDATION_ERROR", "Request body failed validation.", problems
                ),
                notes=problems,
            )
        request = contracts.normalise_query_request(request)

        domain, rationale = self.router(request)

        if domain == "CLASSIFICATION":
            # Free-text queries cannot honestly produce a ClassificationResult —
            # M2 is guided-answers-driven. Abstain toward the guided flow.
            reason = (
                "classification requires the guided question flow "
                "(POST /api/classify with M2's guided answers); a free-text "
                "query cannot be classified without guessing"
            )
            return Outcome(200, self._abstention(request, reason), domain, rationale)

        if domain == "GENERAL":
            if self.general_handler is not None:
                return self._dispatch_rag(request, self.general_handler, domain, rationale)
            reason = (
                "this query needs general assistant handling, which is served "
                "by the central assistant's own corpus path in the integrated "
                "app and is not registered in this build"
            )
            return Outcome(200, self._abstention(request, reason), domain, rationale)

        specialist = self.specialists.get(domain)
        if specialist is None:
            # Corpus-safety rule (MEMBER_1.md §3): never substitute unrelated
            # corpus evidence for a missing specialist — abstain safely.
            reason = (
                f"this question belongs to the {domain} specialist domain, and "
                f"that specialist capability is not available in this build"
            )
            return Outcome(200, self._abstention(request, reason), domain, rationale)

        return self._dispatch_rag(request, specialist, domain, rationale)

    def handle_classify(self, payload) -> Outcome:
        """POST /api/classify: {answers, jurisdiction?, language?} →
        Outcome(status_code, ClassificationResult|ErrorResponse)."""
        problems = self._validate_classify_payload(payload)
        if problems:
            return Outcome(
                status_code=contracts.http_status_for("VALIDATION_ERROR"),
                body=contracts.error_response(
                    "VALIDATION_ERROR", "Classification payload failed validation.", problems
                ),
                notes=problems,
            )
        classifier = self.specialists.get("CLASSIFICATION")
        if classifier is None:
            return Outcome(
                status_code=contracts.http_status_for("SERVICE_UNAVAILABLE"),
                body=contracts.error_response(
                    "SERVICE_UNAVAILABLE",
                    "no classification capability is registered in this build",
                ),
                domain="CLASSIFICATION",
            )
        try:
            result = classifier(payload)
        except SpecialistUnavailable as exc:
            return Outcome(
                status_code=contracts.http_status_for("SERVICE_UNAVAILABLE"),
                body=contracts.error_response("SERVICE_UNAVAILABLE", str(exc)),
                domain="CLASSIFICATION",
            )
        except Exception as exc:  # specialist failure is never disguised
            return Outcome(
                status_code=contracts.http_status_for("PROCESSING_ERROR"),
                body=contracts.error_response("PROCESSING_ERROR", f"specialist failed: {exc}"),
                domain="CLASSIFICATION",
            )
        problems = contracts.validate_classification_result(result)
        if problems:
            return Outcome(
                status_code=contracts.http_status_for("PROCESSING_ERROR"),
                body=contracts.error_response(
                    "PROCESSING_ERROR",
                    "specialist returned an invalid ClassificationResult.",
                    problems,
                ),
                domain="CLASSIFICATION",
                notes=problems,
            )
        return Outcome(200, result, "CLASSIFICATION", "classify payload dispatched")

    # -- internals ------------------------------------------------------------

    @staticmethod
    def _validate_classify_payload(payload) -> list:
        if not isinstance(payload, dict):
            return ["classification payload must be a dict"]
        problems = []
        answers = payload.get("answers")
        if not isinstance(answers, dict):
            problems.append("answers must be a dict of question id → answer value")
        else:
            for key, value in answers.items():
                if not isinstance(key, str) or not key.strip():
                    problems.append(f"question id {key!r} must be a non-empty string")
                elif not isinstance(value, str) or not value.strip():
                    problems.append(f"answer for {key!r} must be a non-empty string")
        if "jurisdiction" in payload and payload["jurisdiction"] not in contracts.JURISDICTIONS:
            problems.append(
                f"jurisdiction {payload['jurisdiction']!r} must be one of "
                f"{list(contracts.JURISDICTIONS)}"
            )
        if "language" in payload and payload["language"] not in contracts.LANGUAGES:
            problems.append(
                f"language {payload['language']!r} must be one of {list(contracts.LANGUAGES)}"
            )
        return problems

    def _dispatch_rag(self, request, specialist, domain, rationale) -> Outcome:
        try:
            result = specialist(request)
        except SpecialistUnavailable as exc:
            return Outcome(
                status_code=contracts.http_status_for("SERVICE_UNAVAILABLE"),
                body=contracts.error_response("SERVICE_UNAVAILABLE", str(exc)),
                domain=domain,
                rationale=rationale,
            )
        except SpecialistProcessingError as exc:
            return Outcome(
                status_code=contracts.http_status_for("PROCESSING_ERROR"),
                body=contracts.error_response("PROCESSING_ERROR", str(exc)),
                domain=domain,
                rationale=rationale,
            )
        except Exception as exc:  # unexpected specialist failure → 502, never a fake answer
            return Outcome(
                status_code=contracts.http_status_for("PROCESSING_ERROR"),
                body=contracts.error_response(
                    "PROCESSING_ERROR", f"specialist failed unexpectedly: {exc}"
                ),
                domain=domain,
                rationale=rationale,
            )

        structural = contracts.validate_rag_result_structure(result)
        if structural:
            return Outcome(
                status_code=contracts.http_status_for("PROCESSING_ERROR"),
                body=contracts.error_response(
                    "PROCESSING_ERROR",
                    "specialist returned a structurally invalid RAG result.",
                    structural,
                ),
                domain=domain,
                rationale=rationale,
                notes=structural,
            )

        # Status is authoritative BEFORE semantic checks: a processing_error
        # result maps to 502 even when the specialist also flagged it
        # abstention=True (M5's current shape — finding F-04).
        if result["status"] == "processing_error":
            if result["citations"]:
                # A processing error must never carry citations — withhold.
                return Outcome(
                    status_code=200,
                    body=self._abstention(
                        request, "processing_error result carried citations; withheld"
                    ),
                    domain=domain,
                    rationale=rationale,
                )
            return Outcome(
                status_code=contracts.http_status_for("PROCESSING_ERROR"),
                body=contracts.error_response(
                    "PROCESSING_ERROR",
                    result.get("answer") or "the specialist reported a processing error.",
                ),
                domain=domain,
                rationale=rationale,
            )

        semantic = contracts.validate_rag_result_semantics(result)
        if semantic:
            # The specialist "answered" but unsafely (e.g. a citation that
            # fails contract validation): withhold — safe abstention, never
            # serve it. (URL-domain authority is each member's own allow-list
            # responsibility; the integration layer checks contract shape.)
            return Outcome(
                status_code=200,
                body=self._abstention(
                    request, "citation/semantic validation failed (" + "; ".join(semantic) + ")"
                ),
                domain=domain,
                rationale=rationale,
                notes=semantic,
            )

        if result["status"] == "abstained":
            return Outcome(
                status_code=200,
                body=self._abstention(request, result["abstention_reason"], answer=result["answer"]),
                domain=domain,
                rationale=rationale,
            )

        answer = result["answer"]
        return Outcome(
            status_code=200,
            body=self._query_response(
                request,
                answer=answer,
                citations=result["citations"],
                confidence=result["confidence"],
                confidence_score=float(result["confidence_score"]),
                abstention=False,
                abstention_reason=None,
            ),
            domain=domain,
            rationale=rationale,
        )
