"""IP-SAKTI Sahayak - Member 2 formulation classifier (Phase 1 + Phase 2).

Deterministic, rule-based classification of Ayurveda formulations into
Classical / Proprietary / Phytopharmaceutical / Ayurveda-Aahar / Cosmetic /
New Drug, with an Uncertain fallback, plus jurisdiction-aware regime mapping,
bilingual (English/Hindi) labels and one-round clarification support.
See classifier.py for the design guarantees and questions.py for the guided
question set.
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
    get_questions,
    get_question,
)
from .strings import LANGUAGES
from .regimes import INDIA, INTERNATIONAL, JURISDICTIONS, CATEGORY_LABELS
from .classifier import (
    classify,
    apply_clarification,
    validate_answers,
    validate_classification_result,
    ValidationError,
)

__all__ = [
    # categories
    "ALL_CATEGORIES",
    "CLASSICAL",
    "PROPRIETARY",
    "PHYTOPHARMACEUTICAL",
    "AYURVEDA_AAHAR",
    "COSMETIC",
    "NEW_DRUG",
    "UNCERTAIN",
    "HIGH",
    "MEDIUM",
    "LOW",
    # questions
    "UNSURE",
    "QUESTIONS",
    "Q_PRIMARY_PURPOSE",
    "Q_FOOD_EXCLUSION",
    "Q_TEXT_SOURCE",
    "Q_STANDARDISED_FRACTION",
    "Q_INGREDIENTS_KNOWN",
    "Q_NEW_INDICATION",
    "get_questions",
    "get_question",
    # context parameters
    "LANGUAGES",
    "INDIA",
    "INTERNATIONAL",
    "JURISDICTIONS",
    "CATEGORY_LABELS",
    # API
    "classify",
    "apply_clarification",
    "validate_answers",
    "validate_classification_result",
    "ValidationError",
]
