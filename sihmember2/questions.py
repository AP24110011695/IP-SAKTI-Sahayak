"""Guided questions for the IP-SAKTI Sahayak formulation classifier (Member 2).

The question set is the minimum needed to discriminate the six formulation
categories defined in PS.md / Research.md:

    Classical | Proprietary | Phytopharmaceutical | Ayurveda-Aahar | Cosmetic | New Drug

Every question has a stable id and a fixed set of allowed values. The
classification decision itself is made ONLY from these answers by the
deterministic rules in ``classifier.py`` -- no LLM, statistical model or
network call takes part in the decision.

Bilingual (English/Hindi): each question carries ``text`` (English) and
``text_hi`` (Hindi), and each option id has an English label in ``options``
and a Hindi label in ``options_hi``. Option ids and answer values are
identical across languages -- multilingual text never changes classification
behaviour.

Answer values are case-insensitive. A missing key, ``None`` or an empty
string means "question not answered"; the literal value ``"unsure"`` means
the user was asked but does not know. Both are safe inputs: they can never
produce a guessed category, only ``Uncertain`` with a clarification prompt.
"""

import copy

UNSURE = "unsure"

# Stable question ids (contract for M1/M6 rendering and answer submission).
Q_PRIMARY_PURPOSE = "primary_purpose"
Q_FOOD_EXCLUSION = "food_exclusion"
Q_TEXT_SOURCE = "text_source"
Q_STANDARDISED_FRACTION = "standardised_fraction"
Q_INGREDIENTS_KNOWN = "ingredients_known"
Q_NEW_INDICATION = "new_indication"

QUESTIONS = [
    {
        "id": Q_PRIMARY_PURPOSE,
        "text": "As presented to the consumer, what is the product's primary intended use?",
        "text_hi": "उपभोक्ता को जैसा प्रस्तुत किया जाता है, उत्पाद का प्राथमिक उपयोग क्या है?",
        "options": {
            "therapeutic": "Taken or used to treat, cure or mitigate a disease or condition (a medicine)",
            "food_wellness": "Consumed as food / nutrition / general wellness, with no treatment claims",
            "external_cosmetic": "Applied externally to cleanse, beautify or alter appearance (cosmetic use)",
            "other": "Something else, or unclear",
        },
        "options_hi": {
            "therapeutic": "किसी रोग या स्थिति के उपचार, निवारण या शमन हेतु लिया या प्रयुक्त होने वाला (औषधि)",
            "food_wellness": "भोजन / पोषण / सामान्य स्वास्थ्य के रूप में सेवन, बिना किसी उपचार दावे के",
            "external_cosmetic": "सफाई, सौंदर्यवर्धन या रूप-रंग बदलने हेतु बाहरी उपयोग (कॉस्मेटिक उपयोग)",
            "other": "अन्य कुछ, या अस्पष्ट",
        },
        "note": "Root discriminator between the drug track, the food (Ayurveda-Aahar) track and the cosmetic track.",
        "asked_when": "always",
    },
    {
        "id": Q_FOOD_EXCLUSION,
        "text": (
            "Does the product contain metal/mineral preparations (bhasma or pishti) or "
            "Schedule E-1 herbs, or does it carry any treatment/cure claim?"
        ),
        "text_hi": (
            "क्या उत्पाद में धातु/खनिज तैयारियाँ (भस्म या पिष्टि) या अनुसूची E-1 की जड़ी-बूटियाँ हैं, "
            "या इसमें कोई उपचार/निवारण दावा है?"
        ),
        "options": {
            "none": "No - none of these",
            "bhasma_or_e1": "Yes - contains bhasma/pishti or Schedule E-1 herbs",
            "cure_claim": "Yes - it carries a treatment/cure claim",
        },
        "options_hi": {
            "none": "नहीं - इनमें से कुछ भी नहीं",
            "bhasma_or_e1": "हाँ - भस्म/पिष्टि या अनुसूची E-1 की जड़ी-बूटियाँ हैं",
            "cure_claim": "हाँ - इसमें उपचार/निवारण का दावा है",
        },
        "note": (
            "Asked when the product is presented as food. The FSSAI Ayurveda-Aahara category "
            "explicitly excludes Ayurvedic drugs, cosmetics, Schedule E-1 herbs and metal-based "
            "products (bhasmas, pishtis); products making treatment/cure claims fall under the "
            "Drugs and Cosmetics Act instead (Research.md B.3.c)."
        ),
        "asked_when": "primary_purpose == food_wellness",
    },
    {
        "id": Q_TEXT_SOURCE,
        "text": (
            "Is the formulation - its ingredients, proportions and preparation method - taken "
            "unchanged from an authoritative Ayurveda text of the First Schedule (e.g. Charaka "
            "Samhita, Sushruta Samhita, Ashtanga Hridaya)?"
        ),
        "text_hi": (
            "क्या यह योग - इसकी सामग्री, अनुपात और निर्माण विधि - प्रथम अनुसूची के प्रामाणिक आयुर्वेद "
            "ग्रंथों (जैसे चरक संहिता, सुश्रुत संहिता, अष्टांग हृदय) से अपरिवर्तित रूप से लिया गया है?"
        ),
        "options": {
            "yes": "Yes - the formulation is reproduced unchanged from an authoritative text",
            "no": "No - it is a modified or new formulation",
        },
        "options_hi": {
            "yes": "हाँ - योग किसी प्रामाणिक ग्रंथ से अपरिवर्तित रूप से लिया गया है",
            "no": "नहीं - यह संशोधित या नया योग है",
        },
        "note": (
            "Asked on the drug track. Separates Classical medicines (formulation and method drawn "
            "from a First-Schedule authoritative text) from every other drug category (PS.md; "
            "Research.md B.3.a)."
        ),
        "asked_when": "drug track",
    },
    {
        "id": Q_STANDARDISED_FRACTION,
        "text": (
            "Is the product a standardised plant fraction or isolated constituent with defined "
            "active markers, rather than a whole preparation as described in the texts?"
        ),
        "text_hi": (
            "क्या उत्पाद, ग्रंथों में वर्णित संपूर्ण तैयारी के बजाय, परिभाषित सक्रिय मार्करों वाला "
            "मानकीकृत पादप अंश या पृथक किया गया घटक है?"
        ),
        "options": {
            "yes": "Yes - it is a standardised fraction/constituent with defined active markers",
            "no": "No - it is a whole preparation, not a standardised fraction",
        },
        "options_hi": {
            "yes": "हाँ - यह परिभाषित सक्रिय मार्करों वाला मानकीकृत अंश/घटक है",
            "no": "नहीं - यह संपूर्ण तैयारी है, मानकीकृत अंश नहीं",
        },
        "note": (
            "Asked on the drug track. Separates phytopharmaceuticals (standardised plant-based "
            "fractions with defined active markers) from the other drug categories (Research.md B.3.a)."
        ),
        "asked_when": "drug track",
    },
    {
        "id": Q_INGREDIENTS_KNOWN,
        "text": "Are all of the ingredients already established and known in Ayurvedic use?",
        "text_hi": "क्या सभी सामग्री आयुर्वेदिक उपयोग में पहले से स्थापित और ज्ञात हैं?",
        "options": {
            "yes": "Yes - all ingredients are already established in Ayurvedic use",
            "no": "No - at least one ingredient is new to Ayurvedic use",
        },
        "options_hi": {
            "yes": "हाँ - सभी सामग्री आयुर्वेदिक उपयोग में पहले से स्थापित हैं",
            "no": "नहीं - कम से कम एक सामग्री आयुर्वेदिक उपयोग के लिए नई है",
        },
        "note": (
            "Asked on the drug track for non-classical, non-standardised products. Separates "
            "proprietary medicines (new formulations of known ingredients) from new drugs "
            "(Research.md B.3.a)."
        ),
        "asked_when": "drug track",
    },
    {
        "id": Q_NEW_INDICATION,
        "text": (
            "Does the product make a treatment/cure claim for an indication that is not already "
            "established for these ingredients (a new therapeutic claim)?"
        ),
        "text_hi": (
            "क्या उत्पाद ऐसे रोग/उपयोग के लिए उपचार/निवारण का दावा करता है जो इन सामग्रियों के "
            "लिए पहले से स्थापित नहीं है (नया चिकित्सकीय दावा)?"
        ),
        "options": {
            "yes": "Yes - it claims a therapeutic use not already established for these ingredients",
            "no": "No - no new therapeutic claim is made",
        },
        "options_hi": {
            "yes": "हाँ - यह इन सामग्रियों के लिए पहले से स्थापित चिकित्सकीय उपयोग के अतिरिक्त नए उपयोग का दावा करता है",
            "no": "नहीं - कोई नया चिकित्सकीय दावा नहीं किया जाता",
        },
        "note": (
            "A new indication means proof of safety and effectiveness is required (new drug). A "
            "definitive 'yes' on a food or cosmetic product also moves it to the drug track, "
            "because products making treatment/cure claims fall under the Drugs and Cosmetics "
            "Act (Research.md B.3.a, B.3.c)."
        ),
        "asked_when": "drug track (also read as a safety cross-check for food/cosmetic answers)",
    },
]


def get_questions():
    """Return a fresh deep copy of all question definitions (for rendering)."""
    return copy.deepcopy(QUESTIONS)


def get_question(question_id):
    """Return a deep copy of one question definition, or None if unknown."""
    for question in QUESTIONS:
        if question["id"] == question_id:
            return copy.deepcopy(question)
    return None
