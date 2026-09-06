"""Conversational follow-up handling (Phase 3, MEMBER_1.md "Phase 3").

Follow-up questions are typically short and elliptical ("What about outside
India?", "And the TKDL angle?") and retrieve poorly on their own. This module
builds the effective retrieval query for the assistant flow:

- A self-contained query (more than MAX_SELF_CONTAINED_TOKENS content tokens,
  or no history) is used unchanged.
- A short query with conversation history is enriched with the content of the
  most recent user turn, so retrieval can find the evidence the conversation
  is about. The original query text is always kept at the end so its own
  tokens still count.

Grounding is unaffected: the expanded query is used only for retrieval; the
answer is still generated exclusively from the retrieved evidence, and the
LLM prompt continues to show the real question plus the history (see
generation.build_messages). Jurisdiction filtering is unaffected — the
explicit India/International toggle always wins.
"""
from __future__ import annotations

from typing import Optional, Sequence

from .models import Message
from .retrieval import tokenize

# A query with more content tokens than this is treated as self-contained;
# shorter queries are presumptively follow-ups when history exists.
MAX_SELF_CONTAINED_TOKENS = 5

# Effective retrieval queries are capped so a long prior turn cannot dominate.
MAX_EFFECTIVE_TOKENS = 40


def last_user_message(history: Sequence[Message]) -> Optional[str]:
    """The most recent user turn, or None when the history has no user turn."""
    for message in reversed(history):
        if message.role == "user":
            return message.content
    return None


def needs_context_carryover(query: str) -> bool:
    """True when the query is short enough that it likely relies on the
    conversation for its subject matter."""
    return len(tokenize(query)) <= MAX_SELF_CONTAINED_TOKENS


def effective_retrieval_query(query: str, history: Sequence[Message]) -> str:
    """Build the query used for retrieval, carrying over the most recent user
    turn for short follow-up questions. Deterministic and side-effect free."""
    if not history:
        return query
    prior = last_user_message(history)
    if not prior:
        return query
    if not needs_context_carryover(query):
        return query
    prior_tokens = tokenize(prior)
    query_tokens = tokenize(query)
    if not prior_tokens:
        return query
    kept = prior_tokens[: max(1, MAX_EFFECTIVE_TOKENS - len(query_tokens))]
    expanded = " ".join(kept + query_tokens)
    return expanded if expanded.strip() else query
