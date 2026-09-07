"""Local deterministic conversational-response layer (M6 Phase 4).

Intercepts ONLY clearly general small talk — greetings, thanks, goodbye,
help/capability questions, simple acknowledgements — and answers it from a
fixed response table BEFORE legal routing. Not an LLM feature: no API key,
no network, no new dependency, no ML — pure standard-library pattern logic,
deterministic for a given message + language.

Boundary rule (the critical one): a message is intercepted only when EVERY
token, after normalisation, belongs to this module's closed conversational
vocabulary, and at least one token names one of the five supported intents.
The vocabulary deliberately contains NO IP / legal / regulatory terms, so a
message carrying any genuine legal request necessarily contains a token
outside the vocabulary and falls through to the existing M1 routing pipeline
unchanged:

    "Hi, can I patent a classical Ayurvedic formulation?"   → patent …   → M1
    "Thanks, but can you explain PCT?"                      → pct …      → M1
    "Okay, what is the Madrid System?"                      → madrid …   → M1
    "What about trademarks?"  (follow-up)                   → trademarks → M1

Ambiguous filler-only messages with no intent token ("what about that?",
"good", "it") are also left to the existing pipeline — only clearly
standalone conversational messages are intercepted. Follow-up behaviour is
untouched: the layer runs before follow-up resolution and routing, so a
short "Thanks" after a legal answer gets the local thanks response while
every substantive follow-up keeps the full context-carrying flow.

Responses respect the request's language setting (en/hi), carry no citations,
claim no legal authority, and include the standing disclaimer required by
m1.safety.assert_response_safe. Response text is a plain fixed string — never
generated.
"""
from __future__ import annotations

import re
from typing import Dict, FrozenSet, Optional

from .config import DISCLAIMER_EN, DISCLAIMER_HI
from .models import QueryRequest, QueryResponse
from .safety import assert_response_safe

# Supported local intents (small, explicit, closed set).
GREETING = "greeting"
THANKS = "thanks"
GOODBYE = "goodbye"
HELP = "help"
ACKNOWLEDGEMENT = "acknowledgement"

# Tokens are matched on a lowercased, punctuation-stripped form; Devanagari
# (\u0900-\u097F) is kept so Hindi-script messages work the same way.
_TOKEN_RE = re.compile(r"[a-z0-9\u0900-\u097f]+")

# A longer message cannot be clearly standalone small talk — defence in depth
# so a sentence that happens to be built from filler words is never hijacked.
MAX_CONVERSATIONAL_TOKENS = 12

# Intent trigger tokens. Membership in the vocabulary alone is not enough — a
# token from one of these sets must be present for an intent to fire.
_GREETING_TOKENS: FrozenSet[str] = frozenset({
    "hi", "hii", "hiii", "hiya", "hello", "helo", "hey", "heyy",
    "greetings", "morning", "afternoon", "evening", "day", "night",
    "namaste", "namaskar", "namaskaram", "suprabhat", "prabhat", "shubh",
    "नमस्ते", "नमस्कार", "सुप्रभात",
})
_THANKS_TOKENS: FrozenSet[str] = frozenset({
    "thanks", "thank", "thankyou", "thnx", "thx", "ty",
    "dhanyavad", "dhanyavaad", "dhanyawad", "shukriya", "aabhari",
    "धन्यवाद", "शुक्रिया", "आभार",
})
_GOODBYE_TOKENS: FrozenSet[str] = frozenset({
    "bye", "byebye", "goodbye", "goodnight", "see", "later", "farewell",
    "cya", "tata", "alvida", "phir", "milenge",
    "अलविदा", "फिर", "मिलेंगे",
})
_HELP_TOKENS: FrozenSet[str] = frozenset({
    "help", "what", "who", "how", "capabilities", "capability", "features",
    "ip", "ipsakti", "sakti", "sahayak", "madad", "kya",
    "मदद", "क्या",
})
_ACKNOWLEDGEMENT_TOKENS: FrozenSet[str] = frozenset({
    "ok", "okay", "okok", "kk", "k", "okie", "got", "alright", "right",
    "fine", "sure", "ya", "yeah", "yep", "yup",
    "thik", "theek", "achha", "accha",
    "ठीक", "अच्छा",
})

# Filler tokens that may accompany an intent token but never trigger one
# themselves. Deliberately excludes vague references ("that", "this",
# "about", "there" …) so context-dependent follow-ups like "What about
# trademarks?"-style short queries keep their existing pipeline behaviour,
# and excludes every domain word by construction.
_FILLER_TOKENS: FrozenSet[str] = frozenset({
    # English politeness / pronouns / auxiliaries / prepositions
    "you", "u", "ur", "your", "yours", "yourself",
    "so", "much", "very", "lot", "lots", "good",
    "a", "an", "the", "to", "for", "of", "in", "on", "at", "by", "with",
    "from", "as", "and", "or", "but", "if", "then",
    "my", "me", "i", "im", "am", "is", "are", "was", "were", "be", "been",
    "being", "do", "does", "did", "doing",
    "can", "could", "would", "will", "shall", "should", "may", "might",
    "must", "please", "pls", "plz", "kindly",
    "sir", "madam", "mam", "maam", "it", "its", "s", "up", "talk",
    # Romanised Hindi filler
    "hai", "hain", "ho", "hun", "hoon", "aap", "tum", "kar", "karo",
    "karein", "kariye", "sakte", "sakta", "saktee",
    "ke", "ka", "ki", "ko", "se", "mein", "meri", "mera",
    "bhai", "ji", "ab", "yeh", "ye", "woh", "wo",
})

_VOCABULARY: FrozenSet[str] = (
    _GREETING_TOKENS | _THANKS_TOKENS | _GOODBYE_TOKENS | _HELP_TOKENS
    | _ACKNOWLEDGEMENT_TOKENS | _FILLER_TOKENS
)

# Intent precedence when several trigger tokens appear ("bye, thanks!"):
# farewell wins over thanks, thanks over greeting, a help/capability question
# over a bare acknowledgement.
_INTENT_PRECEDENCE = (
    (GOODBYE, _GOODBYE_TOKENS),
    (THANKS, _THANKS_TOKENS),
    (GREETING, _GREETING_TOKENS),
    (HELP, _HELP_TOKENS),
    (ACKNOWLEDGEMENT, _ACKNOWLEDGEMENT_TOKENS),
)

# Fixed response table (en / hi). Nothing here is generated; nothing claims
# legal authority; capabilities listed match what the integrated pipeline
# actually implements (M2 guided classification, M3 India corpus, M4 ABS/TK,
# M5 PCT/Madrid/Hague, citations/confidence/abstention).
_RESPONSES: Dict[str, Dict[str, str]] = {
    GREETING: {
        "en": (
            "Hello! I'm IP-SAKTI Sahayak. I can help with Ayurvedic "
            "intellectual property, formulation classification, "
            "biodiversity/ABS, traditional knowledge, and international IP "
            "guidance."
        ),
        "hi": (
            "नमस्ते! मैं IP-SAKTI Sahayak हूँ। मैं आयुर्वेदिक बौद्धिक संपदा, "
            "फॉर्मूलेशन वर्गीकरण, जैव विविधता/ABS और अंतरराष्ट्रीय IP "
            "मार्गदर्शन में मदद कर सकता हूँ।"
        ),
    },
    THANKS: {
        "en": (
            "You're welcome. Ask me an Ayurvedic IP or regulatory question "
            "whenever you're ready."
        ),
        "hi": (
            "स्वागत है। जब भी आप तैयार हों, कोई आयुर्वेदिक IP या नियामक प्रश्न "
            "पूछें।"
        ),
    },
    GOODBYE: {
        "en": (
            "Goodbye. You can return anytime with an Ayurvedic IP or "
            "regulatory question."
        ),
        "hi": (
            "अलविदा। आप कभी भी आयुर्वेदिक IP या नियामक प्रश्न लेकर वापस आ "
            "सकते हैं।"
        ),
    },
    ACKNOWLEDGEMENT: {
        "en": (
            "Got it. Ask me an Ayurvedic IP or regulatory question whenever "
            "you're ready."
        ),
        "hi": (
            "ठीक है। जब भी आप तैयार हों, कोई आयुर्वेदिक IP या नियामक प्रश्न "
            "पूछें।"
        ),
    },
    HELP: {
        "en": (
            "I'm IP-SAKTI Sahayak — an assistant for Ayurvedic intellectual "
            "property and regulatory questions. Here is what I can do:\n\n"
            "- Classify an Ayurvedic formulation (Classical, Proprietary, "
            "Phytopharmaceutical, Ayurveda-Aahar, Cosmetic, New Drug) "
            "through the guided classification flow (the Classify tab).\n"
            "- Answer India IP & regulatory questions from a curated corpus "
            "with verifiable citations — the Patents Act (including Section "
            "3(p) on traditional knowledge), Trade Marks, Geographical "
            "Indications, Designs, Copyright, Drugs & Cosmetics, FSSAI "
            "Ayurveda Aahara and related rules.\n"
            "- Guide on biodiversity / access and benefit-sharing and "
            "traditional-knowledge compliance (Biological Diversity Act, "
            "NBA, TKDL pointers).\n"
            "- Explain international IP filing routes (PCT for patents, "
            "Madrid for trademarks, Hague for designs).\n\n"
            "Every legal answer carries citations and a confidence score, "
            "and I abstain instead of guessing when corpus evidence is "
            "insufficient. Ask a question in English or Hindi, and use the "
            "India/International toggle to match your filing route."
        ),
        "hi": (
            "मैं IP-SAKTI Sahayak हूँ — आयुर्वेदिक बौद्धिक संपदा और नियामक "
            "प्रश्नों के लिए सहायक। मैं यह कर सकता हूँ:\n\n"
            "- निर्देशित वर्गीकरण प्रवाह (Classify टैब) से आयुर्वेदिक "
            "फॉर्मूलेशन का वर्गीकरण (Classical, Proprietary, "
            "Phytopharmaceutical, Ayurveda-Aahar, Cosmetic, New Drug)।\n"
            "- सत्यापन योग्य संदर्भों के साथ भारतीय IP और नियामक प्रश्नों के "
            "उत्तर — पेटेंट अधिनियम (पारंपरिक ज्ञान संबंधी धारा 3(प) सहित), "
            "ट्रेड मार्क, भौगोलिक संकेतक, डिज़ाइन, कॉपीराइट, ड्रग्स एंड "
            "कॉस्मेटिक्स, FSSAI आयुर्वेद आहार और संबंधित नियम।\n"
            "- जैव विविधता / लाभ-साझेदारी और पारंपरिक ज्ञान अनुपालन में "
            "मार्गदर्शन (जैव विविधता अधिनियम, NBA, TKDL संकेत)।\n"
            "- अंतरराष्ट्रीय IP फाइलिंग मार्ग (पेटेंट हेतु PCT, ट्रेड मार्क "
            "हेतु मैड्रिड, डिज़ाइन हेतु हेग)।\n\n"
            "हर कानूनी उत्तर के साथ संदर्भ और विश्वास स्कोर होता है, और जब "
            "स्रोत-साक्ष्य पर्याप्त नहीं होता तो मैं अनुमान लगाने के बजाय "
            "उत्तर देने से इनकार कर देता हूँ। प्रश्न हिंदी या अंग्रेज़ी में "
            "पूछें, और भारत/अंतरराष्ट्रीय टॉगल अपने फाइलिंग मार्ग के अनुसार "
            "सेट करें।"
        ),
    },
}


def detect_intent(message: str) -> Optional[str]:
    """Return one of the five supported intents, or None.

    None means "not CLEARLY general conversation" — the caller must send the
    message through the existing legal pipeline. Deterministic and
    side-effect free.
    """
    tokens = set(_TOKEN_RE.findall(message.lower()))
    if not tokens or len(tokens) > MAX_CONVERSATIONAL_TOKENS:
        return None
    if not tokens <= _VOCABULARY:
        return None  # some token is outside the conversational vocabulary
    for intent, trigger_tokens in _INTENT_PRECEDENCE:
        if tokens & trigger_tokens:
            return intent
    return None  # filler-only message with no intent ("it", "good") → pipeline


def local_response(request: QueryRequest) -> Optional[QueryResponse]:
    """A contract-valid QueryResponse for a clearly conversational message,
    or None when the message must continue through the legal pipeline."""
    intent = detect_intent(request.query)
    if intent is None:
        return None
    language = "hi" if request.language == "hi" else "en"
    response = QueryResponse(
        id=request.id,
        answer=_RESPONSES[intent][language],
        citations=[],
        confidence="HIGH",
        confidence_score=1.0,
        abstention=False,
        abstention_reason=None,
        escalation_available=False,
        disclaimer=DISCLAIMER_HI if language == "hi" else DISCLAIMER_EN,
    )
    assert_response_safe(response)
    return response
