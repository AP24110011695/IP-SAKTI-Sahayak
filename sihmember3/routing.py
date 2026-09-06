"""Member 3 Phase 2 — India query routing.

Deterministic, explainable routing of a free-text question to the relevant
Member 3 corpus slice. This is M3's OWN routing (the slice-of-corpus router
described in MEMBER_3.md Phase 2); it is not M1's cross-domain assistant
router and does not import M1/M2/M4/M5 code.

Routes:
    india_ip            → an India IP/regulatory question; scope_area is the
                          relevant member of sources.SCOPE_AREAS.
    international_only  → clearly international-only (PCT/Madrid/Hague/TRIPS/
                          export/FDA/EU ...). Member 5's domain — never
                          answered as India guidance.
    abs_tk_specialist   → ABS/Nagoya/access-approvals/TKDL-access mechanics.
                          Member 4's domain — M3 only keeps the India-IP
                          intersection (e.g. "does the BD Act affect my patent
                          application?"), which routes to india_ip.
    out_of_scope        → neither an India IP/regulatory question nor another
                          specialist's clear domain.

Hindi handling: Devanagari queries are detected as language "hi" and common
Hindi regulatory vocabulary is mapped to English concept terms BEFORE
matching, so routing and retrieval behave identically for Hindi and English
questions. The map is retrieval infrastructure only — it is not user-facing
and no Hindi legal terminology is invented anywhere.

Everything here is deterministic: pure functions, no randomness, no LLM.
"""

import re

from .sources import SCOPE_AREAS

ROUTES = (
    "india_ip",
    "international_only",
    "abs_tk_specialist",
    "out_of_scope",
)

# ---------------------------------------------------------------------------
# Hindi → English concept mapping (retrieval infrastructure, NOT user-facing
# terminology; statute names stay in their official English form everywhere).
# ---------------------------------------------------------------------------

# Multi-word phrases are rewritten in the raw query before tokenising.
# Values emit the same English keywords the equivalent English question would
# produce, so Hindi and English questions score identically.
_HINDI_PHRASES = (
    ("भौगोलिक संकेत", " geographical indication "),
    ("पारंपरिक ज्ञान", " traditional knowledge "),
    ("जैव विविधता अधिनियम", " biodiversity act "),
    ("जैव विविधता", " biodiversity "),
    ("जैविक संसाधन", " biological resource "),
    ("किसान अधिकार", " farmers rights "),
    ("पौधे की किस्म", " plant variety "),
    ("पौध किस्म", " plant variety "),
    ("व्यापार चिह्न", " trademark "),
    ("पेटेंट अधिनियम", " patent "),
    ("कॉपीराइट अधिनियम", " copyright "),
    ("खाद्य सुरक्षा", " fssai "),
    ("आयुर्वेद आहार", " ayurveda aahara "),
    ("उत्पाद डिज़ाइन", " design "),
)

# Single-token Hindi vocabulary -> the equivalent English keyword.
_HINDI_TOKENS = {
    "पेटेंट": "patent",
    "पेटेन्ट": "patent",
    "पेटेंटयोग्य": "patentable",
    "आविष्कार": "invention",
    "जीआई": "gi",
    "टैग": "tag",
    "ट्रेडमार्क": "trademark",
    "ब्रांड": "brand",
    "लोगो": "logo",
    "कॉपीराइट": "copyright",
    "डिज़ाइन": "design",
    "डिजाइन": "design",
    "पैकेजिंग": "packaging",
    "आयुर्वेदिक": "ayurveda",
    "आयुर्वेद": "ayurveda",
    "शास्त्रीय": "classical",
    "क्लासिकल": "classical",
    "फॉर्मूलेशन": "formulation",
    "फ़ॉर्मूलेशन": "formulation",
    "औषधि": "drug",
    "दवा": "drug",
    "कॉस्मेटिक": "cosmetic",
    "खाद्य": "food",
    "भोजन": "food",
    "पोषण": "nutraceutical",
    "विज्ञापन": "advertisement",
    "विज्ञापनों": "advertisement",
    "पंजीकरण": "registration",
    "रजिस्टर": "register",
    "रजिस्ट्रेशन": "registration",
    "पंजीकृत": "registered",
    "लाइसेंस": "licence",
    "लाइसेंसिंग": "licensing",
    "अनुमति": "approval",
    "स्वीकृति": "approval",
    "पौधे": "plant",
    "पौधा": "plant",
    "किस्म": "variety",
    "बीज": "seed",
    "किसान": "farmer",
    "किसानों": "farmer",
    "कृषि": "farmer",
    "पारंपरिक": "traditional",
    "प्रामाणिक": "authoritative",
    "ग्रंथ": "books",
    "किताब": "books",
    "नियम": "rule",
    "कानून": "law",
    "अधिनियम": "statute",
    "धारा": "section",
    "क्लेम": "claim",
    "दावा": "claim",
    "दावों": "claim",
    "फीस": "fees",
    "शुल्क": "fees",
    "प्रक्रिया": "procedure",
    "जमा": "deposit",
    "जैव": "biological",
    "संसाधन": "resource",
    "एनबीए": "nba",
    "एफएसएसएआई": "fssai",
    "फोस्कोस": "foscos",
    "टीकेडीएल": "tkdl",
    "निर्यात": "export",
    "आयात": "import",
    "विदेश": "foreign",
    "विदेशी": "foreign",
    "क्षेत्र": "region",
    "भारत": "india",
    "भारतीय": "indian",
}


# ---------------------------------------------------------------------------
# Curated route/scope keyword tables (English; Hindi input is normalised to
# these same terms first, so one table serves both languages).
# ---------------------------------------------------------------------------

# Questions about these are Member 5's (international) — never answer as India.
_INTERNATIONAL_STRONG = (
    "pct", "madrid", "hague", "trips", "wipo", "epo", "uspto",
    "national phase", "international application", "international patent",
    "international trademark", "international design", "wire mark", "dm1", "dm/1",
    "outside india", "abroad", "foreign country", "foreign countries",
    "export", "exporting", "dshea", "fda", "european union", "eu market",
    "usa market", "us market", "novel food", "gratk",
)

# Questions about these mechanics are Member 4's (ABS/TK specialist). Bare
# "tkdl" or "biodiversity act" is NOT here: an India-patent question may
# legitimately need the TKDL pointer or the BD Act Section 6 intersection.
_ABS_TK_STRONG = (
    "nagoya", "prior informed consent", "mutually agreed terms",
    "benefit sharing", "benefit-sharing", "abs compliance", "abs filing",
    "biopiracy", "biological resource access", "access to biological",
    "resource access approval", "nba approval", "nba permission",
    "state biodiversity board", "biodiversity board", "community consent",
    "tkdl access", "tkdl subscription", "tkdl nda",
)

# India-IP scope terms. Keys are scope areas; matching is substring against
# the normalised query text. Order matters for tie-breaking (earlier wins),
# with the notable deliberate exception that the BD-Act intersection with a
# patent question should land on patents — handled by an explicit rule below.
_SCOPE_TERMS = {
    "patents": (
        "patent", "patentable", "patentability", "3(p)", "3p",
        "inventive step", "invention", "inventions",
    ),
    "geographical_indications": (
        "gi tag", "gi registry", "geographical indication", "geographical indications",
        "gi registration", "gi status", "darjeeling", "regional product",
    ),
    "trademarks": (
        "trademark", "trademarks", "trade mark", "trade marks", "brand name",
        "brand", "logo", "certification mark", "tm-a", "service mark",
    ),
    "copyright": (
        "copyright", "copyrights", "public domain", "translation rights",
        "literary work",
    ),
    "designs": (
        "design", "designs", "packaging", "bottle shape", "label design",
        "ornamental", "product appearance",
    ),
    "ppv_fr": (
        "plant variety", "plant varieties", "farmers rights", "farmer's rights",
        "farmers' rights", "ppv", "seed variety", "breeder", "essentially derived",
    ),
    "drugs_cosmetics": (
        "ayurvedic drug", "ayurvedic medicine", "medicine", "medicines",
        "manufacturing licence", "manufacturing license", "drug licence",
        "drug license", "state licensing authority", "cosmetic", "cosmetics",
        "schedule t", "gmp", "cdsco", "dcgi", "new drug", "phytopharmaceutical",
        "clinical trial", "drug", "drugs",
    ),
    "drugs_magic_remedies": (
        "advertisement", "advertisements", "advertising", "advertise",
        "magic remedies", "magic remedy", "objectionable", "cure claim",
        "cure claims", "misleading claim", "misleading advertisement",
        "misleading claims", "false claim", "false claims",
        "cure", "cures", "curing",
    ),
    "fssai_ayurveda_aahara": (
        "fssai", "ayurveda aahar", "ayurveda aahara", "aahara", "aahar",
        "nutraceutical", "nutraceuticals", "foscos", "health supplement",
        "health supplements", "food licence", "food license", "food business",
        "food product", "herbal food", "food", "foods",
    ),
    "biological_diversity": (
        "biodiversity act", "biological diversity act", "biodiversity",
        "biological resource", "biological resources", "nba", "bda",
    ),
}

# Scope areas checked first when counts tie. Patents before
# biological_diversity so that "does the BD Act affect my patent?" lands on
# the India-IP intersection rather than looking like an ABS question.
_SCOPE_PRIORITY = (
    "patents",
    "geographical_indications",
    "fssai_ayurveda_aahara",
    "drugs_magic_remedies",
    "drugs_cosmetics",
    "biological_diversity",
    "ppv_fr",
    "trademarks",
    "copyright",
    "designs",
)

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_TOKEN_RE = re.compile(r"[a-z0-9()\u0900-\u097F]+")


def detect_language(query):
    """Return "hi" if the query contains Devanagari script, else "en"."""
    return "hi" if _DEVANAGARI.search(query or "") else "en"


def normalize_query(query):
    """Normalise a query for matching: lowercase, rewrite Hindi phrases and
    tokens to their English concept terms, collapse whitespace (Hindi token
    substitution inserts padding spaces, and multi-word route terms such as
    "gi tag" need single-space adjacency). Deterministic."""
    text = (query or "").lower()
    if _DEVANAGARI.search(text):
        for phrase, replacement in _HINDI_PHRASES:
            text = text.replace(phrase, replacement)
        def _sub_token(match):
            word = match.group(0)
            if word in _HINDI_TOKENS:
                return " " + _HINDI_TOKENS[word] + " "
            return word
        text = _TOKEN_RE.sub(_sub_token, text)
    return re.sub(r"\s+", " ", text).strip()


def _count_terms(normalised, terms):
    """Return the sorted list of curated terms present in the text.
    Longest-first so multi-word terms are reported (and counted once)."""
    matched = [t for t in sorted(terms, key=len, reverse=True) if t in normalised]
    return matched


def route_query(query, language=None, jurisdiction=None):
    """Route a free-text question. Returns a dict:

        route          one of ROUTES
        scope_area     primary member of SCOPE_AREAS for india_ip, else None
        matched_areas  ALL scope areas with term matches, best-first (India
                       questions that implicate several regimes at once —
                       e.g. a product that is both a GI candidate and a
                       classical-medicine patent question — list every
                       matched area here); single item for simple questions
        scope_scores   {area: matched-term count} for the matched areas
        language       "en" | "hi" (explicit parameter overrides detection)
        matched_terms  {group: [terms]} — the explainable matching evidence
        reason         short human-readable explanation of the decision

    Deterministic: identical input always yields an identical decision.
    """
    normalised = normalize_query(query)
    lang = language if language in ("en", "hi") else detect_language(query)

    matched_terms = {}
    international = _count_terms(normalised, _INTERNATIONAL_STRONG)
    abs_tk = _count_terms(normalised, _ABS_TK_STRONG)

    if jurisdiction is not None and jurisdiction != "India":
        return {
            "route": "out_of_scope",
            "scope_area": None,
            "matched_areas": [],
            "scope_scores": {},
            "language": lang,
            "matched_terms": {},
            "reason": (
                "explicit jurisdiction %r requested; Member 3 only answers "
                "India questions" % (jurisdiction,)
            ),
        }

    if international:
        matched_terms["international_only"] = international
        return {
            "route": "international_only",
            "scope_area": None,
            "matched_areas": [],
            "scope_scores": {},
            "language": lang,
            "matched_terms": matched_terms,
            "reason": (
                "question matches international-only terms %s; international "
                "IP/export is not Member 3's domain" % international
            ),
        }

    if abs_tk:
        matched_terms["abs_tk_specialist"] = abs_tk
        return {
            "route": "abs_tk_specialist",
            "scope_area": None,
            "matched_areas": [],
            "scope_scores": {},
            "language": lang,
            "matched_terms": matched_terms,
            "reason": (
                "question matches ABS/TK-specialist terms %s; deep "
                "ABS/Nagoya/TKDL-access belongs to Member 4" % abs_tk
            ),
        }

    # India-IP scope scoring: count matched curated terms per scope area.
    scores = {}
    per_area_terms = {}
    for area, terms in _SCOPE_TERMS.items():
        matched = _count_terms(normalised, terms)
        if matched:
            scores[area] = len(matched)
            per_area_terms[area] = matched

    if not scores:
        return {
            "route": "out_of_scope",
            "scope_area": None,
            "matched_areas": [],
            "scope_scores": {},
            "language": lang,
            "matched_terms": {},
            "reason": (
                "no India IP/regulatory scope terms matched the curated "
                "Member 3 corpus areas"
            ),
        }

    # Deterministic ordering: highest count first, then _SCOPE_PRIORITY order.
    def _sort_key(area):
        priority = _SCOPE_PRIORITY.index(area) if area in _SCOPE_PRIORITY else 99
        return (-scores[area], priority, area)

    ranked_areas = sorted(scores, key=_sort_key)
    best_area = ranked_areas[0]
    matched_terms["scope"] = sorted(
        per_area_terms[best_area], key=len, reverse=True
    )
    return {
        "route": "india_ip",
        "scope_area": best_area,
        "matched_areas": ranked_areas,
        "scope_scores": {area: scores[area] for area in ranked_areas},
        "language": lang,
        "matched_terms": matched_terms,
        "reason": (
            "India IP/regulatory question; strongest scope match %r "
            "(%d term(s) matched)%s"
            % (
                best_area,
                scores[best_area],
                "; also implicates %s" % ranked_areas[1:]
                if len(ranked_areas) > 1 else "",
            )
        ),
    }
