"""Bilingual (English/Hindi) user-facing strings for the formulation
classifier (Member 2, Phase 2).

All classification logic reads only machine values; these strings are used
purely for rendering results and clarification prompts in the requested
language. Category labels live in ``regimes.CATEGORY_LABELS``.
"""

EN = "en"
HI = "hi"
LANGUAGES = (EN, HI)

# Category descriptions, keyed by formulation_class.
DESCRIPTIONS = {
    "Classical": {
        "en": (
            "Formulation whose ingredients, proportions and preparation method are "
            "drawn unchanged from an authoritative First-Schedule Ayurveda text "
            "(e.g. Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya). Regulated "
            "as an ASU drug under the Drugs and Cosmetics Act through the State "
            "Licensing Authority; exempt from clinical trials. Largely traditional "
            "knowledge: faces the Section 3(p) patent bar and is defended through "
            "the TKDL."
        ),
        "hi": (
            "ऐसा योग जिसकी सामग्री, अनुपात और निर्माण विधि प्रथम अनुसूची के प्रामाणिक "
            "आयुर्वेद ग्रंथों (जैसे चरक संहिता, सुश्रुत संहिता, अष्टांग हृदय) से "
            "अपरिवर्तित रूप से ली गई है। औषधि एवं प्रसाधन अधिनियम, 1940 के अंतर्गत राज्य "
            "लाइसेंसिंग प्राधिकरण द्वारा ASU औषधि के रूप में विनियमित; नैदानिक परीक्षणों "
            "से मुक्त। अधिकांशतः पारंपरिक ज्ञान: पेटेंट अधिनियम की धारा 3(प) के प्रतिबंध "
            "के अधीन और TKDL द्वारा संरक्षित।"
        ),
    },
    "Proprietary": {
        "en": (
            "New (non-classical) formulation made of ingredients that are already "
            "established in Ayurvedic use, not reproduced from an authoritative "
            "text. Regulated as a proprietary ASU medicine under the Drugs and "
            "Cosmetics Act (State Licensing Authority with CDSCO review; safety "
            "studies, not full clinical trials)."
        ),
        "hi": (
            "ज्ञात आयुर्वेदिक सामग्री से बनी नई (गैर-शास्त्रीय) तैयारी, जो किसी "
            "प्रामाणिक ग्रंथ से अपरिवर्तित रूप से नहीं ली गई। औषधि एवं प्रसाधन अधिनियम "
            "के अंतर्गत प्रोप्राइटरी ASU औषधि के रूप में विनियमित (राज्य लाइसेंसिंग "
            "प्राधिकरण + CDSCO समीक्षा; सुरक्षा अध्ययन, पूर्ण नैदानिक परीक्षण नहीं)।"
        ),
    },
    "Phytopharmaceutical": {
        "en": (
            "Standardised plant-based fraction or constituent with defined active "
            "markers. Treated as a new drug under the Drugs and Cosmetics Act with "
            "central CDSCO evaluation and rigorous clinical trials."
        ),
        "hi": (
            "परिभाषित सक्रिय मार्करों वाला मानकीकृत पादप-आधारित अंश या घटक। औषधि एवं "
            "प्रसाधन अधिनियम के अंतर्गत नई औषधि माना जाता है, जिसमें CDSCO केंद्रीय "
            "मूल्यांकन और कठोर नैदानिक परीक्षण आवश्यक हैं।"
        ),
    },
    "New Drug": {
        "en": (
            "Novel formulation (ingredients not established in Ayurvedic use) or a "
            "product claiming a new therapeutic indication. Requires proof of "
            "safety and effectiveness: CDSCO/DCGI approval with mandatory Phase "
            "I-III clinical trials."
        ),
        "hi": (
            "नया योग (सामग्री आयुर्वेदिक उपयोग में स्थापित नहीं) या नए चिकित्सकीय दावे "
            "वाला उत्पाद। सुरक्षा और प्रभावकारिता के प्रमाण आवश्यक: CDSCO/DCGI "
            "अनुमोदन और अनिवार्य फेज़ I-III नैदानिक परीक्षण।"
        ),
    },
    "Ayurveda-Aahar": {
        "en": (
            "Food (including nutraceutical-style products) prepared according to "
            "Ayurveda-Aahara recipes, ingredients or processes, presented as "
            "food/wellness without treatment claims and without bhasma/pishti or "
            "Schedule E-1 herbs. Regulated by FSSAI under the Food Safety and "
            "Standards (Ayurveda Aahara) Regulations, 2022."
        ),
        "hi": (
            "आयुर्वेद-आहार विधियों, सामग्री या प्रक्रियाओं के अनुसार तैयार भोजन "
            "(पोषक-शैली के उत्पादों सहित), जो बिना उपचार दावों और बिना भस्म/पिष्टि या "
            "अनुसूची E-1 जड़ी-बूटियों के भोजन/स्वास्थ्य के रूप में प्रस्तुत होता है। "
            "FSSAI के खाद्य सुरक्षा और मानक (आयुर्वेद आहार) विनियम, 2022 के अंतर्गत "
            "विनियमित।"
        ),
    },
    "Cosmetic": {
        "en": (
            "Product applied externally for cleansing, beautifying or altering "
            "appearance, presented without therapeutic claims. Regulated under the "
            "Drugs and Cosmetics Act Cosmetic Rules."
        ),
        "hi": (
            "सफाई, सौंदर्यवर्धन या रूप-रंग बदलने हेतु बाहरी उपयोग का उत्पाद, बिना "
            "चिकित्सकीय दावों। औषधि एवं प्रसाधन अधिनियम के कॉस्मेटिक नियमों के "
            "अंतर्गत विनियमित।"
        ),
    },
    "Uncertain": {
        "en": (
            "The guided answers are incomplete, unclear or mutually contradictory, "
            "so no category can be assigned safely. Answer the clarification "
            "question(s) and classify again."
        ),
        "hi": (
            "दिए गए उत्तर अधूरे, अस्पष्ट या परस्पर विरोधी हैं, इसलिए कोई श्रेणी "
            "सुरक्षित रूप से निर्धारित नहीं की जा सकती। कृपया स्पष्टीकरण प्रश्नों के "
            "उत्तर दें और पुनः वर्गीकरण करें।"
        ),
    },
}

# Why each blocking question matters, keyed by question id. Used to compose
# clarification prompts (Uncertain results) and confirmation prompts
# (borderline results).
BLOCKING_REASONS = {
    "primary_purpose": {
        "en": (
            "the product's primary intended use must be known to choose between "
            "the medicine, food (Ayurveda-Aahar) and cosmetic tracks"
        ),
        "hi": (
            "औषधि, भोजन (आयुर्वेद-आहार) और कॉस्मेटिक मार्गों में से चुनने के लिए "
            "उत्पाद का प्राथमिक उपयोग जानना आवश्यक है"
        ),
    },
    "food_exclusion": {
        "en": (
            "whether the product contains bhasma/pishti or Schedule E-1 herbs, or "
            "carries treatment/cure claims, determines whether the food "
            "(Ayurveda-Aahar) category can apply at all"
        ),
        "hi": (
            "क्या उत्पाद में भस्म/पिष्टि या अनुसूची E-1 की जड़ी-बूटियाँ हैं, या "
            "उपचार/निवारण के दावे हैं - यह तय करता है कि भोजन (आयुर्वेद-आहार) "
            "श्रेणी लागू हो भी सकती है या नहीं"
        ),
    },
    "text_source": {
        "en": (
            "whether the formulation comes unchanged from an authoritative "
            "First-Schedule text separates Classical medicines from Proprietary / "
            "Phytopharmaceutical / New Drug products"
        ),
        "hi": (
            "क्या योग किसी प्रामाणिक प्रथम-अनुसूची ग्रंथ से अपरिवर्तित है - यह "
            "शास्त्रीय औषधि को प्रोप्राइटरी / फाइटो-फार्मास्यूटिकल / नई औषधि से "
            "अलग करता है"
        ),
    },
    "ingredients_known": {
        "en": (
            "whether all ingredients are already established in Ayurvedic use "
            "separates Proprietary medicines (known ingredients) from New Drugs "
            "(novel ingredients)"
        ),
        "hi": (
            "क्या सभी सामग्री आयुर्वेदिक उपयोग में पहले से स्थापित हैं - यह "
            "प्रोप्राइटरी औषधि (ज्ञात सामग्री) को नई औषधि (नई सामग्री) से अलग करता है"
        ),
    },
    "standardised_fraction": {
        "en": (
            "whether the product is a standardised fraction with defined active "
            "markers separates Phytopharmaceutical products from the other drug "
            "categories"
        ),
        "hi": (
            "क्या उत्पाद परिभाषित सक्रिय मार्करों वाला मानकीकृत अंश है - यह "
            "फाइटो-फार्मास्यूटिकल को अन्य औषधि श्रेणियों से अलग करता है"
        ),
    },
    "new_indication": {
        "en": (
            "whether the product claims a therapeutic indication not already "
            "established for these ingredients separates Proprietary medicines "
            "from New Drugs"
        ),
        "hi": (
            "क्या उत्पाद इन सामग्रियों के लिए पहले से स्थापित चिकित्सकीय दावा करता "
            "है - यह प्रोप्राइटरी औषधि को नई औषधि से अलग करता है"
        ),
    },
}

# Contradiction between "reproduced unchanged from an authoritative text"
# and "standardised fraction with defined active markers".
CONTRADICTION_TEXT_VS_STANDARDISED = {
    "en": (
        "the answers conflict: the product is described both as reproduced "
        "unchanged from an authoritative First-Schedule text and as a "
        "standardised fraction with defined active markers - please clarify "
        "which one describes the product"
    ),
    "hi": (
        "उत्तर परस्पर विरोधी हैं: उत्पाद को एक ही साथ प्रामाणिक प्रथम-अनुसूची ग्रंथ "
        "से अपरिवर्तित और परिभाषित सक्रिय मार्करों वाला मानकीकृत अंश दोनों बताया "
        "गया है - कृपया स्पष्ट करें कि इनमें से कौन-सा उत्पाद का वर्णन करता है"
    ),
}

# Prompt templates. The question text and reason are appended after these.
PROMPT_CLASSIFY = {
    "en": "To classify this product safely, please answer: ",
    "hi": "उत्पाद का सुरक्षित वर्गीकरण करने के लिए कृपया बताएं: ",
}
PROMPT_CONFIRM = {
    "en": "To confirm this classification, please also answer: ",
    "hi": "इस वर्गीकरण की पुष्टि के लिए कृपया यह भी बताएं: ",
}
