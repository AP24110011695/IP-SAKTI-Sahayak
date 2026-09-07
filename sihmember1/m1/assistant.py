"""M1 orchestration: QueryRequest -> QueryResponse.

Flow (MEMBER_1.md §1), completed in Phase 3:
  local conversational layer (clear small talk answered deterministically,
  everything else passes through untouched)
  -> intent/context handling (incl. follow-up resolution via history)
  -> routing decision -> evidence retrieval (standalone corpus)
  -> evidence sufficiency -> grounded answer -> citation mapping & validation
  -> confidence -> abstention when needed -> final response.

Integration (M6 Phase 2): after the routing decision, a wired-in specialist
handler (register_specialist_handler) serves the routed specialist domain
directly — its validated RAG Result is assembled into the QueryResponse with
the specialist's own citations and confidence. M1's standalone corpus remains
the demo path (specialists not wired) and the GENERAL-domain fallback scope.

Corpus-safety rule (MEMBER_1.md §3): when specialists are wired in
(Config.specialists_wired) and a query routes to a specialist domain with no
registered specialist, the assistant abstains instead of silently substituting
standalone-corpus evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional

from . import retrieval
from .config import (
    Config,
    DISCLAIMER_EN,
    DISCLAIMER_HI,
    FALLBACK_EN,
    FALLBACK_HI,
    SPECIALIST_UNAVAILABLE_EN,
    SPECIALIST_UNAVAILABLE_HI,
    get_config,
)
from .corpus import Evidence, load_corpus
from .conversation import local_response as local_conversational_response
from .followup import effective_retrieval_query
from .generation import GeneratedAnswer, NO_EVIDENCE_REASON, select_generator
from .models import Citation, QueryRequest, QueryResponse
from .routing import DOMAIN_LABELS, Domain, RoutingDecision, route
from .safety import (
    assert_response_safe,
    assess_sufficiency,
    confidence_from,
    map_citations,
    validate_citations,
)


class ProcessingError(Exception):
    """Unexpected internal failure — mapped to HTTP 502 PROCESSING_ERROR by
    the API layer."""


# ---------------------------------------------------------------------------
# Specialist handler registry (integration seam, M6 Phase 2).
#
# register_specialist() (m1.routing) records a human-readable specialist name;
# register_specialist_handler() records the callable M6's integration layer
# provides. Domain handlers take the QueryRequest and return the specialist's
# own RAG Result dict (ALREADY contract-validated and normalised by the
# integration wrapper — structural failures and processing_error statuses
# surface as exceptions from the handler and map to HTTP 502). The
# CLASSIFICATION entry is different by design: it takes the
# /api/classify payload dict {answers, jurisdiction, language} and returns a
# ClassificationResult — the query flow never calls it (see handle_query).
# ---------------------------------------------------------------------------

_SPECIALIST_HANDLERS: Dict[Domain, Callable] = {}


def register_specialist_handler(domain: Domain, handler: Callable) -> None:
    """Integration seam (M6): register the callable that serves a domain."""
    _SPECIALIST_HANDLERS[domain] = handler


def registered_specialist_handler(domain: Domain) -> Optional[Callable]:
    return _SPECIALIST_HANDLERS.get(domain)


@dataclass
class AssistantResult:
    response: QueryResponse
    status: str  # "ok" | "abstained" (Plan.md §7 Internal RAG Result)
    routing: RoutingDecision
    generator_used: str


def _disclaimer(language: str) -> str:
    return DISCLAIMER_HI if language == "hi" else DISCLAIMER_EN


def _fallback_text(language: str) -> str:
    return FALLBACK_HI if language == "hi" else FALLBACK_EN


def _abstention_response(
    request: QueryRequest, reason: str, answer: Optional[str] = None
) -> QueryResponse:
    response = QueryResponse(
        id=request.id,
        answer=answer or _fallback_text(request.language),
        citations=[],
        confidence="LOW",
        confidence_score=0.0,
        abstention=True,
        abstention_reason=reason,
        escalation_available=False,
        disclaimer=_disclaimer(request.language),
    )
    assert_response_safe(response)
    return response


def handle_query(
    request: QueryRequest, config: Optional[Config] = None
) -> AssistantResult:
    cfg = config or get_config()

    # 0. Local conversational layer (M6 Phase 4): clearly general small talk
    #    ("hi", "thanks", "bye", "help", "okay") is answered locally from a
    #    fixed response table and never enters legal routing. The intercept
    #    only fires when EVERY token is in the closed conversational
    #    vocabulary (m1.conversation) — any message carrying a genuine
    #    legal/IP/regulatory word falls through to the flow below unchanged.
    conversational = local_conversational_response(request)
    if conversational is not None:
        return AssistantResult(
            response=conversational,
            status="ok",
            routing=RoutingDecision(
                domain=Domain.GENERAL,
                specialist_registered=False,
                rationale=(
                    "local conversational response (closed-vocabulary small "
                    "talk, no legal/IP/regulatory scope terms)"
                ),
            ),
            generator_used="local-conversation",
        )

    # 1. Intent/context handling: short follow-up queries are resolved against
    #    the most recent user turn for routing and retrieval. The original
    #    request (real question + history) still drives the generator prompt.
    context_query = effective_retrieval_query(request.query, request.history)
    context_request = (
        request
        if context_query == request.query
        else request.model_copy(update={"query": context_query})
    )

    # 2. Routing decision — clean, swappable step (wired to M2–M5 at
    #    integration). Context-aware so follow-ups route on their subject.
    decision = route(context_request)

    # 3. Corpus-safety rule: a specialist-domain query with no available
    #    specialist must abstain, never silently fall back to the demo corpus.
    #    (The GENERAL domain IS M1's standalone fallback scope — it is exempt
    #    and, once specialists are wired in, is still answered from M1's own
    #    corpus in step 4.)
    if (
        cfg.specialists_wired
        and decision.domain is not Domain.GENERAL
        and not decision.specialist_registered
    ):
        domain_label = DOMAIN_LABELS[decision.domain]
        reason = SPECIALIST_UNAVAILABLE_EN.format(domain=domain_label)
        answer = (
            SPECIALIST_UNAVAILABLE_HI.format(domain=domain_label)
            if request.language == "hi"
            else reason
        )
        return AssistantResult(
            response=_abstention_response(request, reason, answer=answer),
            status="abstained",
            routing=decision,
            generator_used="none",
        )

    # 3.5 Specialist dispatch (integration seam, M6 Phase 2): when specialists
    #     are wired in and a handler is registered for the routed domain, the
    #     specialist's validated result IS the answer — M1's standalone corpus
    #     is never consulted for a specialist domain (corpus-safety rule).
    #     Handlers return an already-validated, already-normalised RAG Result;
    #     any handler exception is an internal failure (HTTP 502), and a
    #     specialist abstention stays a valid HTTP 200 abstention.
    if cfg.specialists_wired and decision.specialist_registered:
        if decision.domain is Domain.CLASSIFICATION:
            # M2 is guided-answers-driven: a free-text query cannot honestly
            # be classified without guessing, so the query flow abstains and
            # points at the guided classify flow (POST /api/classify).
            reason = (
                "classification requires the guided question flow (POST "
                "/api/classify with the classifier's guided answers); a "
                "free-text query cannot be classified without guessing"
            )
            return AssistantResult(
                response=_abstention_response(request, reason),
                status="abstained",
                routing=decision,
                generator_used="none",
            )
        handler = registered_specialist_handler(decision.domain)
        if handler is None:
            # Registered by name only, no callable wired: treat as unavailable.
            domain_label = DOMAIN_LABELS[decision.domain]
            reason = SPECIALIST_UNAVAILABLE_EN.format(domain=domain_label)
            return AssistantResult(
                response=_abstention_response(request, reason),
                status="abstained",
                routing=decision,
                generator_used="none",
            )
        try:
            # The follow-up-resolved context request goes to the specialist
            # (its query is what routing and the specialist's retrieval see);
            # the response keeps the original request's id.
            result = handler(context_request)
        except Exception as exc:
            raise ProcessingError(f"specialist dispatch failed: {exc}") from exc

        if result["status"] == "abstained":
            # Valid specialist abstention: HTTP 200 with the specialist's
            # reason; an empty specialist answer (M5) falls back to M1's
            # safe fallback text (finding F-06 normalisation).
            return AssistantResult(
                response=_abstention_response(
                    request, result["abstention_reason"], answer=result["answer"] or None
                ),
                status="abstained",
                routing=decision,
                generator_used="specialist",
            )

        # status "ok": assemble the QueryResponse from the specialist's own
        # answer/citations/confidence — no re-scoring (each domain's
        # confidence is authoritative for its own result, finding F-07).
        citations = [
            Citation(
                id=citation["id"],
                source_name=citation["source_name"],
                source_type=citation["source_type"],
                section=citation.get("section"),
                excerpt=citation["excerpt"],
                url=citation.get("url"),
                effective_date=citation.get("effective_date"),
            )
            for citation in result["citations"]
        ]
        response = QueryResponse(
            id=request.id,
            answer=result["answer"],
            citations=citations,
            confidence=result["confidence"],
            confidence_score=float(result["confidence_score"]),
            abstention=False,
            abstention_reason=None,
            escalation_available=False,  # escalation path is out of MVP scope
            disclaimer=_disclaimer(request.language),
        )
        try:
            assert_response_safe(response)
        except ValueError as exc:
            raise ProcessingError(f"specialist response safety check failed: {exc}") from exc
        return AssistantResult(
            response=response,
            status="ok",
            routing=decision,
            generator_used="specialist",
        )

    # 4. Standalone dev/demo path: retrieve evidence from the own corpus.
    try:
        corpus = load_corpus()
        scored = retrieval.retrieve(
            context_request,
            corpus,
            top_k=cfg.retrieval_top_k,
            min_score=cfg.min_evidence_score,
        )
    except Exception as exc:  # corpus problems are internal failures
        raise ProcessingError(f"retrieval failed: {exc}") from exc

    # 5. Evidence-sufficiency threshold: below it → abstain, not guess.
    sufficiency = assess_sufficiency(scored, cfg.sufficiency_threshold)
    if not sufficiency.sufficient:
        return AssistantResult(
            response=_abstention_response(request, sufficiency.reason),
            status="abstained",
            routing=decision,
            generator_used="none",
        )

    relevant = retrieval.keep_relevant(scored)
    evidence = [s.evidence for s in relevant]

    # 6. Grounded answer generation (hosted LLM, or extractive without a key).
    #    Any generator failure/insufficiency abstains — never a guess.
    try:
        generator = select_generator(cfg)
        generated: GeneratedAnswer = generator.generate(request, evidence)
    except Exception as exc:  # defensive: generators handle their own failures
        raise ProcessingError(f"generation failed: {exc}") from exc

    if generated.insufficient or not generated.text:
        return AssistantResult(
            response=_abstention_response(
                request, generated.reason or NO_EVIDENCE_REASON
            ),
            status="abstained",
            routing=decision,
            generator_used=generated.generator,
        )

    # 7. Citation mapping: only [E#]-tagged, stored evidence becomes a citation.
    citations = map_citations(generated.text, evidence)
    if not citations:
        return AssistantResult(
            response=_abstention_response(
                request,
                "answer could not be mapped to stored evidence; response withheld",
            ),
            status="abstained",
            routing=decision,
            generator_used=generated.generator,
        )

    # 8. Citation validation: every field must equal the stored metadata and
    #    the URL must be an authoritative https URL. Any failure → withhold.
    corpus_by_id = {ev.id: ev for ev in corpus}
    failures = validate_citations(citations, corpus_by_id)
    if failures:
        return AssistantResult(
            response=_abstention_response(
                request,
                "citation validation failed (" + "; ".join(failures) + "); "
                "response withheld",
            ),
            status="abstained",
            routing=decision,
            generator_used=generated.generator,
        )

    # 9. Confidence scoring that varies with evidence strength.
    label, score = confidence_from(relevant)
    response = QueryResponse(
        id=request.id,
        answer=generated.text,
        citations=citations,
        confidence=label,
        confidence_score=score,
        abstention=False,
        abstention_reason=None,
        escalation_available=False,  # escalation path is out of M1 standalone scope
        disclaimer=_disclaimer(request.language),
    )
    # 10. Final contract guards before serving anything.
    try:
        assert_response_safe(response)
    except ValueError as exc:
        raise ProcessingError(f"response safety check failed: {exc}") from exc
    return AssistantResult(
        response=response,
        status="ok",
        routing=decision,
        generator_used=generated.generator,
    )
