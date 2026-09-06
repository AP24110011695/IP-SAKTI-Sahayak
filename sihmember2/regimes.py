"""Jurisdiction-aware regime mapping, category labels and suggested
follow-up questions (Member 2, Phase 2).

All tables are static and deterministic. They NAME regimes only -- they never
state legal conclusions, obligations, filings or advice (that is M3/M4/M5's
job). Every entry is supported by PS.md / Research.md:

- India lists: Research.md B.1 (IP regimes), B.2 (ABS), B.3 (drug/food/cosmetic
  framework), PS.md national coverage.
- International lists: Research.md Section C (TRIPS, CBD/Nagoya, GRATK, PCT,
  Madrid, Hague, Budapest, export-market regimes).

Regime names are kept in English for both languages: they are proper nouns
(statute/treaty names) and machine-readable mapping data; the multilingual
requirement covers category labels, questions and clarification prompts.
"""

from .categories import (
    CLASSICAL,
    PROPRIETARY,
    PHYTOPHARMACEUTICAL,
    AYURVEDA_AAHAR,
    COSMETIC,
    NEW_DRUG,
    UNCERTAIN,
)

INDIA = "India"
INTERNATIONAL = "International"
JURISDICTIONS = (INDIA, INTERNATIONAL)

# Shared, conditionally-worded regime strings (mapping, not guidance).
_BD_ACT = (
    "Biological Diversity Act, 2002 (as amended 2023) - ABS duties where "
    "biological resources are accessed or commercialised (NBA/SBB)"
)
_TM_ACT = "Trade Marks Act, 1999 - brand-name protection"
_DMR_ACT = (
    "Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954 - "
    "constrains therapeutic advertising claims"
)
_NAGOYA = (
    "CBD / Nagoya Protocol - ABS for genetic resources and associated "
    "traditional knowledge"
)
_PCT = "PCT - single international patent application route (national phase entry ~30/31 months)"
_TRIPS_PATENT = "TRIPS Agreement - patentability standards"

INDIA_REGIMES = {
    CLASSICAL: [
        "Drugs and Cosmetics Act, 1940 - ASU drugs (State Licensing Authority; Schedule T GMP)",
        "Patents Act, 1970 - Section 3(p) (traditional knowledge) exposure",
        "TKDL - defensive publication of traditional-knowledge formulations",
        _BD_ACT,
        _TM_ACT,
        _DMR_ACT,
    ],
    PROPRIETARY: [
        "Drugs and Cosmetics Act, 1940 - proprietary ASU medicines (State Licensing Authority + CDSCO review)",
        "Patents Act, 1970 - patentability to be assessed (Section 3(p) may apply to TK-based combinations)",
        _BD_ACT,
        _TM_ACT,
        _DMR_ACT,
    ],
    PHYTOPHARMACEUTICAL: [
        "Drugs and Cosmetics Act, 1940 - phytopharmaceutical (new drug; CDSCO central approval)",
        "Patents Act, 1970 - patentability to be assessed (Section 3(p) may apply)",
        _BD_ACT,
        _TM_ACT,
    ],
    NEW_DRUG: [
        "Drugs and Cosmetics Act, 1940 - new drug (CDSCO/DCGI approval; Phase I-III clinical trials)",
        "Patents Act, 1970 - patent potential for genuine technical advances",
        _BD_ACT,
        _TM_ACT,
        "Budapest Treaty - microorganism deposit at a recognised depository "
        "(e.g. MTCC Chandigarh), only if the formulation involves microorganisms",
    ],
    AYURVEDA_AAHAR: [
        "FSSAI - Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 (FoSCoS licensing)",
        _BD_ACT,
        _TM_ACT,
    ],
    COSMETIC: [
        "Drugs and Cosmetics Act, 1940 - Cosmetic Rules",
        _TM_ACT,
    ],
    UNCERTAIN: [],
}

INTERNATIONAL_REGIMES = {
    CLASSICAL: [
        "TRIPS Agreement - Article 27.3(b) flexibilities relevant to traditional-knowledge exclusions",
        "WIPO GRATK Treaty (2024) - patent-disclosure obligation for genetic resources "
        "and associated traditional knowledge (check WIPO for current entry-into-force status)",
        _NAGOYA,
        "TKDL - defensive publication accessible to patent offices worldwide (under NDA)",
        "Export-market product regulation - market-specific (e.g. US FDA/DSHEA, "
        "EU THMPD/Novel Food; check the target market)",
    ],
    PROPRIETARY: [
        _TRIPS_PATENT,
        _PCT,
        "Madrid System - international trademark registration",
        _NAGOYA,
        "Export-market product regulation - market-specific (check the target market)",
    ],
    PHYTOPHARMACEUTICAL: [
        _TRIPS_PATENT,
        _PCT,
        _NAGOYA,
        "Export-market product regulation - market-specific (check the target market)",
    ],
    NEW_DRUG: [
        _TRIPS_PATENT,
        _PCT,
        _NAGOYA,
        "Budapest Treaty - microorganism deposit at a recognised International "
        "Depositary Authority, only if the formulation involves microorganisms",
        "Export-market clinical and product-registration requirements - market-specific",
    ],
    AYURVEDA_AAHAR: [
        "Export-market food regulation - market-specific (e.g. US FDA/DSHEA dietary "
        "supplements, EU Novel Food Regulation)",
        "Madrid System - international trademark registration",
        _NAGOYA,
    ],
    COSMETIC: [
        "Export-market cosmetic regulation - market-specific (e.g. EU Cosmetic "
        "Regulation (EC) 1223/2009, US FD&C Act / MoCRA)",
        "Madrid System - international trademark registration",
        _NAGOYA,
    ],
    UNCERTAIN: [],
}

REGIMES = {INDIA: INDIA_REGIMES, INTERNATIONAL: INTERNATIONAL_REGIMES}

# Bilingual category labels. The machine value (formulation_class) stays the
# English key; these labels are for rendering only.
CATEGORY_LABELS = {
    CLASSICAL: {"en": "Classical", "hi": "शास्त्रीय औषधि"},
    PROPRIETARY: {"en": "Proprietary", "hi": "प्रोप्राइटरी औषधि"},
    PHYTOPHARMACEUTICAL: {"en": "Phytopharmaceutical", "hi": "फाइटो-फार्मास्यूटिकल"},
    AYURVEDA_AAHAR: {"en": "Ayurveda-Aahar", "hi": "आयुर्वेद-आहार"},
    COSMETIC: {"en": "Cosmetic", "hi": "कॉस्मेटिक"},
    NEW_DRUG: {"en": "New Drug", "hi": "नई औषधि"},
    UNCERTAIN: {"en": "Uncertain", "hi": "अनिश्चित"},
}

# Category-specific suggested follow-up questions (Phase 2). These surface
# regime-relevant context for M1 to offer next -- they ask about the product,
# they never give legal guidance. Machine-stable ids; bilingual text.
SUGGESTED_QUESTIONS = {
    CLASSICAL: [
        {
            "id": "sq_classical_text_reference",
            "en": "Which authoritative text, chapter and verse is the formulation taken from?",
            "hi": "यह योग किस प्रामाणिक ग्रंथ, अध्याय और श्लोक से लिया गया है?",
        },
        {
            "id": "sq_classical_bio_resources",
            "en": "Does the product use biological resources (herbs, plant or animal materials) collected in India?",
            "hi": "क्या उत्पाद में भारत में संग्रहीत जैविक संसाधनों (जड़ी-बूटियाँ, पादप या पशु सामग्री) का उपयोग होता है?",
        },
        {
            "id": "sq_classical_region_link",
            "en": "Is the product or its key ingredient tied to a specific region or community origin?",
            "hi": "क्या उत्पाद या उसकी प्रमुख सामग्री किसी विशेष क्षेत्र या समुदाय से जुड़ी है?",
        },
    ],
    PROPRIETARY: [
        {
            "id": "sq_proprietary_distinction",
            "en": "What distinguishes this formulation from classical-text recipes - a new combination, process or dosage form?",
            "hi": "यह योग शास्त्रीय ग्रंथों की विधियों से किस प्रकार भिन्न है - नया संयोजन, प्रक्रिया या खुराक रूप?",
        },
        {
            "id": "sq_proprietary_sourcing",
            "en": "Are the ingredients cultivated or collected from the wild?",
            "hi": "क्या सामग्री कृषि-उत्पादित हैं या जंगल से संग्रहीत की गई हैं?",
        },
        {
            "id": "sq_proprietary_brand",
            "en": "What brand name will the product be sold under?",
            "hi": "उत्पाद किस ब्रांड नाम से बेचा जाएगा?",
        },
    ],
    PHYTOPHARMACEUTICAL: [
        {
            "id": "sq_phyto_markers",
            "en": "Which plant and which active markers are used for standardisation?",
            "hi": "मानकीकरण हेतु कौन-सा पादप और कौन-से सक्रिय मार्कर उपयोग होते हैं?",
        },
        {
            "id": "sq_phyto_evidence",
            "en": "What safety or clinical evidence exists for the product so far?",
            "hi": "अब तक उत्पाद के लिए क्या सुरक्षा या नैदानिक प्रमाण उपलब्ध हैं?",
        },
    ],
    NEW_DRUG: [
        {
            "id": "sq_newdrug_evidence",
            "en": "What evidence of safety and effectiveness has been generated so far?",
            "hi": "अब तक सुरक्षा और प्रभावकारिता के क्या प्रमाण तैयार हुए हैं?",
        },
        {
            "id": "sq_newdrug_microorganism",
            "en": "Does the formulation involve any microorganism (e.g. fermented or probiotic preparations)?",
            "hi": "क्या योग में कोई सूक्ष्मजीव शामिल है (जैसे किण्वित या प्रोबायोटिक तैयारी)?",
        },
        {
            "id": "sq_newdrug_patent_plan",
            "en": "Is a patent filing planned in India or abroad?",
            "hi": "क्या भारत या विदेश में पेटेंट फाइलिंग की योजना है?",
        },
    ],
    AYURVEDA_AAHAR: [
        {
            "id": "sq_aahar_category_a",
            "en": "Is the recipe one of the FSSAI pre-approved Category-A recipes, or a non-standardised one needing product approval?",
            "hi": "क्या यह विधि FSSAI की पूर्व-अनुमोदित श्रेणी-A विधियों में से है, या उत्पाद अनुमोदन चाहने वाली गैर-मानकीकृत विधि है?",
        },
        {
            "id": "sq_aahar_label_claims",
            "en": "What claims appear on the label?",
            "hi": "लेबल पर क्या दावे लिखे हैं?",
        },
    ],
    COSMETIC: [
        {
            "id": "sq_cosmetic_label_claims",
            "en": "What claims appear on the label (cleansing/beautifying versus therapeutic)?",
            "hi": "लेबल पर क्या दावे हैं (सफाई/सौंदर्यवर्धन बनाम चिकित्सकीय)?",
        },
        {
            "id": "sq_cosmetic_markets",
            "en": "In which markets will the product be sold?",
            "hi": "उत्पाद किन बाज़ारों में बेचा जाएगा?",
        },
    ],
    UNCERTAIN: [],
}
