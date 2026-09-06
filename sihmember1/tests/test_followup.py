"""Follow-up handling tests (Phase 3): short elliptical queries resolve
against the most recent user turn; self-contained queries pass unchanged."""
from m1.followup import (
    effective_retrieval_query,
    last_user_message,
    needs_context_carryover,
)
from m1.models import Message


def history(*contents):
    return [Message(role="user", content=c) for c in contents]


def test_no_history_returns_query_unchanged():
    assert effective_retrieval_query("patent route?", []) == "patent route?"


def test_self_contained_query_unchanged_even_with_history():
    long_query = (
        "Can I patent a classical Ayurvedic formulation from an authoritative text?"
    )
    assert (
        effective_retrieval_query(long_query, history("What is the PCT?"))
        == long_query
    )


def test_short_followup_expands_with_last_user_turn():
    q = "What about outside India?"
    prior = (
        "Can I patent a classical Ayurvedic formulation from an authoritative text?"
    )
    expanded = effective_retrieval_query(q, history(prior))
    assert expanded != q
    # Expansion is token-based: the follow-up's own content tokens come last.
    assert expanded.split()[-2:] == ["outside", "india"]
    assert "patent" in expanded and "formulation" in expanded


def test_uses_most_recent_user_turn_skipping_assistant_turns():
    h = [
        Message(role="user", content="How do I register a GI tag for Basmati?"),
        Message(role="assistant", content="The GI Act covers registration..."),
        Message(role="user", content="I want to file a patent for my new formulation"),
        Message(role="assistant", content="Here is what the sources say..."),
    ]
    expanded = effective_retrieval_query("and the fees?", h)
    assert "fees" in expanded
    assert "formulation" in expanded  # from the most recent user turn
    assert "Basmati" not in expanded  # older turn not used


def test_history_with_only_assistant_turns_changes_nothing():
    h = [Message(role="assistant", content="Prior answer text")]
    q = "and the fees?"
    assert effective_retrieval_query(q, h) == q


def test_prior_turn_without_content_tokens_changes_nothing():
    # A prior user turn with no tokenizable content contributes nothing; the
    # query is returned unchanged.
    h = [Message(role="user", content="???")]
    q = "and the fees?"
    assert effective_retrieval_query(q, h) == q


def test_expansion_is_capped():
    long_prior = " ".join(f"topic{i}" for i in range(100))
    expanded = effective_retrieval_query("fees?", history(long_prior))
    assert len(expanded.split()) <= 45  # cap + the query tokens


def test_needs_context_carryover_threshold():
    assert needs_context_carryover("and the fees?")
    assert needs_context_carryover("What about outside India?")
    assert not needs_context_carryover(
        "Can I patent a classical Ayurvedic formulation from an authoritative text?"
    )


def test_last_user_message():
    h = [
        Message(role="user", content="first"),
        Message(role="assistant", content="reply"),
        Message(role="user", content="second"),
    ]
    assert last_user_message(h) == "second"
    assert last_user_message([]) is None
