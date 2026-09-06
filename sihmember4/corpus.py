"""Member 4 Phase 1 — curated ABS / TK source corpus.

EVERY record below was verified on 2026-09-06 against the official document at
its URL (downloaded and text-extracted; see ``provenance`` on each record).
Excerpts are verbatim from the verified documents; whitespace/PDF-line-break
artifacts were normalised and any other deviation is disclosed in
``provenance``. Nothing in this corpus is invented: no provisions, no approval
requirements, no exemptions, no fees, no URLs, no citations.

TKDL constraint (MEMBER_4.md section 3): the TKDL record is a pointer /
description built only from the official public homepage (tkdl.res.in).
TKDL's full database content is restricted to patent offices under the TKDL
Access Agreement and is NOT reproduced here. No formulation counts, records,
classifications or patent-office results are claimed anywhere in this corpus.

Record schema (all fields required unless noted optional):
    id                   stable identifier (M4-SRC-NNN)
    source_name          official name of the source document
    source_type          statute | amendment_act | subordinate_legislation |
                         treaty | official_website
    section              section / article / rule marker (None only for
                         official_website records)
    excerpt              short verbatim excerpt from the verified source
    url                  the URL that was actually fetched and verified
    effective_date       ISO date if known, else None
    jurisdiction         India | International
    scope                explicit statement of what the provision covers
    keywords             curated retrieval tokens (our own tagging; not part
                         of the legal text)
    tkdl_pointer_record  True only for the TKDL pointer record
    pointer_guidance     (TKDL record only) how Phase 2 must use this record
    provenance           verification metadata; keys verified_on,
                         verification_method, document_identity always present;
                         optional canonical_source, commencement_verification,
                         notes.
"""

CORPUS_VERSION = "m4-abs-phase1-2026-09-06"

VERIFIED_ON = "2026-09-06"

_GAZETTE_AMENDMENT_2023 = (
    "Biological Diversity (Amendment) Act, 2023 (Act No. 10 of 2023), "
    "Gazette of India Extraordinary, Part II - Section 1, published 3 August 2023"
)

_AMENDMENT_GAZETTE_URL = "https://egazette.gov.in/WritereadData/2023/247815.pdf"

_AMENDMENT_PROVENANCE = {
    "verified_on": VERIFIED_ON,
    "verification_method": (
        "Official Gazette PDF downloaded (HTTP 200) and text extracted with "
        "pypdf; quoted passages located in the extracted text."
    ),
    "document_identity": (
        "Gazette of India Extraordinary CG-DL-E-03082023-247815, "
        "Ministry of Law and Justice, assent of the President 3 August 2023; "
        "Act No. 10 of 2023."
    ),
    "commencement_verification": (
        "Effective date 2024-04-01 verified from MoEFCC notification S.O. "
        "295(E) dated 18 January 2024, which appoints 'the 1st day of April, "
        "2024 as the date on which the said Act shall come into force'. "
        "Verified from the Gazette of India Extraordinary No. 286 of "
        "19 January 2024 (CG-DL-E-20012024-251527), official copy hosted by "
        "the National Biodiversity Authority: "
        "https://www.nbaindia.nic.in/sites/default/files/2026-05/BDAct_Gazette.pdf"
    ),
    "notes": (
        "PDF text layer reflows words across lines; spacing artifacts were "
        "normalised. Ellipses [...] in excerpts elide repeated statutory "
        "language, disclosed per record below."
    ),
}

SOURCE_RECORDS = [
    # ------------------------------------------------------------------ 1
    {
        "id": "M4-SRC-001",
        "source_name": "The Biological Diversity Act, 2002 (Act No. 18 of 2003)",
        "source_type": "statute",
        "section": "Section 3(1)",
        "excerpt": (
            "3. (1) No person referred to in sub-section (2) shall, without "
            "previous approval of the National Biodiversity Authority, obtain "
            "any biological resource occurring in India or knowledge associated "
            "thereto for research or for commercial utilization or for "
            "bio-survey and bio-utilisation."
        ),
        "url": "https://megbiodiversity.nic.in/sites/default/files/Biodiversity_Act_2002.pdf",
        "effective_date": "2003-02-05",
        "jurisdiction": "India",
        "scope": (
            "Persons needing prior NBA approval under section 3 are defined in "
            "section 3(2): a non-citizen; a non-resident citizen; and a body "
            "corporate, association or organisation not incorporated/registered "
            "in India or incorporated/registered in India with foreign control. "
            "The 2023 Amendment substituted section 3(2)(c)(ii) to cover "
            "entities incorporated or registered in India 'which is controlled "
            "by a foreigner within the meaning of clause (27) of section 2 of "
            "the Companies Act, 2013'. Section 3(1) itself was not amended."
        ),
        "keywords": [
            "nba approval", "foreign", "non-citizen", "non-resident",
            "body corporate", "foreign-controlled", "access", "biological resource",
            "bio-survey", "commercial utilisation", "commercial utilization",
            "national biodiversity authority",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            "verified_on": VERIFIED_ON,
            "verification_method": (
                "PDF downloaded (HTTP 200, application/pdf) from the Meghalaya "
                "Biodiversity Board (megbiodiversity.nic.in, official NIC "
                "government domain) and text extracted with pypdf; section 3(1) "
                "located and quoted verbatim."
            ),
            "document_identity": (
                "THE BIOLOGICAL DIVERSITY ACT, 2002, No. 18 OF 2003 "
                "(5th February, 2003) - full act text."
            ),
            "canonical_source": (
                "India Code (indiacode.gov.in) is the canonical consolidated "
                "source. Scripted access to India Code was not possible during "
                "verification (legacy indiacode.nic.in serves a site-migration "
                "notice; the new portal is a client-side application), so the "
                "verbatim text was verified from the government-hosted copy "
                "above instead. This is a government mirror, not a substitute "
                "authority - the Act itself is the authority."
            ),
            "notes": (
                "Spelling 'commercial utilization' in section 3(1) follows the "
                "source text. Section 3(2)(c)(ii) amendment wording verified "
                "separately from the 2023 Amendment Gazette "
                "(https://egazette.gov.in/WritereadData/2023/247815.pdf)."
            ),
        },
    },
    # ------------------------------------------------------------------ 2
    {
        "id": "M4-SRC-002",
        "source_name": _GAZETTE_AMENDMENT_2023,
        "source_type": "amendment_act",
        "section": "Section 6(1A) and 6(1B) (substituted)",
        "excerpt": (
            "(1A) Any person covered under section 7 applying for any "
            "intellectual property right, by whatever name called, in or "
            "outside India, for any invention based on any research or "
            "information on a biological resource which is accessed from India "
            "[...] shall register with the National Biodiversity Authority "
            "before grant of such intellectual property rights. (1B) Any "
            "person covered under section 7 who has obtained intellectual "
            "property right [...] shall obtain prior approval of the National "
            "Biodiversity Authority at the time of commercialisation."
        ),
        "url": _AMENDMENT_GAZETTE_URL,
        "effective_date": "2024-04-01",
        "jurisdiction": "India",
        "scope": (
            "After the 2023 Amendment, Indian persons (covered under section 7) "
            "must register with the NBA before grant of an IPR based on "
            "biological resources accessed from India or associated traditional "
            "knowledge, and obtain prior NBA approval at the time of "
            "commercialisation. Persons/entities covered under section 3(2) "
            "(foreign-controlled) must instead obtain prior NBA approval "
            "before grant of the IPR (amended section 6(1), same Gazette)."
        ),
        "keywords": [
            "intellectual property right", "ipr", "patent", "register",
            "registration", "nba", "national biodiversity authority",
            "approval", "commercialisation", "commercialization", "grant",
            "biological resource", "traditional knowledge",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            **_AMENDMENT_PROVENANCE,
            "notes": (
                "Ellipses [...] elide the repeated phrase 'including those "
                "deposited in repositories outside India, or traditional "
                "knowledge associated thereto'. One apparent typographical "
                "variant in the Gazette text layer ('Biodivesity') and the "
                "line-break artifact 'commerciali sation' were normalised; "
                "substance unchanged and disclosed here."
            ),
        },
    },
    # ------------------------------------------------------------------ 3
    {
        "id": "M4-SRC-003",
        "source_name": _GAZETTE_AMENDMENT_2023,
        "source_type": "amendment_act",
        "section": "Section 7 (substituted)",
        "excerpt": (
            "7. (1) No person, other than the person covered under "
            "sub-section (2) of section 3, shall access any biological resource "
            "and its associated knowledge for commercial utilisation, without "
            "giving prior intimation to the concerned State Biodiversity "
            "Board, but such access shall be subject to the provisions of "
            "clause (b) of section 23 and sub-section (2) of section 24: "
            "Provided that the provisions of this section shall not apply to "
            "the codified traditional knowledge, cultivated medicinal plants "
            "and its products, local people and communities of the area, "
            "including growers and cultivators of biodiversity and to vaids, "
            "hakims and registered AYUSH practitioners only who have been "
            "practicing indigenous medicines, including Indian systems of "
            "medicine as profession for sustenance and livelihood."
        ),
        "url": _AMENDMENT_GAZETTE_URL,
        "effective_date": "2024-04-01",
        "jurisdiction": "India",
        "scope": (
            "Indian persons accessing biological resources and associated "
            "knowledge for commercial utilisation must give prior intimation "
            "to the concerned State Biodiversity Board, except for codified "
            "traditional knowledge, cultivated medicinal plants and their "
            "products, local people and communities, and vaids, hakims and "
            "registered AYUSH practitioners practising indigenous medicine for "
            "sustenance and livelihood. Substituted section 7(2)-(3) "
            "additionally require that the cultivated-medicinal-plants "
            "exemption is available only if a certificate of origin is "
            "obtained from the Biodiversity Management Committee in the "
            "prescribed manner."
        ),
        "keywords": [
            "commercialise", "commercialisation", "commercial utilisation",
            "approval", "approvals", "state biodiversity board", "sbb",
            "prior intimation", "exemption", "ayush", "codified traditional knowledge",
            "cultivated medicinal plants", "plant", "plants", "biological resource",
            "formulation", "formulations", "vaids", "hakims",
            "biodiversity management committee", "certificate of origin",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            **_AMENDMENT_PROVENANCE,
            "notes": (
                "Clause 9 of the Amendment Act substitutes section 7 in full; "
                "the substituted text was located in the Gazette and quoted "
                "verbatim (spacing artifacts normalised). Marginal heading in "
                "the Gazette: 'Prior intimation to State Biodiversity Board "
                "for accessing biological resource for certain purposes'."
            ),
        },
    },
    # ------------------------------------------------------------------ 4
    {
        "id": "M4-SRC-004",
        "source_name": _GAZETTE_AMENDMENT_2023,
        "source_type": "amendment_act",
        "section": "Section 21(1) (amended)",
        "excerpt": (
            "(1) The National Biodiversity Authority shall, while determining "
            "benefit sharing for the approval granted under this Act, ensure "
            "that the terms and conditions subject to which the approval is "
            "granted secures fair and equitable sharing of benefits arising "
            "out of the use of accessed biological resources, their "
            "derivatives, innovations and practices associated with their use "
            "and applications and knowledge relating thereto in accordance "
            "with mutually agreed terms and conditions [...]"
        ),
        "url": _AMENDMENT_GAZETTE_URL,
        "effective_date": "2024-04-01",
        "jurisdiction": "India",
        "scope": (
            "Benefit sharing is a condition the NBA attaches to approvals: "
            "terms must secure fair and equitable sharing of benefits "
            "(monetary or otherwise) arising from use of accessed biological "
            "resources, derivatives, innovations, practices and knowledge, in "
            "accordance with mutually agreed terms. Amended section 21(3) "
            "proviso additionally lets the NBA direct payment directly to "
            "benefit claimers per the terms of an agreement."
        ),
        "keywords": [
            "benefit sharing", "benefits", "fair and equitable",
            "mutually agreed terms", "nba", "national biodiversity authority",
            "approval", "derivatives", "benefit claimers",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            **_AMENDMENT_PROVENANCE,
            "notes": (
                "Clause 19 of the Amendment Act amends section 21. The final "
                "clause of substituted 21(1) (naming the Biodiversity "
                "Management Committee, represented by the NBA) is elided with "
                "[...] because the Gazette text layer prints 'Commitee' "
                "(printing error); the elision is disclosed rather than "
                "silently corrected."
            ),
        },
    },
    # ------------------------------------------------------------------ 5
    {
        "id": "M4-SRC-005",
        "source_name": (
            "The Biological Diversity Rules, 2024 (G.S.R. 665(E), "
            "Ministry of Environment, Forest and Climate Change)"
        ),
        "source_type": "subordinate_legislation",
        "section": "Rule 13(1) (Procedure for access to biological resources and knowledge associated thereto)",
        "excerpt": (
            "13. Procedure for access to biological resources and knowledge "
            "associated thereto. - (1) Any person, referred to in sub-section "
            "(2) of section 3 of the Act, seeking approval of the Authority "
            "for access to biological resources and knowledge associated "
            "thereto for research or for bio-survey and bio-utilisation shall "
            "make an application on the web portal of the Authority in "
            "Form 1, and for commercial utilisation shall make an application "
            "on the web portal of the Authority in Form 2."
        ),
        "url": "https://www.nbaindia.nic.in/sites/default/files/2026-05/BD_Rules.pdf",
        "effective_date": "2024-12-21",
        "jurisdiction": "India",
        "scope": (
            "Prescribes how persons covered under section 3(2) of the Act "
            "(foreign-controlled/non-citizen persons) apply to the NBA: via "
            "the Authority's web portal, Form 1 for research or bio-survey and "
            "bio-utilisation, Form 2 for commercial utilisation. Rule 13(3) "
            "requires every application to be accompanied by the specified fee "
            "paid electronically to the National Biodiversity Fund. The 2024 "
            "Rules supersede the Biological Diversity Rules, 2004."
        ),
        "keywords": [
            "form 2", "form 1", "web portal", "application", "nba",
            "national biodiversity authority", "access", "commercial utilisation",
            "commercialisation", "approval", "biological resources",
            "bio-survey", "bio-utilisation", "rules 2024",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            "verified_on": VERIFIED_ON,
            "verification_method": (
                "Official Gazette PDF of the Rules downloaded from the "
                "National Biodiversity Authority website (HTTP 200, 2.4 MB, "
                "bilingual Hindi/English) and text extracted with pypdf; "
                "notification header and Rule 13(1) quoted from the extracted "
                "text."
            ),
            "document_identity": (
                "THE GAZETTE OF INDIA : EXTRAORDINARY [PART II - SEC. 3(i)], "
                "MINISTRY OF ENVIRONMENT, FOREST AND CLIMATE CHANGE, "
                "NOTIFICATION, New Delhi, the 22nd October, 2024, G.S.R. "
                "665(E), in supersession of the Biological Diversity Rules, "
                "2004."
            ),
            "notes": (
                "Rule 1: 'They shall come into force on expiry of sixty days "
                "from the date of their notification in the Official "
                "Gazette.' Notification date 22 October 2024 verified from "
                "the Gazette header; effective_date 2024-12-21 is computed as "
                "60 days after notification - secondary sources cite 21-24 "
                "December 2024, so re-verify the precise day before relying "
                "on it. WIPO Lex (record 23135) independently lists date of "
                "text as 22 October 2024. A Biological Diversity (Amendment) "
                "Rules, 2025 exists per WIPO Lex and the NBA rules page; it "
                "is not covered by this Phase 1 corpus."
            ),
        },
    },
    # ------------------------------------------------------------------ 6
    {
        "id": "M4-SRC-006",
        "source_name": (
            "Nagoya Protocol on Access to Genetic Resources and the Fair and "
            "Equitable Sharing of Benefits Arising from their Utilization to "
            "the Convention on Biological Diversity"
        ),
        "source_type": "treaty",
        "section": "Article 5(5)",
        "excerpt": (
            "Each Party shall take legislative, administrative or policy "
            "measures, as appropriate, in order that the benefits arising from "
            "the utilization of traditional knowledge associated with genetic "
            "resources are shared in a fair and equitable way with indigenous "
            "and local communities holding such knowledge. Such sharing shall "
            "be upon mutually agreed terms."
        ),
        "url": "https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
        "effective_date": "2014-10-12",
        "jurisdiction": "International",
        "scope": (
            "ABS-regulation obligation under the Nagoya Protocol: benefits "
            "from the utilization of traditional knowledge associated with "
            "genetic resources must be shared fairly and equitably with the "
            "indigenous and local communities holding that knowledge, on "
            "mutually agreed terms. India is a Party (stated in the preamble "
            "of the Biological Diversity (Amendment) Act, 2023)."
        ),
        "keywords": [
            "nagoya", "protocol", "benefit sharing", "benefits", "fair and equitable",
            "mutually agreed terms", "traditional knowledge", "genetic resources",
            "indigenous", "local communities", "cbd",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            "verified_on": VERIFIED_ON,
            "verification_method": (
                "Official CBD Secretariat PDF ('TEXT AND ANNEX') downloaded "
                "(HTTP 200) and text extracted with pypdf; Article 5 located "
                "by its heading 'FAIR AND EQUITABLE BENEFIT-SHARING' and "
                "paragraph 5 quoted verbatim (PDF hyphenation/spacing "
                "normalised)."
            ),
            "document_identity": (
                "Secretariat of the Convention on Biological Diversity, "
                "Montreal, 'Nagoya Protocol on Access to Genetic Resources "
                "and the Fair and Equitable Sharing of Benefits Arising from "
                "their Utilization to the Convention on Biological Diversity "
                "- Text and Annex'."
            ),
            "notes": (
                "Adopted at COP-10 on 29 October 2010 in Nagoya, Japan "
                "(verified from the same PDF's introduction); entry into "
                "force 12 October 2014, 90 days after the deposit of the "
                "fiftieth instrument of ratification (verified from "
                "https://www.cbd.int/abs/about). Article 33 of the PDF text "
                "states the 90-day/50th-ratification mechanism."
            ),
        },
    },
    # ------------------------------------------------------------------ 7
    {
        "id": "M4-SRC-007",
        "source_name": (
            "Nagoya Protocol on Access to Genetic Resources and the Fair and "
            "Equitable Sharing of Benefits Arising from their Utilization to "
            "the Convention on Biological Diversity"
        ),
        "source_type": "treaty",
        "section": "Article 6(1)",
        "excerpt": (
            "In the exercise of sovereign rights over natural resources, and "
            "subject to domestic access and benefit-sharing legislation or "
            "regulatory requirements, access to genetic resources for their "
            "utilization shall be subject to the prior informed consent of the "
            "Party providing such resources that is the country of origin of "
            "such resources or a Party that has acquired the genetic resources "
            "in accordance with the Convention, unless otherwise determined by "
            "that Party."
        ),
        "url": "https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
        "effective_date": "2014-10-12",
        "jurisdiction": "International",
        "scope": (
            "Access obligation: access to genetic resources for utilization "
            "is subject to the prior informed consent (PIC) of the providing "
            "Party, unless that Party otherwise determines. India implements "
            "PIC domestically through the Biological Diversity Act framework."
        ),
        "keywords": [
            "nagoya", "protocol", "prior informed consent", "pic",
            "access", "genetic resources", "sovereign rights", "cbd",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            "verified_on": VERIFIED_ON,
            "verification_method": (
                "Same official CBD PDF as M4-SRC-006; Article 6 located by "
                "its heading 'ACCESS TO GENETIC RESOURCES' and paragraph 1 "
                "quoted verbatim (spacing normalised)."
            ),
            "document_identity": "Same document as M4-SRC-006.",
            "notes": "Entry-into-force date as for M4-SRC-006.",
        },
    },
    # ------------------------------------------------------------------ 8
    {
        "id": "M4-SRC-008",
        "source_name": (
            "Nagoya Protocol on Access to Genetic Resources and the Fair and "
            "Equitable Sharing of Benefits Arising from their Utilization to "
            "the Convention on Biological Diversity"
        ),
        "source_type": "treaty",
        "section": "Article 7",
        "excerpt": (
            "In accordance with domestic law, each Party shall take measures, "
            "as appropriate, with the aim of ensuring that traditional "
            "knowledge associated with genetic resources that is held by "
            "indigenous and local communities is accessed with the prior and "
            "informed consent or approval and involvement of these indigenous "
            "and local communities, and that mutually agreed terms have been "
            "established."
        ),
        "url": "https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
        "effective_date": "2014-10-12",
        "jurisdiction": "International",
        "scope": (
            "Traditional-knowledge access obligation: TK associated with "
            "genetic resources and held by indigenous and local communities "
            "must be accessed with their prior and informed consent or "
            "approval and involvement, and with mutually agreed terms "
            "established."
        ),
        "keywords": [
            "nagoya", "protocol", "traditional knowledge",
            "prior and informed consent", "indigenous", "local communities",
            "mutually agreed terms", "cbd",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            "verified_on": VERIFIED_ON,
            "verification_method": (
                "Same official CBD PDF as M4-SRC-006; Article 7 located by "
                "its heading 'ACCESS TO TRADITIONAL KNOWLEDGE ASSOCIATED WITH "
                "GENETIC RESOURCES' and quoted verbatim in full."
            ),
            "document_identity": "Same document as M4-SRC-006.",
            "notes": "Entry-into-force date as for M4-SRC-006.",
        },
    },
    # ------------------------------------------------------------------ 9
    {
        "id": "M4-SRC-009",
        "source_name": (
            "Convention on Biological Diversity (Rio de Janeiro, 5 June 1992)"
        ),
        "source_type": "treaty",
        "section": "Article 8(j)",
        "excerpt": (
            "Subject to its national legislation, respect, preserve and "
            "maintain knowledge, innovations and practices of indigenous and "
            "local communities embodying traditional lifestyles relevant for "
            "the conservation and sustainable use of biological diversity and "
            "promote their wider application with the approval and involvement "
            "of the holders of such knowledge, innovations and practices and "
            "encourage the equitable sharing of the benefits arising from the "
            "utilization of such knowledge, innovations and practices;"
        ),
        "url": "https://www.cbd.int/doc/legal/cbd-en.pdf",
        "effective_date": "1993-12-29",
        "jurisdiction": "International",
        "scope": (
            "The CBD's traditional-knowledge provision - the foundational "
            "international description of traditional knowledge as the "
            "knowledge, innovations and practices of indigenous and local "
            "communities, to be respected, preserved, maintained and applied "
            "with the holders' approval and involvement, with equitable "
            "benefit sharing. India is a Party (recited in the preamble of "
            "the Biological Diversity Act, 2002)."
        ),
        "keywords": [
            "cbd", "convention on biological diversity", "traditional knowledge",
            "knowledge, innovations and practices", "indigenous",
            "local communities", "benefit sharing",
        ],
        "tkdl_pointer_record": False,
        "provenance": {
            "verified_on": VERIFIED_ON,
            "verification_method": (
                "Official CBD treaty PDF downloaded (HTTP 200) and text "
                "extracted with pypdf; Article 8, item (j) located and quoted "
                "verbatim."
            ),
            "document_identity": (
                "Secretariat of the Convention on Biological Diversity, "
                "'Convention on Biological Diversity' treaty text."
            ),
            "notes": (
                "Entry into force 29 December 1993 verified from the same "
                "PDF's introduction."
            ),
        },
    },
    # ------------------------------------------------------------------ 10
    {
        "id": "M4-SRC-010",
        "source_name": (
            "Traditional Knowledge Digital Library (TKDL) - official website, "
            "initiative of CSIR and Ministry of Ayush"
        ),
        "source_type": "official_website",
        "section": None,
        "excerpt": (
            "Representative Database of Ayurvedic, Unani, Siddha and Sowarigpa "
            "Formulations [...] Access to the full database is available to "
            "Patent Offices only under TKDL Access Agreement [...] Initiative "
            "of Council of Scientific & Industrial Research (CSIR) [...] "
            "Ministry of Ayurveda, Yoga & Naturopathy, Unani, Siddha and "
            "Homeopathy (AYUSH)"
        ),
        "url": "https://tkdl.res.in/",
        "effective_date": None,
        "jurisdiction": "India",
        "scope": (
            "POINTER ONLY - describes TKDL's public role, not its contents. "
            "Per the official homepage: TKDL is an initiative of CSIR and the "
            "Ministry of Ayush maintaining a representative database of "
            "Ayurvedic, Unani, Siddha and Sowarigpa formulations, and access "
            "to the full database is available to Patent Offices only under "
            "the TKDL Access Agreement. For any question about traditional "
            "knowledge as prior art, the correct behaviour is to point the "
            "user to TKDL and to a patent professional - never to reproduce "
            "or paraphrase TKDL's internal database content."
        ),
        "keywords": [
            "tkdl", "traditional knowledge digital library", "prior art",
            "defensive publication", "patent office", "csir", "ayush",
            "ayurveda", "unani", "siddha", "sowarigpa", "traditional knowledge",
        ],
        "tkdl_pointer_record": True,
        "pointer_guidance": (
            "Use this record only as a pointer/description. If a question "
            "involves traditional knowledge or prior art, advise: this is "
            "traditional knowledge that TKDL (tkdl.res.in) may cover; access "
            "to the full database is available to patent offices only under "
            "the TKDL Access Agreement - consult TKDL via the relevant patent "
            "examiner or a patent professional. Never quote, paraphrase in "
            "detail, or fabricate TKDL database content; never state "
            "'TKDL says X'; never cite formulation counts, records or "
            "patent-office outcomes as TKDL facts."
        ),
        "provenance": {
            "verified_on": VERIFIED_ON,
            "verification_method": (
                "Homepage fetched (HTTP 200) and visible text extracted; the "
                "excerpt joins three verbatim homepage fragments with [...] "
                "separators: the site banner, the access-restriction notice, "
                "and the ownership line. No other content from TKDL was used."
            ),
            "document_identity": (
                "tkdl.res.in homepage: 'TKDL Traditional Knowledge Digital "
                "Library'; navigation includes About TKDL, FAQ, Bio-Piracy, "
                "TKDL Outcomes, Contact Us."
            ),
            "notes": (
                "TKDL's full database content is restricted to patent offices "
                "under the TKDL Access Agreement and must never be reproduced "
                "here. Deliberately no counts of formulations, records, "
                "classifications or patent-office outcomes are included, "
                "because they are not verifiable from the public homepage "
                "text used for this record."
            ),
        },
    },
]


def record_ids():
    """Stable, ordered list of record ids (determinism anchor)."""
    return [r["id"] for r in SOURCE_RECORDS]


def get_record(record_id):
    """Return the record with the given id, or None."""
    for record in SOURCE_RECORDS:
        if record["id"] == record_id:
            return record
    return None


def to_citation(record):
    """Map a corpus record onto the shared Citation shape from Plan.md section 7."""
    return {
        "id": record["id"],
        "source_name": record["source_name"],
        "source_type": record["source_type"],
        "section": record["section"],
        "excerpt": record["excerpt"],
        "url": record["url"],
        "effective_date": record["effective_date"],
    }


TKDL_RECORD_ID = "M4-SRC-010"
