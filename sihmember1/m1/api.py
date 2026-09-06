"""Public API for M1 (Plan.md §7): POST /api/query, POST /api/classify,
GET /api/health.

A valid abstention is HTTP 200 with abstention=true, never an error. Validation
failures map to 400 VALIDATION_ERROR; unexpected internal failures map to
502 PROCESSING_ERROR; an unavailable downstream service maps to 503
SERVICE_UNAVAILABLE (Plan.md §7 ErrorResponse).

/api/classify (added at integration, M6 Phase 2 — finding F-02) serves the
real M2 classifier through the specialist-handler seam: it never duplicates
classification logic. Without a registered classification handler it returns
503 SERVICE_UNAVAILABLE.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import __version__
from .assistant import (
    ProcessingError,
    handle_query,
    registered_specialist_handler,
)
from .config import get_config
from .models import ClassifyRequest, ErrorBody, QueryRequest, QueryResponse
from .routing import DOMAIN_LABELS, Domain, registered_specialist

app = FastAPI(
    title="IP-SAKTI Sahayak — M1 Main Legal AI Assistant",
    version=__version__,
    description=(
        "Central conversational assistant. Standalone mode answers from M1's "
        "own corpus; with specialists wired in (integration.app) the routed "
        "specialist domains M2–M5 serve the answer."
    ),
)


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=ErrorBody(
            error="VALIDATION_ERROR",
            message="Request body failed validation.",
            detail=[
                {
                    "loc": [str(p) for p in err.get("loc", [])],
                    "msg": err.get("msg", ""),
                }
                for err in exc.errors()
            ],
        ).model_dump(),
    )


@app.get("/api/health")
def health() -> dict:
    cfg = get_config()
    specialists = {
        domain.value: registered_specialist(domain)
        for domain in Domain
        if registered_specialist(domain) is not None
    }
    return {
        "status": "ok",
        "service": "m1-assistant",
        "version": __version__,
        "generator_mode": cfg.generator_mode,
        "specialists_wired": cfg.specialists_wired,
        "specialists": specialists,
    }


@app.post("/api/query")
def query(query_request: QueryRequest) -> QueryResponse:
    try:
        result = handle_query(query_request)
    except ProcessingError as exc:
        return JSONResponse(
            status_code=502,
            content=ErrorBody(
                error="PROCESSING_ERROR",
                message=str(exc),
            ).model_dump(),
        )
    # "abstained" is a valid outcome: HTTP 200, abstention=true.
    return result.response


@app.post("/api/classify")
def classify(classify_request: ClassifyRequest) -> JSONResponse:
    """Classify a formulation with the real M2 classifier (F-02 resolution).

    Returns the ClassificationResult on 200. 503 when no classification
    capability is registered (standalone M1); 502 when the classifier fails;
    400 is produced by request validation above."""
    handler = registered_specialist_handler(Domain.CLASSIFICATION)
    if handler is None:
        return JSONResponse(
            status_code=503,
            content=ErrorBody(
                error="SERVICE_UNAVAILABLE",
                message=(
                    "no classification capability is registered in this build "
                    "(run the integrated app: integration.adapters:app)"
                ),
            ).model_dump(),
        )
    try:
        result = handler(classify_request.model_dump())
    except ValueError as exc:
        # Input problems surfaced by the classifier (M2's ValidationError is
        # a ValueError: unknown question ids, disallowed answer values).
        return JSONResponse(
            status_code=400,
            content=ErrorBody(
                error="VALIDATION_ERROR",
                message=f"classification payload rejected: {exc}",
            ).model_dump(),
        )
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content=ErrorBody(
                error="PROCESSING_ERROR",
                message=f"classification failed: {exc}",
            ).model_dump(),
        )
    if not isinstance(result, dict) or "formulation_class" not in result:
        return JSONResponse(
            status_code=502,
            content=ErrorBody(
                error="PROCESSING_ERROR",
                message="classifier returned an invalid ClassificationResult.",
            ).model_dump(),
        )
    # "abstained"-style outcomes do not exist for classification: an
    # Uncertain result with a clarification prompt is a valid HTTP 200 body.
    return JSONResponse(status_code=200, content=result)
