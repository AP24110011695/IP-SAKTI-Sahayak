"""Member 4 Phase 2 — practical Hindi support for the ABS/TK workstream.

Approach (MVP-simple, deterministic, no invented legal terminology):
- `detect_language` classifies a query as Hindi when it contains Devanagari.
- `shadow_query` maps common Hindi ABS/TK phrases onto their standard English
  equivalents, so Hindi and English queries flow through the *same*
  deterministic classification and retrieval path and land on the same
  evidence. Only widely used renderings are mapped (e.g. जैव संसाधन ->
  biological resource, राष्ट्रीय जैव विविधता प्राधिकरण -> National
  Biodiversity Authority, पारंपरिक ज्ञान -> traditional knowledge); statutory
  names are additionally kept in English in the response text so nothing is
  mistranslated into an invented Hindi legal term.
- User-facing Hindi strings (disclaimer, abstention, TKDL pointer, guidance
  framing) live here so tests can assert them.
"""

import re

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")

# Longer phrases first so the longest match wins during substitution.
_HINDI_MAP = (
    ("राष्ट्रीय जैव विविधता प्राधिकरण", "national biodiversity authority"),
    ("राज्य जैव विविधता बोर्ड", "state biodiversity board"),
    ("जैव विविधता प्राधिकरण", "biodiversity authority"),
    ("जैव विविधता अधिनियम", "biological diversity act"),
    ("जैव विविधता प्रबंधन समिति", "biodiversity management committee"),
    ("पूर्व सूचित सहमति", "prior informed consent"),
    ("परस्पर सहमत शर्तें", "mutually agreed terms"),
    ("जैव विविधता", "biodiversity"),
    ("जैव संसाधन", "biological resource"),
    ("लाभ की साझेदारी", "benefit sharing"),
    ("लाभ साझाकरण", "benefit sharing"),
    ("पारंपरिक ज्ञान", "traditional knowledge"),
    ("पूर्व सूचना", "prior intimation"),
    ("नागोया प्रोटोकॉल", "nagoya protocol"),
    ("व्यावसायिक उपयोग", "commercialise"),
    ("व्यावसायीकरण", "commercialise"),
    ("व्यावसायिक", "commercial"),
    ("अनुमोदन", "approvals"),
    ("मंजूरी", "approvals"),
    ("स्वीकृति", "approvals"),
    ("पौधों", "plant"),
    ("पौधे", "plant"),
    ("पौधा", "plant"),
    ("वनस्पति", "plant"),
    ("फॉर्मूलेशन", "formulation"),
    ("नुस्खा", "formulation"),
    ("एकत्रित", "collected"),
    ("आयुर्वेदिक", "ayurvedic"),
    ("आयुर्वेद", "ayurveda"),
    ("टीकेडीएल", "tkdl"),
    ("पूर्व तकनीक", "prior art"),
    ("वैद्य", "vaids"),
    ("हकीम", "hakims"),
    ("जड़ी-बूटी", "herbal"),
    ("जड़ी बूटी", "herbal"),
    ("ट्रेडमार्क", "trademark"),
    ("कॉपीराइट", "copyright"),
    ("पेटेंट", "patent"),
    ("फीस", "fee"),
    ("फॉर्म", "form"),
    ("नियम", "rule"),
    ("धारा", "section"),
    ("किसान", "farmer"),
    ("उगाई", "cultivated"),
    ("खेती", "cultivation"),
    ("निर्यात", "export"),
    ("संरक्षण", "conservation"),
    ("प्राधिकरण", "authority"),
    ("बोर्ड", "board"),
    ("भारत", "india"),
    ("यूरोप", "europe"),
    ("जैव", "biological"),
    ("पारंपरिक", "traditional"),
    ("ज्ञान", "knowledge"),
)


def detect_language(query):
    """Return 'hi' for Devanagari queries, 'en' otherwise."""
    return "hi" if _DEVANAGARI.search(query or "") else "en"


def shadow_query(query):
    """Map known Hindi ABS/TK phrases to their standard English equivalents.

    Non-Hindi text passes through unchanged, so the same downstream pipeline
    (classification + retrieval) serves both languages deterministically.
    """
    text = query or ""
    if not _DEVANAGARI.search(text):
        return text
    for hindi_phrase, english in _HINDI_MAP:
        text = text.replace(hindi_phrase, " " + english + " ")
    return text


# ---------------------------------------------------------------- user-facing strings

DISCLAIMER_EN = (
    "This is general information, not legal advice. Verify current "
    "requirements with the National Biodiversity Authority or a qualified "
    "professional before acting."
)
DISCLAIMER_HI = (
    "यह सामान्य जानकारी है, कानूनी सलाह नहीं। कार्रवाई से पहले राष्ट्रीय जैव "
    "विविधता प्राधिकरण (NBA) या योग्य पेशेवर से वर्तमान आवश्यकताओं की पुष्टि करें।"
)

ABSTAIN_UNRELATED_EN = (
    "This question does not appear to require Access-and-Benefit-Sharing or "
    "Traditional-Knowledge guidance, so it is outside this workstream. "
    "Member 4 covers ABS, the Biological Diversity Act framework, the Nagoya "
    "Protocol, traditional knowledge and TKDL pointers - not patents, "
    "trademarks, GI, copyright or designs. " + DISCLAIMER_EN
)
ABSTAIN_UNRELATED_HI = (
    "यह प्रश्न एक्सेस-एंड-बेनिफिट-शेयरिंग (ABS) या पारंपरिक ज्ञान (Traditional "
    "Knowledge) मार्गदर्शन से संबंधित प्रतीत नहीं होता, इसलिए यह इस "
    "वर्कस्ट्रीम के दायरे में नहीं आता। " + DISCLAIMER_HI
)
ABSTAIN_UNCLEAR_EN = (
    "This question was not recognized as an ABS/Traditional-Knowledge "
    "question, so no guidance is provided. Please rephrase it around the "
    "biological resource, its access/commercialisation, benefit sharing, the "
    "Nagoya Protocol or traditional knowledge. " + DISCLAIMER_EN
)
ABSTAIN_UNCLEAR_HI = (
    "यह प्रश्न ABS/पारंपरिक ज्ञान प्रश्न के रूप में पहचाना नहीं जा सका, "
    "इसलिए कोई मार्गदर्शन नहीं दिया जा रहा। " + DISCLAIMER_HI
)
ABSTAIN_NO_EVIDENCE_EN = (
    "The curated ABS/TK evidence base does not contain sufficient verified "
    "material to answer this question, so it is being declined rather than "
    "answered from general knowledge. Please consult the National "
    "Biodiversity Authority or a qualified ABS professional. " + DISCLAIMER_EN
)
ABSTAIN_NO_EVIDENCE_HI = (
    "इस प्रश्न के लिए हमारे सत्यापित ABS/पारंपरिक-ज्ञान स्रोतों में पर्याप्त "
    "प्रमाण नहीं है, इसलिए सामान्य ज्ञान से उत्तर देने के बजाय इसे लटकाया जा "
    "रहा है। कृपया राष्ट्रीय जैव विविधता प्राधिकरण या योग्य ABS विशेषज्ञ से "
    "परामर्श करें। " + DISCLAIMER_HI
)
ABSTAIN_VALIDATION_EN = (
    "The generated draft failed the safety validation (unsupported or "
    "unverifiable content), so no answer is provided. " + DISCLAIMER_EN
)
ABSTAIN_VALIDATION_HI = (
    "जेनरेट किया गया मसौदा सुरक्षा सत्यापन में विफल रहा (असमर्थित सामग्री), "
    "इसलिए कोई उत्तर नहीं दिया जा रहा। " + DISCLAIMER_HI
)
TKDL_POINTER_EN = (
    "Your question may involve traditional knowledge. This may be knowledge "
    "that the Traditional Knowledge Digital Library (TKDL) covers. TKDL "
    "(https://tkdl.res.in) is an initiative of CSIR and the Ministry of Ayush "
    "maintaining a representative database of Ayurvedic, Unani, Siddha and "
    "Sowarigpa formulations; access to the full database is available to "
    "patent offices only under the TKDL Access Agreement. To assess "
    "prior-art implications, consult TKDL via the relevant patent examiner or "
    "a qualified patent professional. This assistant points to TKDL and never "
    "reproduces its database content."
)
TKDL_POINTER_HI = (
    "आपका प्रश्न पारंपरिक ज्ञान (Traditional Knowledge) से जुड़ा हो सकता है। "
    "यह ज्ञान TKDL (Traditional Knowledge Digital Library) में शामिल हो "
    "सकता है। TKDL (https://tkdl.res.in) CSIR और आयुष मंत्रालय की पहल है, "
    "जिसमें आयुर्वेद, यूनानी, सिद्ध और सोवा-रिग्पा फॉर्मूलेशन का "
    "प्रतिनिधि डेटाबेस है; पूरे डेटाबेस तक पहुँच केवल TKDL Access Agreement "
    "के अंतर्गत पेटेंट कार्यालयों को प्राप्त है। पूर्व-तकनीक (prior art) की "
    "जाँच हेतु TKDL / संबंधित पेटेंट परीक्षक या योग्य पेटेंट विशेषज्ञ से "
    "परामर्श करें। यह सहायक TKDL की ओर संकेत करता है, उसकी डेटाबेस सामग्री "
    "कभी पुनः प्रस्तुत नहीं करता।"
)


def disclaimer(lang):
    return DISCLAIMER_HI if lang == "hi" else DISCLAIMER_EN


def abstain_text(reason_key, lang):
    table = {
        "unrelated": (ABSTAIN_UNRELATED_EN, ABSTAIN_UNRELATED_HI),
        "unclear": (ABSTAIN_UNCLEAR_EN, ABSTAIN_UNCLEAR_HI),
        "no_evidence": (ABSTAIN_NO_EVIDENCE_EN, ABSTAIN_NO_EVIDENCE_HI),
        "validation": (ABSTAIN_VALIDATION_EN, ABSTAIN_VALIDATION_HI),
    }
    en, hi = table[reason_key]
    return hi if lang == "hi" else en


def tkdl_pointer(lang):
    return TKDL_POINTER_HI if lang == "hi" else TKDL_POINTER_EN
