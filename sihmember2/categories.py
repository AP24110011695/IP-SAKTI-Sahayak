"""Category and confidence vocabulary for the Member 2 formulation classifier.

Machine-readable values are stable across phases and languages: classification
results always use these English constants as ``formulation_class`` and
``confidence``. Human-readable labels (English/Hindi) live in
``regimes.CATEGORY_LABELS``; descriptive text lives in ``strings.py``.
"""

CLASSICAL = "Classical"
PROPRIETARY = "Proprietary"
PHYTOPHARMACEUTICAL = "Phytopharmaceutical"
AYURVEDA_AAHAR = "Ayurveda-Aahar"
COSMETIC = "Cosmetic"
NEW_DRUG = "New Drug"
UNCERTAIN = "Uncertain"

ALL_CATEGORIES = (
    CLASSICAL,
    PROPRIETARY,
    PHYTOPHARMACEUTICAL,
    AYURVEDA_AAHAR,
    COSMETIC,
    NEW_DRUG,
    UNCERTAIN,
)

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
