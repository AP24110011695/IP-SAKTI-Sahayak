"""Member 3 — India Source Foundation (Phase 1).

A small, curated corpus of REAL Indian statutory/regulatory source records
covering the priority scope in MEMBER_3.md. Every record carries complete
metadata (source name, type, section, verbatim excerpt, URL, effective date,
explicit India jurisdiction) and a verification entry describing exactly how
the URL/excerpt was checked (checked on 2026-09-06):

- "downloaded+extracted": the official PDF was downloaded and the excerpt
  extracted verbatim from it (light whitespace normalisation only).
- "mirror-verified": the live automated fetch of the official page is bot-
  walled (HTTP stub to scripted clients), so the section text was verified
  verbatim against the Indian Kanoon mirror of the same Act; the recorded URL
  is the canonical official page (HTTP 200).

 NOTHING IN THIS FILE IS LEGAL GUIDANCE. This is a source index only; the
 guidance layer belongs to Phase 2. Nothing is invented: statutes, sections,
 URLs and excerpts all trace to the sources named in each record.

Excerpt conventions: excerpts are verbatim quotes of the provision as printed
in the cited source, except that (a) whitespace is normalised, (b) obvious
PDF-extraction hyphen/spacing artefacts are joined (noted per record), and
(c) square brackets such as [sixty years] are amendment annotations printed
in the source itself and are preserved as-is.
"""

import re

# Priority scope areas (MEMBER_3.md Section 1)
SCOPE_AREAS = (
    "patents",
    "geographical_indications",
    "trademarks",
    "copyright",
    "designs",
    "ppv_fr",
    "drugs_cosmetics",
    "drugs_magic_remedies",
    "fssai_ayurveda_aahara",
    "biological_diversity",
)

SOURCE_TYPES = ("statute", "rules", "regulation", "registry_notice")

JURISDICTION = "India"

_CORPUS_TUPLE = (
    # ------------------------------------------------------------------
    # Patents — golden scenario 1 ("Can I patent a classical Ayurvedic
    # formulation from an authoritative text?")
    # ------------------------------------------------------------------
    {
        "id": "patents_act_1970_s3p",
        "source_name": "The Patents Act, 1970 (Act 39 of 1970) — consolidated text, IP India",
        "source_type": "statute",
        "issuer": "Government of India; hosted by IP India (Office of CGPDTM)",
        "jurisdiction": "India",
        "scope_area": "patents",
        "section": "Section 3(p)",
        "section_title": "What are not inventions — clause (p) (traditional knowledge)",
        "excerpt": (
            "(p) an invention which, in effect, is traditional knowledge or which "
            "is an aggregation or duplication of known properties of traditionally "
            "known component or components."
        ),
        "url": (
            "https://ipindia.gov.in/frontend/pdf/patents/"
            "1_113_1_The_Patents_Act__1970___incorporating_all_amendments_till_1-08-2024.pdf"
        ),
        "effective_date": (
            "Act 39 of 1970; consolidated official text includes amendments in "
            "force up to 1 August 2024"
        ),
        "tags": [
            "patents", "patent", "invention", "not patentable", "traditional knowledge",
            "tk", "section 3p", "3(p)", "ayurveda", "classical formulation",
            "biopiracy", "aggregation", "known properties",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 665,996 bytes)",
            "notes": (
                "Excerpt extracted verbatim (whitespace normalised) from the "
                "official IP India consolidated PDF. Trailing ']' of the source "
                "print (amendment marker) omitted. Clause (p) was inserted by the "
                "Patents (Amendment) Act, 2002. Cross-checked against the Act "
                "mirror on Indian Kanoon (doc/874310)."
            ),
        },
    },
    {
        "id": "patents_act_1970_s2j",
        "source_name": "The Patents Act, 1970 (Act 39 of 1970) — consolidated text, IP India",
        "source_type": "statute",
        "issuer": "Government of India; hosted by IP India (Office of CGPDTM)",
        "jurisdiction": "India",
        "scope_area": "patents",
        "section": "Section 2(1)(j)",
        "section_title": "Definitions and interpretation — 'invention'",
        "excerpt": (
            "(j) “invention” means a new product or process involving an inventive "
            "step and capable of industrial application;"
        ),
        "url": (
            "https://ipindia.gov.in/frontend/pdf/patents/"
            "1_113_1_The_Patents_Act__1970___incorporating_all_amendments_till_1-08-2024.pdf"
        ),
        "effective_date": (
            "Act 39 of 1970; consolidated official text includes amendments in "
            "force up to 1 August 2024"
        ),
        "tags": [
            "patents", "patent", "invention", "definition", "inventive step",
            "industrial application", "novelty", "patentability",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf)",
            "notes": (
                "Verbatim from the same official consolidated PDF; a PDF-extraction "
                "spacing artefact ('involv ing') joined to 'involving'."
            ),
        },
    },
    {
        "id": "patents_act_1970_s10_4d",
        "source_name": "The Patents Act, 1970 (Act 39 of 1970) — consolidated text, IP India",
        "source_type": "statute",
        "issuer": "Government of India; hosted by IP India (Office of CGPDTM)",
        "jurisdiction": "India",
        "scope_area": "patents",
        "section": "Section 10(4)(d), proviso (ii), sub-clause (D)",
        "section_title": (
            "Contents of specification — disclosure of source and geographical "
            "origin of biological material"
        ),
        "excerpt": (
            "(D) disclose the source and geographical origin of the biological "
            "material in the specification, when used in an invention."
        ),
        "url": (
            "https://ipindia.gov.in/frontend/pdf/patents/"
            "1_113_1_The_Patents_Act__1970___incorporating_all_amendments_till_1-08-2024.pdf"
        ),
        "effective_date": (
            "Act 39 of 1970; consolidated official text includes amendments in "
            "force up to 1 August 2024"
        ),
        "tags": [
            "patents", "biological material", "disclosure", "specification",
            "geographical origin", "budapest treaty", "deposition", "ayurveda",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf)",
            "notes": (
                "Verbatim from the official consolidated PDF. Structural note: the "
                "disclosure duty sits in the proviso to Section 10(4)(d) (the "
                "abstract clause), sub-proviso (ii) about biological material, "
                "sub-clause (D) — NOT in standalone Section 10(4)(d). The same "
                "proviso (ii) references deposit of biological material at an "
                "international depository authority under the Budapest Treaty."
            ),
        },
    },
    # ------------------------------------------------------------------
    # Geographical Indications — golden scenario 2 (GI registration)
    # ------------------------------------------------------------------
    {
        "id": "gi_act_1999_s2_1e",
        "source_name": (
            "The Geographical Indications of Goods (Registration and Protection) "
            "Act, 1999 (Act 48 of 1999) — Gazette text, IP India"
        ),
        "source_type": "statute",
        "issuer": "Government of India; hosted by IP India (Office of CGPDTM)",
        "jurisdiction": "India",
        "scope_area": "geographical_indications",
        "section": "Section 2(1)(e)",
        "section_title": "Definitions and interpretation — 'geographical indication'",
        "excerpt": (
            "(e) “geographical indication”, in relation to goods, means an "
            "indication which identifies such goods as agricultural goods, natural "
            "goods or manufactured goods as originating, or manufactured in the "
            "territory of a country, or a region or locality in that territory, "
            "where a given quality, reputation or other characteristic of such "
            "goods is essentially attributable to its geographical origin and in "
            "case where such goods are manufactured goods one of the activities of "
            "either the production or of processing or preparation of the goods "
            "concerned takes place in such territory, region or locality, as the "
            "case may be."
        ),
        "url": (
            "https://ipindia.gov.in/storage/uploads/docs-operator/"
            "5720e089-4967-408c-bc76-031d2a7fd72c.pdf"
        ),
        "effective_date": "Act 48 of 1999 (Gazette of India Extraordinary, 30 December 1999)",
        "tags": [
            "gi", "geographical indication", "definition", "goods", "origin",
            "region", "reputation", "quality", "registration", "tag",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 37 pages)",
            "notes": (
                "Verbatim from the official IP India Gazette PDF of the Act "
                "(as enacted). PRECISION NOTE: in this Act the GI definition is "
                "clause (e) of Section 2(1) — the frequent citation '2(1)(f)' "
                "actually defines 'goods'. Verified clause letters directly from "
                "the Gazette print. India Code also hosts the Act (handle "
                "123456789/2049, HTTP 200; body bot-walled to scripted fetches)."
            ),
        },
    },
    {
        "id": "gi_act_1999_s11_1",
        "source_name": (
            "The Geographical Indications of Goods (Registration and Protection) "
            "Act, 1999 (Act 48 of 1999) — Gazette text, IP India"
        ),
        "source_type": "statute",
        "issuer": "Government of India; hosted by IP India (Office of CGPDTM)",
        "jurisdiction": "India",
        "scope_area": "geographical_indications",
        "section": "Section 11(1)",
        "section_title": "Application for registration of a geographical indication — who may apply",
        "excerpt": (
            "11. (1) Any association of persons or producers or any organization "
            "or authority established by or under any law for the time being in "
            "force representing the interest of the producers of the concerned "
            "goods, who are desirous of registering a geographical indication in "
            "relation to such goods shall apply in writing to the Registrar in "
            "such form and in such manner and accompanied by such fees as may be "
            "prescribed for the registration of the geographical indication."
        ),
        "url": (
            "https://ipindia.gov.in/storage/uploads/docs-operator/"
            "5720e089-4967-408c-bc76-031d2a7fd72c.pdf"
        ),
        "effective_date": "Act 48 of 1999 (Gazette of India Extraordinary, 30 December 1999)",
        "tags": [
            "gi", "geographical indication", "registration", "apply", "applicant",
            "producers", "association", "registrar", "form", "fees", "gi tag",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 37 pages)",
            "notes": (
                "Verbatim from the official IP India Gazette PDF (as enacted). "
                "Application form/fee specifics live in the GI Rules and registry "
                "practice — deliberately NOT recorded here to avoid inventing "
                "fee figures; Phase 2 should cite the GI Registry/ GI Rules "
                "directly if it needs them."
            ),
        },
    },
    # ------------------------------------------------------------------
    # Trade Marks
    # ------------------------------------------------------------------
    {
        "id": "tm_act_1999_s9_1b",
        "source_name": (
            "The Trade Marks Act, 1999 (Act 47 of 1999) — Gazette text, IP India"
        ),
        "source_type": "statute",
        "issuer": "Government of India; hosted by IP India (Office of CGPDTM)",
        "jurisdiction": "India",
        "scope_area": "trademarks",
        "section": "Section 9(1)(b)",
        "section_title": "Grounds for refusal of registration — absolute grounds (descriptive marks)",
        "excerpt": (
            "(b) which consist exclusively of marks or indications which may serve "
            "in trade to designate the kind, quality, quantity, intended purpose, "
            "values, geographical origin or the time of production of the goods or "
            "rendering of the service or other characteristics of the goods or "
            "services;"
        ),
        "url": (
            "https://ipindia.gov.in/storage/uploads/docs-operator/"
            "c9e8a57e-bc94-4b93-8518-6e8729c976bf.pdf"
        ),
        "effective_date": (
            "Act 47 of 1999; in force since 15 September 2003 (per IP India)"
        ),
        "tags": [
            "trademark", "trade marks", "registration", "refusal", "descriptive",
            "distinctive character", "generic", "brand", "brand name",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 51 pages)",
            "notes": (
                "Verbatim from the official IP India Gazette PDF of the Trade "
                "Marks Act, 1999 (Act 47 of 1999). Relevant to the Research.md "
                "note that generic Ayurveda terms (e.g. 'Chyawanprash') may face "
                "descriptiveness challenges under Section 9. The source print "
                "shows minor typesetting artefacts around dashes/semicolons; "
                "clause lettering and wording are as printed."
            ),
        },
    },
    # ------------------------------------------------------------------
    # Designs
    # ------------------------------------------------------------------
    {
        "id": "designs_act_2000_s2d",
        "source_name": "The Designs Act, 2000 (Act 16 of 2000) — Gazette text, IP India",
        "source_type": "statute",
        "issuer": "Government of India; hosted by IP India (Office of CGPDTM)",
        "jurisdiction": "India",
        "scope_area": "designs",
        "section": "Section 2(d)",
        "section_title": "Definitions — 'design'",
        "excerpt": (
            "(d) “design” means only the features of shape, configuration, "
            "pattern, ornament or composition of lines or colours applied to any "
            "article whether in two dimensional or three dimensional or in both "
            "forms, by any industrial process or means, whether manual, mechanical "
            "or chemical, separate or combined, which in the finished article "
            "appeal to and are judged solely by the eye; but does not include any "
            "mode or principle of construction or anything which is in substance "
            "a mere mechanical device"
        ),
        "url": (
            "https://ipindia.gov.in/storage/uploads/docs-operator/"
            "b86a073f-f3f5-4484-b98c-1ca21cd846a3.pdf"
        ),
        "effective_date": "Act 16 of 2000 (Gazette of India Extraordinary, 12 May 2000)",
        "tags": [
            "designs", "design", "definition", "packaging", "bottle", "shape",
            "label", "ornament", "article", "eye appeal",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 19 pages)",
            "notes": (
                "Verbatim from the official IP India Gazette PDF of the Designs "
                "Act, 2000, except that the source print/extract shows the "
                "clause marker as 'd)' (the opening parenthesis is a "
                "typesetting artefact of the PDF text layer) and the excerpt "
                "restores it as '(d)'. Excerpt ends before the definition's "
                "further exclusion (trade mark clause reference) — omitted, "
                "not silently truncated into another sentence. Supports the "
                "Research.md note that designs protect packaging/bottle "
                "shapes/labels."
            ),
        },
    },
    # ------------------------------------------------------------------
    # Copyright
    # ------------------------------------------------------------------
    {
        "id": "copyright_act_1957_s22",
        "source_name": "The Copyright Act, 1957 (Act 14 of 1957) — text, IP India",
        "source_type": "statute",
        "issuer": "Government of India; hosted by IP India (Office of CGPDTM)",
        "jurisdiction": "India",
        "scope_area": "copyright",
        "section": "Section 22",
        "section_title": "Term of copyright in published literary, dramatic, musical and artistic works",
        "excerpt": (
            "22. Term of copyright in published literary, dramatic, musical and "
            "artistic works. — Except as otherwise hereinafter provided, copyright "
            "shall subsist in any literary, dramatic, musical or artistic work "
            "[***] published within the lifetime of the author until [sixty years] "
            "from the beginning of the calendar year next following the year in "
            "which the author dies."
        ),
        "url": (
            "https://ipindia.gov.in/storage/uploads/docs-operator/"
            "910cd3b9-98b0-4713-bbd8-db4d02f95d1c.pdf"
        ),
        "effective_date": "Act 14 of 1957 (as amended consolidation hosted by IP India)",
        "tags": [
            "copyright", "term", "sixty years", "public domain", "literary work",
            "classical texts", "translations", "commentaries",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 57 pages)",
            "notes": (
                "Verbatim from the official IP India PDF of the Copyright Act, "
                "1957. '[***]' and '[sixty years]' are amendment annotations "
                "printed in the source and preserved as-is. Supports the "
                "Research.md position: classical Ayurveda texts (authors dead "
                "60+ years ago) are out of copyright, while modern "
                "translations/commentaries attract their own fresh term."
            ),
        },
    },
    # ------------------------------------------------------------------
    # Drugs & Cosmetics
    # ------------------------------------------------------------------
    {
        "id": "dc_act_1940_s3a",
        "source_name": (
            "The Drugs and Cosmetics Act, 1940 (Act 23 of 1940) — consolidated "
            "text with the Drugs Rules 1945, CDSCO"
        ),
        "source_type": "statute",
        "issuer": "Government of India; hosted by CDSCO (Central Drugs Standard Control Organisation)",
        "jurisdiction": "India",
        "scope_area": "drugs_cosmetics",
        "section": "Section 3(a)",
        "section_title": "Definitions — 'Ayurvedic, Siddha or Unani drug'",
        "excerpt": (
            "(a) “Ayurvedic, Siddha or Unani drug” includes all medicines intended "
            "for internal or external use for or in the diagnosis, treatment, "
            "mitigation or prevention of [disease or disorder in human beings or "
            "animals, and manufactured] exclusively in accordance with the "
            "formulae described in, the authoritative books of [Ayurvedic, Siddha "
            "and Unani Tibb systems of medicine], specified in the First Schedule;"
        ),
        "url": (
            "https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/"
            "acts_rules/2016DrugsandCosmeticsAct1940Rules1945.pdf"
        ),
        "effective_date": (
            "Act 23 of 1940; CDSCO consolidated PDF (Act + Rules as amended up to "
            "31 December 2016; file dated 22 November 2022 on cdsco.gov.in)"
        ),
        "tags": [
            "drugs and cosmetics", "ayurvedic drug", "definition", "authoritative books",
            "first schedule", "asu", "classical", "formulation", "manufacture",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 8.6 MB)",
            "notes": (
                "Verbatim from the official CDSCO consolidated PDF. Square "
                "brackets are amendment annotations printed in the consolidation "
                "and preserved as-is. This is the drug-law anchor tying ASU "
                "drugs to the First Schedule authoritative books — the same "
                "distinction M2's classifier uses for 'Classical'."
            ),
        },
    },
    # ------------------------------------------------------------------
    # Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954
    # ------------------------------------------------------------------
    {
        "id": "dmr_act_1954_s3",
        "source_name": (
            "The Drugs and Magic Remedies (Objectionable Advertisements) Act, "
            "1954 (Act 21 of 1954) — India Code"
        ),
        "source_type": "statute",
        "issuer": "Government of India; canonical text at India Code (Ministry of Law and Justice)",
        "jurisdiction": "India",
        "scope_area": "drugs_magic_remedies",
        "section": "Section 3",
        "section_title": (
            "Prohibition of advertisement of certain drugs for treatment of "
            "certain diseases and disorders"
        ),
        "excerpt": (
            "3. Prohibition of advertisement of certain drugs for treatment of "
            "certain diseases and disorders.— Subject to the provisions of this "
            "Act, no person shall take any part in the publication of any "
            "advertisement referring to any drug in terms which suggest or are "
            "calculated to lead to the use of that drug for— (a) the procurement "
            "of miscarriage in women or prevention of conception in women; or (b) "
            "the maintenance or improvement of the capacity of human beings for "
            "sexual pleasure; or (c) the correction of menstrual disorder in "
            "women; or (d) the diagnosis, cure, mitigation, treatment or "
            "prevention of any disease, disorder or condition specified in the "
            "Schedule..."
        ),
        "url": "https://indiacode.gov.in/handle/123456789/1412",
        "effective_date": "Act 21 of 1954",
        "tags": [
            "advertising", "advertisement", "objectionable", "magic remedies",
            "dmr act", "claims", "schedule diseases", "diabetes", "cancer",
            "cure claim", "misleading",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "mirror-verified",
            "url_status": (
                "HTTP 200 on the India Code handle page; body is bot-walled to "
                "scripted clients, so section text was verified against the "
                "Indian Kanoon mirror of the Act (indiankanoon.org/doc/1929849)"
            ),
            "notes": (
                "Verbatim per the mirror. Ellipsis: the section continues with "
                "the proviso governing rule-making (conditions added under "
                "Section 3(d) require DTAB consultation). The Schedule lists the "
                "covered diseases/disorders (e.g. diabetes, cancer, epilepsy, "
                "sexual impotence, venereal diseases) — read from the same "
                "mirror; the Schedule is a separate part of the Act, not quoted "
                "here. The Research.md claim about prohibited claims (diabetes, "
                "cancer etc.) maps to this section plus the Schedule."
            ),
        },
    },
    {
        "id": "dmr_act_1954_s2c",
        "source_name": (
            "The Drugs and Magic Remedies (Objectionable Advertisements) Act, "
            "1954 (Act 21 of 1954) — India Code"
        ),
        "source_type": "statute",
        "issuer": "Government of India; canonical text at India Code (Ministry of Law and Justice)",
        "jurisdiction": "India",
        "scope_area": "drugs_magic_remedies",
        "section": "Section 2(c)",
        "section_title": "Definitions — 'magic remedy'",
        "excerpt": (
            "(c) “magic remedy” includes a talisman, mantra, kavacha, and any "
            "other charm of any kind which is alleged to possess miraculous "
            "powers for or in the diagnosis, cure, mitigation, treatment or "
            "prevention of any disease in human beings or animals or for "
            "affecting or influencing in any way the structure or any organic "
            "function of the body of human beings or animals;"
        ),
        "url": "https://indiacode.gov.in/handle/123456789/1412",
        "effective_date": "Act 21 of 1954",
        "tags": [
            "advertising", "magic remedy", "definition", "talisman", "mantra",
            "dmr act", "claims",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "mirror-verified",
            "url_status": (
                "HTTP 200 on the India Code handle page (bot-walled body); text "
                "verified against Indian Kanoon (indiankanoon.org/doc/1929849)"
            ),
            "notes": "Verbatim per the mirror.",
        },
    },
    # ------------------------------------------------------------------
    # PPV&FR
    # ------------------------------------------------------------------
    {
        "id": "ppvfr_act_2001_s39_1iv",
        "source_name": (
            "The Protection of Plant Varieties and Farmers' Rights Act, 2001 "
            "(Act 53 of 2001) — WIPO Lex text (amended up to Act 33 of 2021)"
        ),
        "source_type": "statute",
        "issuer": (
            "Government of India; text mirrored by WIPO Lex; nodal authority is "
            "the PPV&FR Authority (plantauthority.gov.in)"
        ),
        "jurisdiction": "India",
        "scope_area": "ppv_fr",
        "section": "Section 39(1)(iv)",
        "section_title": "Farmers' rights — entitlement to save, use, sow, resow, exchange, share or sell",
        "excerpt": (
            "(iv) a farmer shall be deemed to be entitled to save, use, sow, "
            "resow, exchange, share or sell his farm produce including seed of a "
            "variety protected under this Act in the same manner as he was "
            "entitled before the coming into force of this Act: Provided that the "
            "farmer shall not be entitled to sell branded seed of a variety "
            "protected under this Act."
        ),
        "url": "https://www.wipo.int/wipolex/en/text/339105",
        "effective_date": "Act 53 of 2001 (text reflects amendments up to Act 33 of 2021)",
        "tags": [
            "plant varieties", "farmers rights", "ppv fr", "seed", "farm produce",
            "branded seed", "medicinal plants",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "mirror-verified",
            "url_status": (
                "HTTP 200 on WIPO Lex; section text additionally verified against "
                "Indian Kanoon (indiankanoon.org/doc/1385928, 'Section 39 in The "
                "Protection Of Plant Varieties And Farmers' Rights Act, 2001')"
            ),
            "notes": (
                "Verbatim per the two mirrors (mutually consistent). India Code "
                "hosts the Act under the Ministry of Agriculture collection "
                "(handle 123456789/1362) but did not expose a stable item URL in "
                "automated checks; WIPO Lex is the verified full-text host. "
                "Research.md flags that PPV&FRA x Ayurveda medicinal plants "
                "registrations are under-documented — abstention-friendly. "
                "Phase 3 correction: the former 'variety registration' tag was "
                "removed — this record covers farmers' rights (Section 39), "
                "not a variety-registration procedure, and the tag overstated "
                "its retrieval coverage."
            ),
        },
    },
    # ------------------------------------------------------------------
    # Biological Diversity Act — only the IP intersection (deep ABS = M4)
    # ------------------------------------------------------------------
    {
        "id": "bda_2002_s6",
        "source_name": (
            "The Biological Diversity Act, 2002 — Section 6 as substituted by "
            "the Biological Diversity (Amendment) Act, 2023 (No. 10 of 2023) — "
            "Gazette of India Extraordinary"
        ),
        "source_type": "statute",
        "issuer": (
            "Government of India; amendment text from the Official Gazette "
            "(egazette.gov.in); canonical consolidated Act at India Code "
            "(handle 123456789/12562); implementing authority is the NBA "
            "(nbaindia.org)"
        ),
        "jurisdiction": "India",
        "scope_area": "biological_diversity",
        "section": "Section 6(1) and 6(1A)",
        "section_title": (
            "IPR applications for inventions based on biological resources "
            "accessed from India / associated traditional knowledge — NBA "
            "approval (Section 3(2) persons) and registration (Section 7 "
            "persons) before grant"
        ),
        "excerpt": (
            "(1) Any person or entity covered under sub-section (2) of section 3 "
            "applying for an intellectual property right, by whatever name "
            "called, in or outside India, for any invention based on any research "
            "or information on a biological resource which is accessed from "
            "India, including those deposited in repositories outside India, or "
            "traditional knowledge associated thereto, shall obtain prior "
            "approval of the National Biodiversity Authority before grant of "
            "such intellectual property rights. (1A) Any person covered under "
            "section 7 applying for any intellectual property right, by whatever "
            "name called, in or outside India, for any invention based on any "
            "research or information on a biological resource which is accessed "
            "from India, including those deposited in repositories outside "
            "India, or traditional knowledge associated thereto, shall register "
            "with the National Biodiversity Authority before grant of such "
            "intellectual property rights."
        ),
        "url": "https://egazette.gov.in/WritereadData/2023/247815.pdf",
        "effective_date": (
            "Section 6 as substituted by the Biological Diversity (Amendment) "
            "Act, 2023 (No. 10 of 2023, assent 3 August 2023); in force from "
            "1 April 2024 (per the commencement notification recorded in "
            "Research.md)"
        ),
        "tags": [
            "biodiversity", "biological diversity act", "nba", "intellectual property",
            "biological resource", "patent", "ipr", "approvals", "register",
            "grant", "traditional knowledge", "section 6",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 217,544 bytes)",
            "notes": (
                "RE-VERIFIED 2026-09-06 against the amended framework as "
                "required by the Phase 1 note: the earlier mirror-verified "
                "wording was PRE-2023-AMENDMENT ('previous approval ... before "
                "making such application') and is superseded. The excerpt is "
                "the substituted Section 6(1) and new 6(1A), extracted verbatim "
                "(whitespace normalised) from the Official Gazette PDF of the "
                "Biological Diversity (Amendment) Act, 2023. Amended regime: "
                "Section 3(2) persons (non-residents/foreign) need prior NBA "
                "approval before GRANT of the IPR; Section 7 persons (Indian) "
                "must register with the NBA before grant. New Section 6(1B) "
                "(not quoted; keeps the excerpt within the length cap) adds "
                "prior NBA approval at the time of commercialisation for "
                "Section 7 persons — the official Gazette print of 6(1B) "
                "contains the typo 'National Biodivesity Authority', preserved "
                "here as a print observation, not quoted. Included only because "
                "India-IP questions (patents on herbal formulations) intersect "
                "Section 6; deep ABS/Nagoya treatment belongs to Member 4."
            ),
        },
    },
    # ------------------------------------------------------------------
    # FSSAI — Ayurveda Aahara
    # ------------------------------------------------------------------
    {
        "id": "fss_aahara_regs_2022_reg2b",
        "source_name": (
            "Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 — "
            "Gazette of India, Part III—Section 4 (FSSAI)"
        ),
        "source_type": "regulation",
        "issuer": "Food Safety and Standards Authority of India (FSSAI), Ministry of Health and Family Welfare",
        "jurisdiction": "India",
        "scope_area": "fssai_ayurveda_aahara",
        "section": "Regulation 2(b)",
        "section_title": "Definitions — 'Ayurveda Aahara' (with food/drug exclusions)",
        "excerpt": (
            "(b) “Ayurveda Aahara” means a food prepared in accordance with the "
            "recipes or ingredients or processes as per method described in the "
            "authoritative books of Ayurveda listed under ‘Schedule A’ of these "
            "regulations including products which have other botanical "
            "ingredients in accordance with the concept of Ayurveda Aahara but "
            "does not include Ayurvedic drugs or proprietary Ayurvedic medicines "
            "and medicinal products, cosmetics, narcotic or psychotropic "
            "substances, herbs listed under Schedule E-1 of Drug and Cosmetics "
            "Act, 1940 and the Drug and Cosmetics Rules, 1945, metals based "
            "Ayurvedic drugs or medicines, bhasma or pishti and any other "
            "ingredients notified by the Authority from time to time."
        ),
        "url": (
            "https://foodsafetystandard.in/wp-content/uploads/2025/09/"
            "Gazette_Notification_Ayurveda_Aahara_09_05_2022.pdf"
        ),
        "effective_date": "Notified in the Gazette of India, 5 May 2022 (Part III—Section 4)",
        "tags": [
            "fssai", "ayurveda aahar", "ayurveda aahara", "food", "nutraceutical",
            "schedule a", "bhasma", "pishti", "schedule e-1", "exclusions",
            "food vs drug", "licence",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": (
                "HTTP 200 (application/pdf, 27 pages) — the exact Gazette scan; "
                "see notes on hosting"
            ),
            "notes": (
                "Verbatim from the Gazette notification scan (Gazette "
                "registration DL-33004/99, Part III—Section 4, dated 5 May 2022; "
                "spacing artefacts in the scan normalised). HOSTING NOTE: FSSAI's "
                "previous official path for this PDF "
                "(fssai.gov.in/upload/uploadfiles/files/"
                "Gazette_Notification_Ayurveda_Aahara_09_05_2022.pdf) now serves "
                "the FSSAI site shell after the site redesign, and no "
                "replacement official URL could be located by automated checks; "
                "the recorded URL is a verified copy of the official Gazette "
                "scan. Content is cross-corroborated by the live official FSSAI "
                "Order of 25-07-2025 (record fssai_order_2025_cat_a), which "
                "operates these Regulations. Swap in an official URL if/when "
                "FSSAI re-hosts the notification."
            ),
        },
    },
    {
        "id": "fssai_order_2025_cat_a",
        "source_name": (
            "FSSAI Order dated 25 July 2025 — 'Ayurveda Aahara covered under "
            "Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 – reg'"
        ),
        "source_type": "registry_notice",
        "issuer": "Food Safety and Standards Authority of India (FSSAI), Science and Standards Division",
        "jurisdiction": "India",
        "scope_area": "fssai_ayurveda_aahara",
        "section": "Order text; Schedule B Note (1) of the FSS (Ayurveda Aahara) Regulations, 2022",
        "section_title": "Category-A list of Ayurveda Aahara products (with Ministry of Ayush consultation)",
        "excerpt": (
            "Subject: Ayurveda Aahara covered under Food Safety and Standards "
            "( Ayurveda Aahara ) Regulations, 2022 – reg. ... This is in "
            "reference to the Note (1) under Schedule B of the Food Safety and "
            "Standards ( Ayurveda Aahara ) Regulations, 2022 which specifies "
            "that the Food Authority may provide a list of Ayurveda Aahara "
            "covered under category A from time to time. 2. In this regard, in "
            "consultation with Ministry..."
        ),
        "url": (
            "https://fssai.gov.in/upload/uploadfiles/files/"
            "Order%20dated%2025-07-2025%20enclosing%20Ayurveda%20Aahara.pdf"
        ),
        "effective_date": "25 July 2025 (order date, per the document)",
        "tags": [
            "fssai", "ayurveda aahara", "category a", "pre-approved recipes",
            "schedule b", "foscos", "central licence", "ministry of ayush",
        ],
        "verification": {
            "checked_on": "2026-09-06",
            "method": "downloaded+extracted",
            "url_status": "HTTP 200 (application/pdf, 172 pages, live on fssai.gov.in)",
            "notes": (
                "Verbatim (bilingual Hindi/English order; English portion "
                "quoted; internal spacing normalised). The order encloses the "
                "list of Ayurveda Aahara products falling under Category A "
                "(Research.md: 91 pre-approved recipes, FoSCoS Kind-of-Business "
                "live 1 September 2025). Ellipsis: order continues with the "
                "consultation statement and enclosures."
            ),
        },
    },
)

# Public list (mutable copy semantics avoided: expose a tuple-building function)
def all_sources():
    """Return fresh copies of all source records (mutating a copy must not
    corrupt the corpus)."""
    import copy
    return copy.deepcopy(list(_CORPUS_TUPLE))


# ---------------------------------------------------------------------------
# Validation (Phase 1 tests + reusable by Phase 2/M6)
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = (
    "id", "source_name", "source_type", "issuer", "jurisdiction",
    "scope_area", "section", "section_title", "excerpt", "url",
    "effective_date", "tags", "verification",
)


def validate_source_record(record):
    """Check one source record for complete, well-formed metadata.

    Returns a list of problems (empty list = valid).
    """
    problems = []
    if not isinstance(record, dict):
        return ["record must be a dict, got %s" % type(record).__name__]

    for field in _REQUIRED_FIELDS:
        if field not in record:
            problems.append("missing required field: %s" % field)
    if problems:
        return problems

    if not re.fullmatch(r"[a-z0-9_]+", record["id"] or ""):
        problems.append("id must be snake_case: %r" % record["id"])
    for field in ("source_name", "section", "section_title", "excerpt",
                  "url", "effective_date"):
        if not isinstance(record[field], str) or not record[field].strip():
            problems.append("%s must be a non-empty string" % field)
    if record["source_type"] not in SOURCE_TYPES:
        problems.append(
            "source_type %r must be one of %s"
            % (record["source_type"], list(SOURCE_TYPES))
        )
    if record["scope_area"] not in SCOPE_AREAS:
        problems.append(
            "scope_area %r must be one of %s"
            % (record["scope_area"], list(SCOPE_AREAS))
        )
    if record["jurisdiction"] != JURISDICTION:
        problems.append(
            "jurisdiction must be exactly %r for every record (got %r)"
            % (JURISDICTION, record["jurisdiction"])
        )
    if not isinstance(record["tags"], list) or not all(
        isinstance(t, str) and t.strip() for t in record["tags"]
    ):
        problems.append("tags must be a list of non-empty strings")
    elif len(record["tags"]) < 3:
        problems.append("tags should have at least 3 keywords for retrieval")

    if not record["url"].startswith("https://"):
        problems.append("url must be https")

    excerpt_len = len(record["excerpt"])
    if not 60 <= excerpt_len <= 1200:
        problems.append(
            "excerpt should be a short quote (60-1200 chars), got %d" % excerpt_len
        )

    verification = record["verification"]
    if not isinstance(verification, dict):
        problems.append("verification must be a dict")
    else:
        for field in ("checked_on", "method", "url_status"):
            if not isinstance(verification.get(field), str) or not verification[field].strip():
                problems.append("verification.%s must be a non-empty string" % field)
        if verification.get("method") not in ("downloaded+extracted", "mirror-verified"):
            problems.append(
                "verification.method must be 'downloaded+extracted' or "
                "'mirror-verified' (got %r)" % verification.get("method")
            )
        if not isinstance(verification.get("notes"), str) or not verification["notes"].strip():
            problems.append("verification.notes must be a non-empty string")

    return problems


def validate_corpus():
    """Validate every record; returns {record_id: [problems]} for all records
    (empty dict = all valid), plus duplicate-id detection."""
    problems_by_id = {}
    seen_ids = set()
    for record in _CORPUS_TUPLE:
        problems = validate_source_record(record)
        if record["id"] in seen_ids:
            problems.append("duplicate record id")
        seen_ids.add(record["id"])
        if problems:
            problems_by_id[record["id"]] = problems
    return problems_by_id


# ---------------------------------------------------------------------------
# Minimal retrieval seam (Phase 1 placeholder)
#
# Deliberately simple: keyword/tag matching only, deterministic, no vectors,
# no rerankers. Phase 2 (India Guidance) will replace or extend this; it
# exists now so the corpus is testably consumable and the out-of-corpus
# abstention behaviour is demonstrable.
# ---------------------------------------------------------------------------

# Stopwords excluded from retrieval matching (generic function words must
# not surface records on their own).
_STOPWORDS = {
    "the", "and", "for", "with", "under", "from", "that", "this", "any",
    "are", "was", "has", "its", "his", "her", "can", "how", "what", "when",
    "not", "per", "via", "all", "new", "act", "law",
}


def find_sources(query, sources=None, min_score=2):
    """Return matching records for a free-text query, best-first.

    A record scores 1 for each query keyword (len >= 3, not a stopword) that
    appears (case-insensitive, substring) in its tags, section,
    section_title or source_name. Records with score below ``min_score`` are
    dropped. The default of 2 is deliberate: a single weak keyword hit must
    NOT surface a record — Phase 2 should treat weak matches as insufficient
    evidence and abstain. Returns a list of (record, score) sorted by
    descending score, then by record id for determinism.
    """
    if sources is None:
        sources = all_sources()
    keywords = [
        w for w in re.findall(r"[a-z0-9()]+", query.lower())
        if len(w) >= 3 and w not in _STOPWORDS
    ]
    scored = []
    for record in sources:
        haystack = " ".join(
            record.get("tags", [])
            + [record.get("section", ""), record.get("section_title", ""),
               record.get("source_name", "")]
        ).lower()
        score = sum(1 for kw in keywords if kw in haystack)
        if score >= min_score:
            scored.append((record, score))
    scored.sort(key=lambda pair: (-pair[1], pair[0]["id"]))
    return scored


# ---------------------------------------------------------------------------
# Intentionally out-of-corpus topics (for abstention checks in Phase 2+)
# ---------------------------------------------------------------------------

OUT_OF_CORPUS_TOPICS = (
    # International IP is Member 5's domain — deliberately absent here.
    "Madrid Protocol international trademark filing",
    "PCT national phase entry",
    # Deep ABS/Nagoya/TKDL is Member 4's domain — deliberately absent here.
    "Nagoya Protocol PIC MAT mutually agreed terms",
    "TKDL access under NDA subscription",
)
