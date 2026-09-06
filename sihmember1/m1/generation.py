"""Grounded prompt construction and answer generation for M1.

Two interchangeable generators behind one interface:

- LLMGenerator — calls a hosted LLM API (any OpenAI-compatible
  /chat/completions endpoint) per Plan.md §4.5. The prompt is grounded: the
  model may only use the numbered evidence excerpts and must attribute every
  claim to an [E#] tag. Any failure — transport error, malformed envelope,
  blank content, ungrounded text (no valid [E#] tags) or an
  INSUFFICIENT_EVIDENCE judgment — returns an "insufficient" result so the
  assistant abstains instead of guessing (Phase 2 malformed-output rule:
  don't crash, don't fabricate, don't serve ungrounded text).

- ExtractiveGenerator — deterministic, evidence-only composition used when no
  LLM API key is configured. Grounded by construction: it tags and quotes the
  retrieved evidence verbatim (Hindi renderings where available for hi
  requests) and adds nothing else.

Answers use [E#] tags matching the numbered evidence; the trust layer
(m1/safety.py) maps those tags to citations built only from stored metadata.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .config import Config
from .corpus import Evidence
from .models import Message, QueryRequest
from .safety import _TAG_RE

INSUFFICIENT_MARKER = "INSUFFICIENT_EVIDENCE"

_SYSTEM_PROMPT_TEMPLATE = """You are IP-SAKTI Sahayak, a legal INFORMATION assistant for Ayurveda intellectual property and regulatory questions. You are not a lawyer and your output is not legal advice.

STRICT RULES:
1. Use ONLY the numbered EVIDENCE excerpts provided in the user message as sources of fact.
2. Never invent statutes, sections, articles, treaty names, URLs or citation metadata.
3. Attribute each factual claim to the evidence it comes from by writing its tag, e.g. [E1]. Every factual statement must carry a tag.
4. If the EVIDENCE does not contain enough information to answer the question, reply with exactly: {marker}
5. Keep India rules and International rules separate. The user has selected jurisdiction = {jurisdiction}. Do not mix rules from the other jurisdiction into the answer.
6. Answer in {language_name}.
7. Be concise (at most ~180 words)."""

_USER_PROMPT_TEMPLATE = """CONTEXT:
- Jurisdiction selected by the user: {jurisdiction}
- Answer language: {language_name}
- Formulation class (may be absent): {formulation_class}
- Conversation so far: {history}

EVIDENCE:
{evidence_block}

QUESTION: {query}

Answer using only the EVIDENCE above. If it is not enough, reply with exactly: {marker}"""

# Abstention reasons for every failure mode of a configured LLM (Phase 2:
# don't crash, don't fabricate — abstain instead).
LLM_UNAVAILABLE_REASON = (
    "LLM generation failed or produced malformed output; abstaining rather "
    "than guessing"
)
LLM_UNGROUNDED_REASON = (
    "LLM answer was not grounded in the retrieved evidence tags; abstaining "
    "rather than serving ungrounded text"
)
MODEL_INSUFFICIENT_REASON = (
    "the generator judged the retrieved evidence insufficient to answer safely"
)
NO_EVIDENCE_REASON = "no relevant evidence in the standalone corpus"


@dataclass
class GeneratedAnswer:
    text: Optional[str]  # None when the answer must be withheld
    insufficient: bool  # True → the assistant must abstain
    generator: str  # "llm" or "extractive"
    reason: Optional[str] = None  # abstention reason when insufficient


def _language_name(language: str) -> str:
    return "Hindi (Devanagari script)" if language == "hi" else "English"


def _excerpt_for(ev: Evidence, language: str) -> str:
    """Hindi rendering when the request is Hindi and one exists; the stored
    (authoritative) English excerpt otherwise."""
    if language == "hi" and ev.text_hi:
        return ev.text_hi
    return ev.text


def _history_text(history: Sequence[Message]) -> str:
    if not history:
        return "(none)"
    return " | ".join(f"{m.role}: {m.content}" for m in history[-4:])


def build_messages(
    request: QueryRequest,
    evidence: Sequence[Evidence],
    config: Config,
) -> List[dict]:
    """Build the grounded chat messages. Evidence excerpts are tagged [E1..En]
    so the model can attribute claims without inventing citation metadata."""
    system = _SYSTEM_PROMPT_TEMPLATE.format(
        marker=INSUFFICIENT_MARKER,
        jurisdiction=request.jurisdiction,
        language_name=_language_name(request.language),
    )
    lines = []
    for i, ev in enumerate(evidence, start=1):
        lines.append(
            f"[E{i}] {ev.source_name} | {ev.section} | {_excerpt_for(ev, request.language)}"
        )
    user = _USER_PROMPT_TEMPLATE.format(
        jurisdiction=request.jurisdiction,
        language_name=_language_name(request.language),
        formulation_class=request.formulation_class.value
        if request.formulation_class
        else "(not classified)",
        history=_history_text(request.history),
        evidence_block="\n".join(lines) if lines else "(no evidence retrieved)",
        query=request.query,
        marker=INSUFFICIENT_MARKER,
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _post_json(url: str, payload: dict, api_key: str, timeout_secs: float) -> dict:
    """POST a JSON payload and return the parsed JSON response. Kept as a
    module-level function so tests can stub the transport."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_secs) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _grounded_tags(text: str, n_evidence: int) -> bool:
    """True when every [E#] tag in the text resolves to a known evidence
    index and at least one tag is present (the answer is traceable)."""
    refs = [int(m) for m in _TAG_RE.findall(text)]
    if not refs:
        return False
    return all(1 <= r <= n_evidence for r in refs)


class LLMGenerator:
    """Hosted-LLM generator (OpenAI-compatible chat completions)."""

    generator_name = "llm"

    def __init__(self, config: Config):
        self.config = config

    @property
    def _endpoint(self) -> str:
        base = self.config.llm_base_url.rstrip("/")
        return f"{base}/chat/completions"

    def _call_transport(self, messages: List[dict]) -> dict:
        return _post_json(
            self._endpoint,
            {
                "model": self.config.llm_model,
                "messages": messages,
                "temperature": 0.1,
            },
            self.config.llm_api_key,
            self.config.llm_timeout_secs,
        )

    def _extract_content(self, response: dict) -> Optional[str]:
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None
        return content if isinstance(content, str) else None

    def _insufficient(self, reason: str) -> GeneratedAnswer:
        return GeneratedAnswer(
            text=None, insufficient=True, generator=self.generator_name, reason=reason
        )

    def generate(self, request: QueryRequest, evidence: Sequence[Evidence]) -> GeneratedAnswer:
        messages = build_messages(request, evidence, self.config)
        try:
            response = self._call_transport(messages)
        except Exception:  # transport/HTTP/JSON failure → abstain, never crash
            return self._insufficient(LLM_UNAVAILABLE_REASON)
        content = self._extract_content(response)
        if content is None or not content.strip():
            return self._insufficient(LLM_UNAVAILABLE_REASON)
        text = content.strip()
        if text == INSUFFICIENT_MARKER or text.startswith(INSUFFICIENT_MARKER):
            return self._insufficient(MODEL_INSUFFICIENT_REASON)
        if not _grounded_tags(text, len(evidence)):
            return self._insufficient(LLM_UNGROUNDED_REASON)
        return GeneratedAnswer(
            text=text, insufficient=False, generator=self.generator_name
        )


class ExtractiveGenerator:
    """Deterministic evidence-only composition. Used when no LLM API key is
    configured. Grounded by construction: every block is a stored excerpt,
    tagged [E#] for citation mapping."""

    generator_name = "extractive"

    def __init__(self, config: Config):
        self.config = config

    def generate(self, request: QueryRequest, evidence: Sequence[Evidence]) -> GeneratedAnswer:
        if not evidence:
            return GeneratedAnswer(
                text=None,
                insufficient=True,
                generator=self.generator_name,
                reason=NO_EVIDENCE_REASON,
            )
        hi = request.language == "hi"
        if hi:
            intro = (
                f"आपके प्रश्न पर ({request.jurisdiction} क्षेत्र के लिए) "
                f"चुनिंदा स्रोतों में यह मिला:"
            )
        else:
            intro = (
                f"Here is what the curated sources retrieved for your question "
                f"({request.jurisdiction} jurisdiction) say:"
            )
        parts = [intro]
        english_used = False
        for i, ev in enumerate(evidence, start=1):
            if hi and not ev.text_hi:
                english_used = True
            parts.append(
                f"[E{i}] {ev.source_name}, {ev.section}: {_excerpt_for(ev, request.language)}"
            )
        if hi:
            outro = "यह केवल ऊपर दिए गए स्रोतों से ली गई सामान्य जानकारी है, कानूनी सलाह नहीं।"
            if english_used:
                outro = "(कुछ स्रोत पाठ अंग्रेज़ी में हैं।) " + outro
        else:
            outro = (
                "This is general information drawn only from the sources above, "
                "not legal advice."
            )
        parts.append(outro)
        return GeneratedAnswer(
            text="\n\n".join(parts),
            insufficient=False,
            generator=self.generator_name,
        )


def select_generator(config: Config):
    """Pick the generator from config: hosted LLM when an API key is set,
    otherwise the deterministic extractive generator."""
    return LLMGenerator(config) if config.generator_mode == "llm" else ExtractiveGenerator(config)
