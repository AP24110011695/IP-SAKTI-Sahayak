"""Contract models for M1 — Main Legal AI Assistant.

Implements the shared interface contract from Plan.md §7 / MEMBER_1.md §4:
QueryRequest, QueryResponse, Citation, Message, FormulationClass. Built
independently (no imports from other members); Member 6 reconciles small
mismatches at final integration.

A valid abstention is a normal HTTP 200 response, not an error. Error
responses use the ErrorResponse codes from Plan.md §7:
VALIDATION_ERROR → 400, PROCESSING_ERROR → 502, SERVICE_UNAVAILABLE → 503.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Language = Literal["en", "hi"]
Jurisdiction = Literal["India", "International"]


class FormulationClass(str, Enum):
    """Categories owned by Member 2 (Plan.md §6, Member 2)."""

    CLASSICAL = "Classical"
    PROPRIETARY = "Proprietary"
    PHYTOPHARMACEUTICAL = "Phytopharmaceutical"
    AYURVEDA_AAHAR = "Ayurveda-Aahar"
    COSMETIC = "Cosmetic"
    NEW_DRUG = "New Drug"
    UNCERTAIN = "Uncertain"


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def _content_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message content must not be empty or whitespace")
        return v


class QueryRequest(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    query: str = Field(min_length=1, max_length=2000)
    language: Language = "en"
    jurisdiction: Jurisdiction = "India"
    formulation_class: Optional[FormulationClass] = None
    history: List[Message] = Field(default_factory=list, max_length=20)

    @field_validator("id")
    @classmethod
    def _id_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("id must not be empty or whitespace")
        return v

    @field_validator("query")
    @classmethod
    def _query_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query must not be empty or whitespace")
        return v


class Citation(BaseModel):
    """Citation metadata is copied verbatim from stored corpus entries — the
    LLM never generates any part of it."""

    id: str
    source_name: str
    source_type: str
    section: Optional[str] = None
    excerpt: str
    url: Optional[str] = None
    effective_date: Optional[str] = None


class QueryResponse(BaseModel):
    id: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    abstention: bool
    abstention_reason: Optional[str] = None
    escalation_available: bool = False
    disclaimer: str


class ErrorBody(BaseModel):
    """Plan.md §7 ErrorResponse: VALIDATION_ERROR → 400,
    PROCESSING_ERROR → 502, SERVICE_UNAVAILABLE → 503."""

    error: Literal["VALIDATION_ERROR", "PROCESSING_ERROR", "SERVICE_UNAVAILABLE"]
    message: str
    detail: Optional[list] = None


class ClassifyRequest(BaseModel):
    """POST /api/classify payload (integration, M6 Phase 2 / finding F-02).

    ``answers`` maps M2's guided question ids (sihmember2 questions.py) to
    their allowed option values. The classification itself is performed by
    the real M2 classifier via the specialist-handler seam — this model only
    carries and validates the request. Unknown question ids / values are
    rejected by M2's own validation and surface as a 400."""
    answers: Dict[str, str] = Field(default_factory=dict)
    jurisdiction: Jurisdiction = "India"
    language: Language = "en"
