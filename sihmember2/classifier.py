"""Deterministic formulation-classification engine (Member 2, Phase 1 + 2).

Classifies a formulation into one of

    Classical | Proprietary | Phytopharmaceutical | Ayurveda-Aahar | Cosmetic | New Drug

or returns ``Uncertain`` when the guided answers are incomplete, mutually
contradictory or otherwise insufficient.

Design guarantees
-----------------
* Deterministic and rule-based: the same answers always produce the same
  result. No LLM, randomness or network access takes part in the decision.
* Explainable and traceable: every result carries a step-by-step ``reasoning``
  trace naming the answers each rule fired on, and confidence is computed by
  re-running the same rules on hypothetical answer variations.
* Conservative on incomplete input: questions that are missing or answered
  ``"unsure"`` never cause a guess. If a discriminating answer is missing or
  unclear the result is ``Uncertain`` with ``needs_clarification=True`` and a
  concrete clarification prompt.
* Jurisdiction-aware (Phase 2): ``classify(..., jurisdiction="India"|"International")``
  attaches the jurisdiction-appropriate regime list. The classification itself
  NEVER depends on jurisdiction -- only the attached context does.
* Bilingual (Phase 2): ``classify(..., language="en"|"hi"|"hi")`` localises the
  description and clarification prompts; machine values stay stable.
* Source of truth: the category distinctions implemented here come from
  PS.md and Research.md only (the B.3 drug/food/cosmetic framework table, the
  First-Schedule classical definition, the FSSAI Ayurveda-Aahara exclusions
  and the phytopharmaceutical/new-drug definitions). Regime mappings name
  regimes; they do not give legal guidance.

ClassificationResult shape (Plan.md Section 7 contract, implemented here
independently; the fields marked (P2) are Phase 2 additive extras for M1/M6):

    formulation_class           : one of ALL_CATEGORIES (machine value, always English)
    description                 : plain-language description of the category (localised)
    relevant_regimes            : list of regime names for the requested jurisdiction
    tkdl_pointer                : TKDL pointer text, or None
    confidence                  : "HIGH" | "MEDIUM" | "LOW"
    confidence_score            : float in 0.0-1.0
    needs_clarification         : bool (True for Uncertain results and for
                                  borderline definite results where one missing
                                  answer could change the category)
    clarification_prompt        : str | None (localised)
    clarification_question_ids  : list of question ids to answer (P2)
    jurisdiction                : "India" | "International" (P2)
    language                    : "en" | "hi" (P2)
    category_labels             : {"en": ..., "hi": ...} (P2)
    suggested_questions         : category-specific follow-up questions (P2)
    reasoning                   : list of trace strings (English; developer-facing)
"""

from .categories import (
    ALL_CATEGORIES,
    CLASSICAL,
    PROPRIETARY,
    PHYTOPHARMACEUTICAL,
    AYURVEDA_AAHAR,
    COSMETIC,
    NEW_DRUG,
    UNCERTAIN,
    HIGH,
    MEDIUM,
    LOW,
)
from .questions import (
    UNSURE,
    QUESTIONS,
    Q_PRIMARY_PURPOSE,
    Q_FOOD_EXCLUSION,
    Q_TEXT_SOURCE,
    Q_STANDARDISED_FRACTION,
    Q_INGREDIENTS_KNOWN,
    Q_NEW_INDICATION,
    get_question,
)
from .strings import (
    EN,
    HI,
    LANGUAGES,
    DESCRIPTIONS,
    BLOCKING_REASONS,
    CONTRADICTION_TEXT_VS_STANDARDISED,
    PROMPT_CLASSIFY,
    PROMPT_CONFIRM,
)
from .regimes import (
    INDIA,
    INTERNATIONAL,
    JURISDICTIONS,
    REGIMES,
    CATEGORY_LABELS,
    SUGGESTED_QUESTIONS,
)

YES = "yes"
NO = "no"

_THERAPEUTIC = "therapeutic"
_FOOD = "food_wellness"
_COSMETIC_USE = "external_cosmetic"

# Allowed values per question id. Missing keys / None / "" mean "not
# answered"; UNSURE is an allowed value everywhere.
_ALLOWED_VALUES = {
    Q_PRIMARY_PURPOSE: {_THERAPEUTIC, _FOOD, _COSMETIC_USE, "other", UNSURE},
    Q_FOOD_EXCLUSION: {"none", "bhasma_or_e1", "cure_claim", UNSURE},
    Q_TEXT_SOURCE: {YES, NO, UNSURE},
    Q_STANDARDISED_FRACTION: {YES, NO, UNSURE},
    Q_INGREDIENTS_KNOWN: {YES, NO, UNSURE},
    Q_NEW_INDICATION: {YES, NO, UNSURE},
}

# Concrete (non-"unsure") values, sorted for deterministic iteration; used by
# the confidence sensitivity analysis.
_CONCRETE_VALUES = {
    question_id: sorted(values - {UNSURE})
    for question_id, values in _ALLOWED_VALUES.items()
}

_CONF_SCORES = {HIGH: 0.95, MEDIUM: 0.70, LOW: 0.45}


class ValidationError(ValueError):
    """Raised when the answer payload or request parameters are structurally
    invalid.

    This covers: not a mapping, unknown question ids, answer values outside
    the allowed set, and unknown jurisdiction/language values. Incomplete
    answers (missing keys, None, empty string, "unsure") are NOT validation
    errors -- they classify safely as Uncertain.
    """


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def validate_answers(answers):
    """Validate and normalise the answer payload.

    Returns a new dict containing only known question ids with normalised
    (stripped, lowercased) values; unanswered entries are dropped.
    Raises ValidationError for structurally invalid payloads.
    """
    if answers is None:
        return {}
    if not isinstance(answers, dict):
        raise ValidationError(
            "answers must be a dict mapping question id to answer value, "
            "got %s" % type(answers).__name__
        )
    normalized = {}
    for key, value in answers.items():
        if key not in _ALLOWED_VALUES:
            raise ValidationError(
                "unknown question id %r; valid ids: %s"
                % (key, sorted(_ALLOWED_VALUES))
            )
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValidationError(
                "answer for %r must be a string or None, got %s"
                % (key, type(value).__name__)
            )
        cleaned = value.strip().lower()
        if cleaned == "":
            continue  # empty answer is treated as "not answered"
        if cleaned not in _ALLOWED_VALUES[key]:
            raise ValidationError(
                "invalid value %r for %r; allowed values: %s"
                % (value, key, sorted(_ALLOWED_VALUES[key]))
            )
        normalized[key] = cleaned
    return normalized


class _Consulted(dict):
    """Answer mapping that records which questions the decision rules read.

    Only ``.get`` accesses count as reads; the decision code must use
    ``.get`` exclusively so the confidence sensitivity analysis knows which
    questions actually influenced the outcome.
    """

    def __init__(self, data):
        super().__init__(data)
        self.consulted = set()

    def get(self, key, default=None):
        self.consulted.add(key)
        return super().get(key, default)


# ---------------------------------------------------------------------------
# Deterministic decision rules (classification NEVER depends on jurisdiction
# or language -- those only affect the attached context)
# ---------------------------------------------------------------------------

def _outcome(category, trace, blocking=None, contradiction=False,
             notes=None, cap_medium=False):
    return {
        "category": category,
        "trace": trace,
        "blocking": blocking or [],
        "contradiction": contradiction,
        "notes": notes or [],
        "cap_medium": cap_medium,
    }


def _decide(a):
    """Run the deterministic decision rules.

    ``a`` is a ``_Consulted`` mapping of normalised answers. Returns an
    outcome dict with the category, the reasoning trace, and (for Uncertain
    results) which question ids block the decision.
    """
    trace = []
    purpose = a.get(Q_PRIMARY_PURPOSE)
    new_indication = a.get(Q_NEW_INDICATION)
    trace.append("primary_purpose=%s" % (repr(purpose) if purpose else "not answered"))

    # Root discriminator: without a usable purpose we cannot even choose a
    # regulatory track (medicine vs food vs cosmetic).
    if purpose not in (_THERAPEUTIC, _FOOD, _COSMETIC_USE):
        trace.append(
            "primary purpose missing, 'unsure' or 'other' -> cannot choose "
            "between the medicine, food and cosmetic tracks"
        )
        return _outcome(UNCERTAIN, trace=trace, blocking=[Q_PRIMARY_PURPOSE])

    # Any definitive treatment/cure claim puts the product on the drug track:
    # products making treatment/cure claims fall under the Drugs and
    # Cosmetics Act, not FSSAI food or cosmetic rules (Research.md B.3.c).
    cure_claim = new_indication == YES
    if cure_claim:
        trace.append(
            "new_indication='yes' -> a definitive treatment/cure claim puts "
            "the product on the drug track"
        )

    if purpose == _COSMETIC_USE and not cure_claim:
        trace.append("external cosmetic use with no therapeutic claim -> Cosmetic")
        return _outcome(COSMETIC, trace=trace)

    if purpose == _FOOD and not cure_claim:
        exclusion = a.get(Q_FOOD_EXCLUSION)
        trace.append("food_exclusion=%s" % (repr(exclusion) if exclusion else "not answered"))
        if exclusion == "none":
            trace.append(
                "presented as food with no bhasma/pishti, no Schedule E-1 herbs "
                "and no cure claims -> Ayurveda-Aahar"
            )
            return _outcome(AYURVEDA_AAHAR, trace=trace)
        if exclusion in ("bhasma_or_e1", "cure_claim"):
            trace.append(
                "contains bhasma/pishti or Schedule E-1 herbs, or carries cure "
                "claims -> excluded from the FSSAI food category; falls under "
                "the Drugs and Cosmetics Act (drug track)"
            )
        else:
            trace.append(
                "food_exclusion missing or 'unsure' -> cannot safely apply the "
                "Ayurveda-Aahar (food) category"
            )
            return _outcome(UNCERTAIN, trace=trace, blocking=[Q_FOOD_EXCLUSION])

    # ---- drug track (therapeutic purpose, or food/cosmetic with cure claims
    #      or excluded substances) ----
    standardised = a.get(Q_STANDARDISED_FRACTION)
    text_source = a.get(Q_TEXT_SOURCE)
    trace.append(
        "standardised_fraction=%s; text_source=%s"
        % (repr(standardised) if standardised else "not answered",
           repr(text_source) if text_source else "not answered")
    )

    if standardised == YES and text_source == YES:
        trace.append(
            "answers conflict: a product cannot both be reproduced unchanged "
            "from an authoritative text and be a standardised fraction with "
            "defined active markers"
        )
        return _outcome(
            UNCERTAIN,
            trace=trace,
            blocking=[Q_TEXT_SOURCE, Q_STANDARDISED_FRACTION],
            contradiction=True,
        )

    if standardised == YES:
        trace.append(
            "standardised plant fraction with defined active markers -> "
            "Phytopharmaceutical (CDSCO central approval as a new drug)"
        )
        return _outcome(PHYTOPHARMACEUTICAL, trace=trace)

    if text_source == YES:
        trace.append(
            "formulation reproduced unchanged from an authoritative "
            "First-Schedule text -> Classical"
        )
        notes = []
        cap = False
        if new_indication == YES:
            notes.append(
                "the formulation is classical, but a new therapeutic claim was "
                "also recorded; the formulation class stays Classical while the "
                "claim-level regulatory treatment may differ"
            )
            cap = True
        return _outcome(CLASSICAL, trace=trace, notes=notes, cap_medium=cap)

    if text_source in (None, UNSURE):
        trace.append(
            "text_source missing/unsure -> cannot separate Classical from "
            "Proprietary / Phytopharmaceutical / New Drug"
        )
        return _outcome(UNCERTAIN, trace=trace, blocking=[Q_TEXT_SOURCE])

    # text_source == "no": modified/new formulation on the drug track.
    known = a.get(Q_INGREDIENTS_KNOWN)
    trace.append("ingredients_known=%s" % (repr(known) if known else "not answered"))

    if known == NO or new_indication == YES:
        why = (
            "novel ingredients not established in Ayurvedic use"
            if known == NO
            else "a new therapeutic indication"
        )
        trace.append("%s -> New Drug (proof of safety and effectiveness required)" % why)
        return _outcome(NEW_DRUG, trace=trace)

    if known == YES and new_indication == NO:
        trace.append(
            "new formulation of known Ayurvedic ingredients with no new "
            "indication -> Proprietary medicine"
        )
        return _outcome(PROPRIETARY, trace=trace)

    if known in (None, UNSURE):
        trace.append(
            "ingredients_known missing/unsure -> cannot separate Proprietary "
            "(known ingredients) from New Drug (novel ingredients)"
        )
        return _outcome(UNCERTAIN, trace=trace, blocking=[Q_INGREDIENTS_KNOWN])

    trace.append(
        "ingredients known but the new-indication answer is missing/unsure -> "
        "cannot separate Proprietary from New Drug"
    )
    return _outcome(UNCERTAIN, trace=trace, blocking=[Q_NEW_INDICATION])


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def _assess_confidence(answers, decision):
    """Deterministic confidence assessment.

    For every question that the decision rules actually consulted but that
    was left unanswered (or answered "unsure"), re-run the rules with each of
    that question's concrete values and check whether the outcome category
    would change. Zero such sensitivities -> HIGH; one -> MEDIUM; two or
    more -> LOW. An Uncertain result is always LOW.

    A hypothetical answer that contradicts other definitive answers produces
    a contradiction-Uncertain outcome; that does not reduce the confidence of
    a definite classification (the engine would ask for clarification rather
    than reclassify). A Classical product carrying a new-indication claim is
    capped at MEDIUM because the claim sits awkwardly on a classical
    formulation.

    Returns (label, score, extra_trace, risks) where ``risks`` is a list of
    (question_id, hypothetical_value, alternative_category) tuples in
    deterministic (question declaration) order.
    """
    extra_trace = []
    if decision["category"] == UNCERTAIN:
        extra_trace.append(
            "the product could not be classified from the given answers -> confidence LOW"
        )
        return LOW, _CONF_SCORES[LOW], extra_trace, []

    risks = []
    for question in QUESTIONS:  # deterministic (declaration) order
        question_id = question["id"]
        current = answers.get(question_id)
        if current not in (None, "", UNSURE):
            continue
        if question_id not in decision["consulted"]:
            continue
        for value in _CONCRETE_VALUES[question_id]:
            alt = dict(answers)
            alt[question_id] = value
            alt_decision = _decide(_Consulted(alt))
            if (alt_decision["category"] != decision["category"]
                    and not alt_decision["contradiction"]):
                risks.append((question_id, value, alt_decision["category"]))
                break

    count = min(len(risks), 2)
    label = HIGH if count == 0 else MEDIUM if count == 1 else LOW
    if decision["cap_medium"]:
        label = MEDIUM
    score = _CONF_SCORES[label]

    for question_id, value, alt_category in risks:
        question = get_question(question_id)
        question_text = question["text"] if question else question_id
        extra_trace.append(
            "confidence reduced: the answer to \"%s\" (%s) is missing or "
            "'unsure'; answering '%s' would instead classify the product as %s"
            % (question_text, question_id, value, alt_category)
        )
    if decision["cap_medium"]:
        extra_trace.append(
            "confidence capped at MEDIUM: a new therapeutic claim was recorded "
            "alongside a classical-text formulation"
        )
    return label, score, extra_trace, risks


# ---------------------------------------------------------------------------
# Clarification prompt composition (localised)
# ---------------------------------------------------------------------------

def _question_text(question_id, language):
    question = get_question(question_id)
    if question is None:
        return question_id
    return question["text_hi"] if language == HI else question["text"]


def _reason_text(decision, language):
    if decision["contradiction"]:
        return CONTRADICTION_TEXT_VS_STANDARDISED[language]
    return None


def _compose_prompt(decision, question_ids, language, confirm):
    """Build a localised clarification/confirmation prompt.

    For the contradiction case the prompt is the conflict explanation itself;
    otherwise it lists the blocking question(s) with the reason each matters.
    """
    contradiction_reason = _reason_text(decision, language)
    if contradiction_reason is not None:
        return contradiction_reason
    template = PROMPT_CONFIRM[language] if confirm else PROMPT_CLASSIFY[language]
    parts = []
    for question_id in question_ids:
        reason = BLOCKING_REASONS[question_id][language]
        parts.append('"%s" (%s)' % (_question_text(question_id, language), reason))
    return template + " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify(answers, jurisdiction=INDIA, language=EN):
    """Classify a formulation from guided answers.

    ``answers`` is a dict mapping question id (see ``questions.py``) to one of
    its allowed values, case-insensitive. Missing keys, ``None`` and empty
    strings mean "not answered"; the literal value ``"unsure"`` means the user
    does not know. Both are safe: they lead to ``Uncertain`` plus a
    clarification prompt, never to a guess.

    ``jurisdiction`` is ``"India"`` (default) or ``"International"``. It never
    changes the classification -- only the attached ``relevant_regimes``.

    ``language`` is ``"en"`` (default) or ``"hi"``. It localises the
    description and clarification prompts; all machine values (question ids,
    option values, ``formulation_class``) are language-independent.

    ``needs_clarification`` is True when the result is Uncertain (the
    classification cannot be made) OR when the result is definite but
    borderline (at least one unanswered, decision-relevant question could
    change the category). Clear-cut results never ask for clarification.

    Returns a ClassificationResult dict (see module docstring). Raises
    ``ValidationError`` for structurally invalid payloads or parameters.
    """
    if jurisdiction not in JURISDICTIONS:
        raise ValidationError(
            "jurisdiction %r must be one of %s" % (jurisdiction, list(JURISDICTIONS))
        )
    if language not in LANGUAGES:
        raise ValidationError(
            "language %r must be one of %s" % (language, list(LANGUAGES))
        )

    normalized = validate_answers(answers)
    consulted_answers = _Consulted(normalized)
    decision = _decide(consulted_answers)
    decision["consulted"] = consulted_answers.consulted

    category = decision["category"]
    confidence_label, confidence_score, extra_trace, risks = _assess_confidence(
        normalized, decision
    )

    reasoning = list(decision["trace"]) + extra_trace
    for note in decision["notes"]:
        reasoning.append("note: %s" % note)

    if category == UNCERTAIN:
        needs_clarification = True
        clarification_ids = list(decision["blocking"])
        prompt = _compose_prompt(decision, clarification_ids, language, confirm=False)
    elif risks:
        # Definite but borderline: one or more unanswered decision-relevant
        # questions could change the category. One round of targeted
        # clarification narrows this -- clear-cut results never reach here.
        needs_clarification = True
        clarification_ids = [question_id for question_id, _, _ in risks]
        prompt = _compose_prompt(decision, clarification_ids, language, confirm=True)
    else:
        needs_clarification = False
        clarification_ids = []
        prompt = None

    return {
        "formulation_class": category,
        "description": DESCRIPTIONS[category][language],
        "relevant_regimes": list(REGIMES[jurisdiction][category]),
        "tkdl_pointer": _TKDL_POINTERS.get(category),
        "confidence": confidence_label,
        "confidence_score": confidence_score,
        "needs_clarification": needs_clarification,
        "clarification_prompt": prompt,
        "clarification_question_ids": clarification_ids,
        "jurisdiction": jurisdiction,
        "language": language,
        "category_labels": dict(CATEGORY_LABELS[category]),
        "suggested_questions": [dict(sq) for sq in SUGGESTED_QUESTIONS[category]],
        "reasoning": reasoning,
    }


def apply_clarification(answers, clarification_answers, jurisdiction=INDIA, language=EN):
    """Apply exactly one round of clarification and re-classify.

    Merges ``clarification_answers`` over ``answers`` (clarification values
    win) and classifies the merged answer set with the same jurisdiction and
    language. The one-round conversational policy -- do not keep asking after
    the clarification round -- belongs to the caller (M1); this helper only
    makes the merge and re-classification deterministic.
    """
    merged = dict(validate_answers(answers))
    merged.update(validate_answers(clarification_answers))
    return classify(merged, jurisdiction=jurisdiction, language=language)


# TKDL is pointed at, never quoted: full text is restricted to patent offices
# under NDA (Research.md D.1). URL taken from PS.md's dataset list. Relevant
# in both jurisdictions: TKDL prior-art citations are used at patent offices
# worldwide.
_TKDL_POINTERS = {
    CLASSICAL: (
        "Traditional Knowledge Digital Library (TKDL) - tkdl.res.in. TKDL "
        "documents traditional-knowledge formulations for patent-office prior-art "
        "search; full-text access is restricted (patent offices under NDA)."
    ),
}


def validate_classification_result(result):
    """Check a ClassificationResult against the contract.

    Returns a list of problems (empty list = valid). Used by the test suite
    and available to M6 for integration checks. Fields added in Phase 2 are
    validated when present.
    """
    if not isinstance(result, dict):
        return ["result must be a dict, got %s" % type(result).__name__]

    required = (
        "formulation_class",
        "description",
        "relevant_regimes",
        "tkdl_pointer",
        "confidence",
        "needs_clarification",
        "clarification_prompt",
    )
    problems = [field for field in required if field not in result]
    if problems:
        return ["missing required field(s): %s" % ", ".join(problems)]

    if result["formulation_class"] not in ALL_CATEGORIES:
        problems.append(
            "formulation_class %r is not one of %s"
            % (result["formulation_class"], list(ALL_CATEGORIES))
        )
    if not isinstance(result["description"], str) or not result["description"].strip():
        problems.append("description must be a non-empty string")

    regimes = result["relevant_regimes"]
    if not isinstance(regimes, list) or not all(
        isinstance(item, str) and item.strip() for item in regimes
    ):
        problems.append("relevant_regimes must be a list of non-empty strings")

    pointer = result["tkdl_pointer"]
    if pointer is not None and (not isinstance(pointer, str) or not pointer.strip()):
        problems.append("tkdl_pointer must be None or a non-empty string")

    if result["confidence"] not in (HIGH, MEDIUM, LOW):
        problems.append(
            "confidence %r must be one of %s" % (result["confidence"], (HIGH, MEDIUM, LOW))
        )

    # confidence_score is an additive extra: optional for contract-minimal
    # results, but validated for type/range/consistency when present.
    score = result.get("confidence_score")
    if score is not None:
        if not isinstance(score, (int, float)) or isinstance(score, bool) \
                or not 0.0 <= float(score) <= 1.0:
            problems.append("confidence_score must be a number in 0.0-1.0")
        else:
            score = float(score)
            expected = HIGH if score >= 0.85 else MEDIUM if score >= 0.60 else LOW
            if expected != result["confidence"]:
                problems.append(
                    "confidence_score %s is inconsistent with confidence label %r"
                    % (score, result["confidence"])
                )

    if not isinstance(result["needs_clarification"], bool):
        problems.append("needs_clarification must be a boolean")

    prompt = result["clarification_prompt"]
    if result["needs_clarification"]:
        if not isinstance(prompt, str) or not prompt.strip():
            problems.append(
                "clarification_prompt must be a non-empty string when "
                "needs_clarification is True"
            )
    elif prompt is not None:
        problems.append(
            "clarification_prompt must be None when needs_clarification is False"
        )

    reasoning = result.get("reasoning")
    if reasoning is not None:
        if not isinstance(reasoning, list) or not all(
            isinstance(item, str) for item in reasoning
        ):
            problems.append("reasoning must be a list of strings")

    clarification_ids = result.get("clarification_question_ids")
    if clarification_ids is not None:
        known_ids = {question["id"] for question in QUESTIONS}
        if (not isinstance(clarification_ids, list)
                or not all(item in known_ids for item in clarification_ids)):
            problems.append(
                "clarification_question_ids must be a list of known question ids"
            )
        elif result["needs_clarification"] and not clarification_ids:
            problems.append(
                "clarification_question_ids must be non-empty when "
                "needs_clarification is True"
            )
        elif not result["needs_clarification"] and clarification_ids:
            problems.append(
                "clarification_question_ids must be empty when "
                "needs_clarification is False"
            )

    jurisdiction = result.get("jurisdiction")
    if jurisdiction is not None and jurisdiction not in JURISDICTIONS:
        problems.append(
            "jurisdiction %r must be one of %s" % (jurisdiction, list(JURISDICTIONS))
        )

    language = result.get("language")
    if language is not None and language not in LANGUAGES:
        problems.append("language %r must be one of %s" % (language, list(LANGUAGES)))

    labels = result.get("category_labels")
    if labels is not None:
        if (not isinstance(labels, dict)
                or not isinstance(labels.get("en"), str) or not labels.get("en").strip()
                or not isinstance(labels.get("hi"), str) or not labels.get("hi").strip()):
            problems.append("category_labels must provide non-empty 'en' and 'hi' labels")

    suggested = result.get("suggested_questions")
    if suggested is not None:
        if not isinstance(suggested, list):
            problems.append("suggested_questions must be a list")
        else:
            for entry in suggested:
                if (not isinstance(entry, dict)
                        or not isinstance(entry.get("id"), str) or not entry.get("id").strip()
                        or not isinstance(entry.get("en"), str) or not entry.get("en").strip()
                        or not isinstance(entry.get("hi"), str) or not entry.get("hi").strip()):
                    problems.append(
                        "each suggested question needs non-empty 'id', 'en' and 'hi'"
                    )
                    break

    return problems
