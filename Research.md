IP-SAKTI Sahayak
Consolidated Research Dossier — Ayurveda IP & Regulatory Guidance AI Assistant
Smart India Hackathon — Problem Statement SIH-26045
Ministry of Ayush | All India Institute of Ayurveda

This dossier consolidates and deduplicates two independently compiled research passes on the IP-SAKTI Sahayak problem statement — one produced using Kimi ("Source K", Research_for_PS_26041.docx) and one using Perplexity ("Source P", Research_for_PS_26045.docx), both dated 26 August 2026. Where the two sources agree, this document states the fact once. Where they diverge — on figures, dates, case citations, or scope — both versions are preserved and flagged as a Reconciliation note so nothing is silently discarded. Content unique to one source is retained and attributed.
Both source dossiers were themselves compiled against the brief in Problem_Statement_I1.docx (IP-SAKTI Sahayak: a multilingual, RAG-based, source-cited AI assistant for IP and regulatory guidance in Ayurveda across national and international regimes).
 
Executive Summary
The Ayurveda/AYUSH sector is large and fast-growing, but IP protection, Access-and-Benefit-Sharing (ABS) compliance, and drug/food/cosmetic regulatory classification remain fragmented across many statutes, portals, and international regimes. No comprehensive AI tool currently exists to guide practitioners, researchers, and MSMEs through this landscape. Both research passes converge on the same core diagnosis and MVP direction; they differ mainly in the specific market-size figures cited and in which secondary case law and export-market details they surfaced.
●	No comprehensive AI tool exists that integrates Patents Act Section 3(p), TKDL, Biological Diversity Act/ABS, Drugs and Cosmetics Act classification, FSSAI Ayurveda-Aahar rules, and international regimes (TRIPS, CBD/Nagoya, WIPO GRATK, PCT, Madrid, Hague) into one citation-grounded, multilingual assistant.
●	Key recent developments both sources flag: the February 2025 Draft AYUSH Patent Guidelines / September 2025 CGPDTM AYUSH guidelines; the Biological Diversity (Amendment) Act, 2023 (in force 1 April 2024) with 2024 Rules and 2025 ABS Regulations; the WIPO Treaty on Genetic Resources and Associated Traditional Knowledge (GRATK), adopted 24 May 2024 and still short of the 15 ratifications needed for entry into force; FSSAI's "Ayurveda Aahara" Kind of Business live on FoSCoS since 1 September 2025; and continuing judicial refinement of Section 3(p) (Zero Brand Zone, 2024; Shaafi Naturcure, 2026).
●	The corpus for a RAG system can be built largely from open, authoritative sources (India Code, IP India, NBA, CDSCO, FSSAI, WIPO Lex) plus a paid-per-call case-law API (Indian Kanoon). TKDL full text is not available for public RAG ingestion — access is restricted to patent offices under NDA — so the assistant can point to TKDL rather than quote it directly.
●	Recommended MVP: a formulation classifier, an India-vs-international jurisdiction toggle, IP-type routing, an ABS compliance helper with a TKDL/prior-art pointer, mandatory source citations with a confidence indicator, a human-escalation path, Hindi+English multilingual delivery via Bhashini (expanding to more Indic languages later), and a persistent "information, not legal advice" disclaimer aligned with DPDP Act and MeitY AI-advisory expectations.
Reconciliation note: Headline market-size figures differ by source and are not directly comparable — see Section A.1. Treat all figures as sourced estimates, not verified government statistics, and cite the underlying source when using them in pitch materials.
Section A — Domain & Stakeholder Landscape
A.1 Ayurveda Ecosystem Mapping
Market size and growth
●	Source K: Indian Ayurveda market ≈ INR 57,450 crore (≈ USD 7 billion) in FY23, projected to reach INR 1.2 lakh crore (≈ USD 16.3 billion) by FY28 at ~15% CAGR (product segment 16% CAGR, services 12.4% CAGR). IMARC separately estimates the Ayurvedic products market at INR 875.9 billion in 2024, growing at 16.17% CAGR (2025–2033). Ayurveda is 71.10% of the India AYUSH/Alternative Medicine market in 2025.
●	Source P: AYUSH market (2023–2024) ≈ USD 43.4 billion (domestic ≈ USD 41 billion; exports ≈ USD 2–3 billion). Ayurveda's 71.10% share of AYUSH implies ≈ USD 24.87 billion (2025 estimate — the 71.10% figure itself matches Source K). Projected AYUSH growth: 17% CAGR (2024–2032) targeting USD 200 billion by 2029–2030; Ayurveda products specifically projected at 15.5–20% CAGR (2025–2034) reaching INR 3,728 billion (≈ USD 45 billion) by 2034. Ayurveda exports: USD 688.89 million in FY 2024–25 (6.11% YoY growth).
Reconciliation note: The two sources' base-year market-size figures differ by roughly an order of magnitude in places (e.g., ~USD 7bn vs ~USD 43bn for related-but-different scopes: Ayurveda-only vs. all-AYUSH, and different base years/currencies). Both agree closely on Ayurveda's 71.10% share of AYUSH and on the general 15–20% CAGR trajectory. Verify the specific figure against its named source (IBEF/Mordor Intelligence for Source K; IMARC/Grand View/Market.us-style aggregation for Source P) before using in pitch materials, and always state which scope (Ayurveda vs. AYUSH, domestic vs. domestic+export) a figure refers to.
Practitioners, MSMEs, manufacturers
●	MSMEs in the AYUSH sector: 38,216 (August 2021) → 53,023 (January 2023) → 92,653 (August 2025) — both sources agree on this ~144% four-year growth figure.
●	Source K: 500,000 registered Ayurveda practitioners per Mordor Intelligence (2025); other sources cite 780,000+ registered practitioners across all AYUSH systems. 8,648 licensed Ayurvedic manufacturers, 17% industry CAGR, 280 Ayurveda colleges.
●	Source P: Granular AYUSH-registered practitioner counts are not publicly available at year-wise level (flagged as unverifiable). AIIA-ICAINE incubation centre established to support Ayush startups; Ministry of Ayush developing entrepreneurship support programmes.
Major clusters
●	Kerala: Hub for Ayurveda tourism and classical-medicine manufacturing. Source K notes Navara Rice (GI-tagged) cultivated largely in Palakkad; Source P quantifies Kerala Ayurveda/medical-value tourism at INR 13,500 crore (2024), 25% YoY growth.
●	Gujarat, Rajasthan, Madhya Pradesh: Both sources flag these as significant manufacturing/raw-material clusters. Source P adds that Nagauri Ashwagandha (Rajasthan) received a GI tag in 2026.
●	Karnataka: Coorg Green Cardamom (GI-tagged) is a key Ayurvedic ingredient (Source K).
●	Cluster-specific export volumes are not publicly available from either source (see Appendix IV).
Product categories
Category	Regulatory framework	Notes
Classical medicines	Drugs & Cosmetics Act, ASU rules; First-Schedule texts	Major segment; 37.20% of India AYUSH market (2025, Source K)
Proprietary medicines	Drugs & Cosmetics Act	Significant commercial segment; new formulations, known ingredients
Phytopharmaceuticals	D&C Act "new drug" category	Standardized plant fractions with defined active markers; central CDSCO evaluation
Ayurveda-Aahar (nutraceuticals)	FSSAI (Ayurveda Aahara) Regulations 2022 + 2025 KoB	91 pre-approved Category-A recipes; central licence ₹7,500 + GST
Cosmetics / Personal care	D&C Act, Cosmetic Rules	Fastest-growing segment, 10.63% CAGR (Source K); export-oriented (Source P)
New drugs (AYUSH) / phytopharmaceuticals	D&C Act, CDSCO, DCGI	Stringent Phase I–III clinical-trial requirements
Reconciliation note: Neither source could find a government-published revenue split by product category — both flag this as unverifiable (see Appendix IV, item 1/2).
A.2 Stakeholder Pain-Points
Documented case studies of under-protection / misappropriation
Combining both sources' verified case lists (deduplicated):
●	Turmeric Patent (US Patent 5,401,504, 1995): USPTO granted a patent to the University of Mississippi for turmeric's wound-healing properties. CSIR challenged it with 32 prior-art documents, including a 1953 Journal of the Indian Medical Association paper and ancient Sanskrit texts. Revoked in 1997 — India's first successful TK-based USPTO challenge. Source K estimates the legal cost to India at ~USD 2 million.
●	Neem Patent (EPO 436257, 1994): Granted to USDA/W.R. Grace for a neem-based fungicide. Revoked in 2000 following opposition by Indian activists/scientists; upheld on appeal in 2005 — the world's first biopiracy reversal at the EPO, and the case that established TKDL's defensive-publication strategy.
●	Basmati Rice Patent (US Patent 5,663,484, 1997): RiceTec obtained a patent on "Basmati rice lines and grains." Following India's challenge, 15 of 20 claims were withdrawn (January 2002) and "Basmati" was removed from the title; this episode catalysed India's GI Act, 1999 and the subsequent GI registration of Indian Basmati.
●	Yoga patents (Source K only): Over 900 yoga-related patents filed globally, mostly by US entities; India has successfully opposed several through TKDL.
●	Phyllanthus niruri / Bhuiamla (Source P only): Multiple international patent applications on hepatoprotective properties; TKDL citations have been used to block or amend applications at the EPO and USPTO — an ongoing example of defensive protection.
●	Zero Brand Zone v. Controller of Patents & Designs (Madras HC, panchagavya-lamp case): Court upheld rejection of a patent for a lamp made from panchagavya (cow dung, urine, ghee, butter, milk, curd) plus neem/lemon/peepal leaves, holding it fell under Section 3(p) as an aggregation of known properties of traditionally known components.
●	Divya Pharmacy v. Uttarakhand State Biodiversity Board (Uttarakhand HC, 2018, Source K only): Court held Divya Pharmacy (Patanjali group) liable for non-payment of ABS and failure to obtain State Biodiversity Board consent, ordering ~INR 20.4 million. The subsequent 2023 Biodiversity Amendment exempted AYUSH practitioners from ABS payments, creating ongoing legal ambiguity, especially against the conflicting 2024 Himachal Pradesh HC ruling in Hygienic Research Institute v. HP SBB (Indian firms need only "prior intimation" under Section 7, not ABS payment).
●	Shaafi Naturcure LLP v. Assistant Controller of Patents (Delhi HC, Source P only): A 2026 ruling on a patent application for a herbal formulation combining traditional ingredients. Court upheld rejection under Section 3(p), holding that mere optimisation of known ingredients without a genuine technical advance does not qualify — but also clarified that Section 3(p) does not categorically shut out every TK-adjacent invention.
Reconciliation note: The two sources give conflicting citation details for the Zero Brand Zone case: Source K cites Madras HC, 5 July 2024, OA/32/2020/Pt/CHN; Source P cites Madras HC, December 2024, W.P. No. 12345/2023. These may reflect different stages of the same proceeding (e.g., an original order vs. a later writ petition) or a transcription difference between the two research passes — verify the correct citation against Indian Kanoon or the Madras HC website before citing it in any deliverable. Similarly, Source P's count of "5 verifiable case studies" and Source K's "6" reflect different inclusion choices (Source P excludes yoga patents and the Divya Pharmacy ABS matter as not meeting its ground-rule criteria for this list; Source K excludes Phyllanthus niruri and Shaafi Naturcure).
Survey / interview findings
●	Neither source located a large-scale, publicly available survey specifically quantifying IP/regulatory challenges faced by AYUSH startups and MSMEs (flagged as unverifiable by both).
●	Pain points are inferred instead from enforcement data — e.g., 18,812 objectionable advertisements reported by Pharmacovigilance Centres, 2018–December 2021 (Source K) — and from qualitative themes: a fragmented regulatory landscape where clearing D&C Act/AYUSH rules does not itself secure trademark protection and vice versa; stringent "inventive step" requirements and convoluted NBA/ABS processes that can unintentionally suppress proactive innovation; and quality/standardisation concerns including counterfeiting and limited clinical trials (Source P).
Gaps in current legal-aid / consulting services
●	Cost: High cost of patent attorneys and regulatory consultants relative to MSME budgets — Source P quantifies this at roughly ₹15,000–50,000+ per matter for IP counsel and ₹20,000–100,000 per project for regulatory consultants.
●	Specialisation deficit: Most IP law firms lack Ayurveda-specific expertise; general patent attorneys are often unfamiliar with TKDL and Section 3(p) nuances (Source P).
●	Geographic concentration: Quality IP/regulatory counsel is concentrated in metros (Delhi, Mumbai, Bengaluru), with limited access for the Kerala, Gujarat, and Rajasthan clusters (Source P).
●	Fragmentation: No centralised, plain-language tool integrates IP + regulatory + ABS layers; both sources agree this is the core gap.
●	TKDL access: Restricted to patent offices under NDA; a Cabinet-approved paid-subscription model for wider access was approved in 2022, but its operational status remains unclear as of August 2026.
●	Conflicting case law: The Divya Pharmacy vs. Hygienic Research Institute split on domestic ABS obligations remains unresolved by the Supreme Court, creating compliance uncertainty.
●	Language: Most legal resources are English-only; practitioners working in regional languages lack accessible guidance (Source P).
Section B — Legal & Regulatory Framework (National — India)
B.1 Intellectual Property Regimes
B.1.a Patents Act, 1970 + 2024 Patents Rules
●	Governing statute: The Patents Act, 1970, as amended through 1 August 2024. The 2024 Patents Rules were notified 15 March 2024, updating examination procedures, fee structures, and timelines.
●	Section 3(p): Bars "an invention which, in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components."
●	Judicial interpretation: The Madras HC (Zero Brand Zone, 2024) held that Section 3(p) defensively protects TK by excluding inventions that are "in effect" TK, preventing circumvention by concealing traditionally known components — an aggregation of known properties falls under 3(p) even if some individual ingredients were not separately known for that specific use. The Delhi HC (Shaafi Naturcure, 2026 — Source P) added that Section 3(p) does not completely shut out every invention drawing on TK: if the invention cannot fairly be described "in effect" as TK, and it exhibits a genuine unknown property or non-obvious inventive step, it may still be patentable.
●	Patentability of Ayurvedic formulations: Classical formulations documented in First-Schedule authoritative texts (Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya) are not patentable. Modified formulations may qualify if they show a novel combination with synergistic effect, an unexpected technical advance (e.g., a new extraction method improving bioavailability), or a non-obvious inventive step beyond what TK already discloses.
●	Defensive protection scale (Source P): TKDL documents 400,000+ formulations across Ayurveda, Unani, Siddha, Sowa Rigpa, and Yoga, and has helped block, amend, or trigger withdrawal of 370+ patent applications across patent offices worldwide.
●	AYUSH-specific guidelines: Draft "Guidelines for Processing Patent Applications of AYUSH Systems and Related Inventions" issued for stakeholder consultation in February 2025 (complementing the 2012 TK/Biological Material Guidelines); CGPDTM guidelines for AYUSH inventions (23 September 2025 — Source P) mandate a TKDL prior-art search, require Biodiversity Act compliance for biological resources, and apply Section 3 exclusions rigorously.
●	Section 10(4)(d): Requires disclosure of the geographical origin and source of biological material used in an invention.
●	Forms/fees/timelines (Source P): Patent application — Form 1 (₹1,600 individual / ₹4,000 startup / ₹8,000 others); examination request — Form 18, within 48 months of filing; grant timeline 24–48 months (expedited: 12–18 months); adjudicating body is the Office of the Controller General of Patents, Designs & Trade Marks (CGPDTM), with appeals to the Intellectual Property Appellate Board (IPAB).
B.1.b Geographical Indications (GI)
●	Governing statute: Geographical Indications of Goods (Registration and Protection) Act, 1999. GI Registry is administered by the Office of the Controller General of Patents, Designs & Trade Marks. Application: Form GI-1 (₹5,000 per class); registration valid for 10 years, renewable.
●	Verified Ayurveda-related GIs: Navara Rice (Kerala; Shashtikashali in Ayurveda, used in Navarakizhi); Alleppey Green Cardamom and Coorg Green Cardamom (Sukshma-ela/Elaichi); Ganjam Kewda Flower (Odisha; Ketakipushpa); Saffron (J&K; Kumkuma); Lakadong Turmeric; and Nagauri Ashwagandha (Rajasthan, GI tag granted 2026 — Source P). Basmati Rice is GI-registered across multiple states, with ongoing disputes involving Pakistan.
●	Limitation: India's GI Act restricts protection to goods only — Ayurvedic services (massage, dietary regimes) are not covered. A comprehensive list of Ayurveda-specific GIs is not publicly compiled; the GI Registry's Part-A Register would need manual review (Source P).
B.1.c Trade Marks
●	Governing statute: Trade Marks Act, 1999 + Trade Marks Rules, 2017. Application: Form TM-A (₹4,500 per class individual/startup; ₹9,000 others); validity 10 years, indefinitely renewable.
●	Brand names cannot claim therapeutic efficacy without D&C Act/FSSAI approval. Certification marks are available for standards compliance (GMP, an AYUSH Standard Mark). Generic Ayurveda terms (e.g., "Chyawanprash") may face registration challenges as descriptive terms. Kerala Ayurveda Ltd. and Patanjali are cited examples of brands that have leveraged trademark protection for global presence (Source K).
B.1.d Designs
●	Governing statute: Designs Act, 2000 + Designs Rules, 2001. Application: Form 1 (₹1,000 individual; ₹2,000 startup; ₹4,000 others); validity 10 years, extendable by 5. Applies to packaging, bottle shapes, and label designs; no Ayurveda-specific design litigation was located for 2020–2025.
B.1.e Copyright
●	Governing statute: Copyright Act, 1957 + Copyright Rules, 2013. Classical Ayurvedic texts are in the public domain; translations, commentaries, and modern compilations may be copyrighted. Formulations themselves are not copyrightable as functional/recipe content, though accompanying text or diagrams may be. Registration: Form XIV (₹500 per work); term is the author's lifetime plus 60 years. No recent Ayurveda-text copyright case law was located.
B.1.f Plant Variety Protection & Farmers' Rights Act (PPV&FRA), 2001
●	Medicinal plant varieties are eligible for registration if distinct, uniform, and stable, across four categories: new (breeder-developed), extant (already cultivated), farmers' varieties (a distinctively Indian category), and essentially derived varieties. Protection terms: 15 years for crops, 18 years for trees/vines. Farmers retain rights to save, use, sow, re-sow, exchange, share, and sell farm produce (including seed), but cannot sell branded seed of a protected variety. Administering authority: PPV&FR Authority, New Delhi.
●	Neither source located case law or registrations specifically linking PPV&FRA to Ayurveda medicinal plants — this intersection remains under-documented in primary sources.
B.2 Access and Benefit Sharing (ABS)
●	Governing statute: Biological Diversity Act, 2002, as amended in 2023, plus Biological Diversity Rules, 2024 and (per Source P) 2025 ABS Regulations. The Biological Diversity (Amendment) Act, 2023 received presidential assent 3 August 2023 and came into force 1 April 2024; the 2024 Rules took effect 22 December 2024.
●	Key changes: Decriminalisation of offences (monetary penalties replace imprisonment); exemption of codified TK, cultivated medicinal plants, local communities, and registered AYUSH practitioners from prior-intimation requirements, alongside fast-track approvals for AYUSH practitioners/traditional healers; Indian entities need not obtain prior NBA approval before a patent grant but must register with NBA before grant and obtain prior approval at commercialisation; foreign entities require NBA approval before accessing biological resources and before IPR grant; Digital Sequence Information (DSI) is now brought within ABS obligations when used in inventions; and applications now run through an online NBA portal with a revised fee structure.
●	Three-tier structure (Source P): National Biodiversity Authority (NBA) handles national/international and foreign-entity applications; State Biodiversity Boards/UT Biodiversity Councils handle state-level access and benefit-sharing agreements with local communities; Biodiversity Management Committees (BMC) handle local-level documentation. Application portal: absefiling.nbaindia.in; timeline 90–180 days depending on complexity.
●	Benefit-sharing mechanics — two complementary figures from the two sources: Source K reports turnover-based benefit-sharing slabs payable by applicants — ₹5–50 crore turnover → 0.2%; ₹50–250 crore → 0.4%; ₹250 crore+ → 0.6%; higher rates (5–20%) for high-value resources. Source P separately reports how collected benefit-sharing funds are then distributed — 25–40% to repository institutions (where origin is known) and 60–75% to local beneficiaries.
●	Conflicting case law: The 2018 Uttarakhand HC ruling in Divya Pharmacy imposed ABS liability on an Indian company, while the 2024 Himachal Pradesh HC ruling in Hygienic Research Institute v. HP SBB held that Indian firms need only "prior intimation" under Section 7, not ABS payment. This conflict remains unresolved by the Supreme Court.
●	Nagoya Protocol compliance: India ratified the Nagoya Protocol on ABS in 2014, implemented via the Biological Diversity Act. Exporters must obtain Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT), and (per Source P) an Internationally Recognized Certificate of Compliance (IRCC) for due diligence.
●	ABS–patent intersection (Source P): Patent applications using biological resources must declare NBA/SBB compliance; the WIPO GRATK Treaty reinforces this disclosure trend at the international level (see Section C.3).
Reconciliation note: Do not conflate the two benefit-sharing percentages above — one (Source K) is the payment rate applicants owe based on their turnover; the other (Source P) is how the NBA/SBB then splits collected funds between institutions and local communities. Both should be represented in an ABS-compliance helper, but as separate steps.
B.3 Drug & Food Regulatory Framework
B.3.a Drugs and Cosmetics Act, 1940 + Rules
Category	Definition	Regulatory pathway
Classical medicine	Formulations documented in authoritative Ayurveda texts (Schedule A / First Schedule)	State Licensing Authority (SLA); simplified approval; exempt from clinical trials
Proprietary medicine	New/patented formulation with known ingredients, not in classical texts	SLA + CDSCO review; safety studies but not full clinical trials
Phytopharmaceutical	Standardised plant-based fraction with defined active markers	CDSCO central approval as a "new drug"; rigorous clinical trials
New drug (AYUSH)	Novel formulation or new indication	CDSCO + DCGI approval; Phase I–III trials mandatory
●	ASU pathway: State Licensing Authorities issue manufacturing licences for classical/proprietary medicines under CDSCO oversight; Schedule T of the Drug Rules, 1945 specifies GMP for ASU drugs. Rules 161 and 161B mandate labelling disclosure of ingredients, batch numbers, manufacturer details, licence numbers, and shelf life.
●	Neither source located post-2023 D&C Act amendments specifically targeting AYUSH beyond enhanced GMP requirements and stricter adverse-event reporting (Source P).
B.3.b Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954
●	Prohibited claims: Advertising cure or treatment for diseases in the Schedule — cancer, diabetes, heart disease, genetic disorders, blindness, epilepsy, asthma, venereal disease/sexual impotence or sterility — is strictly forbidden, as are pregnancy-related claims (conception, sex determination, miscarriage prevention).
●	Enforcement data (2020–2025, Source K): Karnataka issued 1,409 notices to erring advertisers; Maharashtra detected 73 objectionable advertisements since 2020 with 13 prosecutions; Gujarat recorded 24 (2020), 6 (2021), 4 (2022); Kerala received 19 complaints and has filed 11 cases under the Act since 2013. First conviction carries up to 6 months' imprisonment and/or a fine; subsequent conviction up to 1 year.
●	Source P adds that Supreme Court directives (2023–2024) called for stricter enforcement, but notes that specific post-2020 case citations require SCC Online/Manupatra access not available during this research.
B.3.c FSSAI — Ayurveda-Aahar Regulations
●	Governing framework: Food Safety and Standards (Ayurveda Aahara) Regulations, 2022, plus 2025 notifications. Ayurveda-Aahar is food prepared per recipes, ingredients, or processes in authoritative Ayurveda texts (Schedule A); it explicitly excludes Ayurvedic drugs, cosmetics, narcotic/psychotropic substances, Schedule E-1 herbs, and metal-based products (bhasmas, pishtis).
●	Licensing: "Ayurveda Aahara (Manufacturer)" became a new Kind of Business on the FoSCoS portal effective 1 September 2025, requiring a mandatory Central Licence (₹7,500 + GST annually). Under Food Category 102: 102.1 (Category A) covers 91 pre-approved recipes published by FSSAI Order on 25 July 2025, with streamlined approval; Categories 102.2–102.4 (B/B1/B2) are non-standardised products requiring FSSAI-HQ approval for the product and any claims.
●	Labelling must reference the classical text/Schedule A source, list ingredients and nutritional information, and cannot carry disease-cure claims without FSSAI approval.
●	Food vs. drug boundary: Ayurveda-Aahar covers preventive/wellness claims and traditional recipes without therapeutic assertions; products making treatment/cure claims, using Schedule E-1 herbs, or containing metal-based formulations fall under the D&C Act instead.
B.4 Digital & Data Governance
Digital Personal Data Protection (DPDP) Act, 2023
●	Consent and purpose limitation: Processing of personal data (including health conditions or business details in a user's query) requires clear, purpose-limited consent.
●	Data localisation: Sensitive personal data must be processed in India; other personal data may be processed outside India but requires a policy mandating India-based processing. If model training occurs outside India, data must be brought back for India-based processing (Source K).
●	Audit trail (Source P): Log every AI-influenced decision — input, output, human action (approve/modify/reject), actor identity, and timestamp — retained for 36 months (a figure Source P frames as good practice spanning DPDP, CCPA, and EU AI Act expectations rather than an explicit statutory number; see Appendix IV). Logs should be queryable by actor, decision type, time period, and affected individual.
●	Retention and breach notification: Delete personal data once its purpose is fulfilled (absent a legal hold); notify the Data Protection Board without delay and provide full information within 72 hours of a breach.
MeitY AI Advisory (2024)
●	The original 1 March 2024 advisory mandated explicit government approval before deploying under-testing/unreliable AI models; the revised 15 March 2024 advisory removed that mandatory prior-approval requirement but retained a "consent popup" mechanism informing users of possible output unreliability, labelling/metadata for AI-generated content, and compliance with the IT Act 2000 and IT Rules 2021. The Minister clarified the advisory targets "significant platforms," not startups.
●	Source P frames the same landscape as: government-facing AI tools should align with the emerging IndiaAI governance framework and recognised standards (ISO/IEC 42001 AI Management Systems, NIST AI RMF), with clear disclosure of AI usage and human oversight for high-stakes decisions.
Bhashini Mission — governance/compliance angle
●	Run by the Digital India Bhashini Division (DIBD) under MeitY as part of the National Language Translation Mission. Access requires registration on the ULCA (Universal Language Contribution API) platform; integrators receive a userID and ulcaApiKey and are capped at five API keys, with a two-call inference flow (pipeline config, then compute). Free APIs are offered for non-commercial/government use with discounted commercial licensing and attribution requirements for derived models; all processing happens on Indian servers with no cross-border transfer without explicit consent — a good compliance fit with DPDP.
Section C — International Framework
C.1 TRIPS Agreement (WTO)
●	Article 27.3(b) allows WTO members to exclude plants and animals (other than microorganisms), and essentially biological processes for producing them, from patentability, and to protect plant varieties via a sui generis system. India uses this flexibility to exclude TK via Section 3(p); TRIPS does not itself mandate TK protection, but India's implementation (Section 3(p) plus TKDL defensive publication) is understood to exceed the TRIPS minimum. India has been a WTO member since 1995, with TRIPS-compliant Patents Act amendments in 1999, 2002, and 2005.
C.2 Convention on Biological Diversity (CBD) + Nagoya Protocol
●	India ratified the CBD in 1994 and the Nagoya Protocol on ABS in 2014, implemented domestically via the Biological Diversity Act, 2002 plus its 2023 amendments, 2024 Rules, and 2025 ABS Regulations. NBA/SBB processes align with Nagoya's PIC and MAT requirements; exporters must obtain an Internationally Recognized Certificate of Compliance (IRCC) for due diligence.
C.3 WIPO Treaty on Genetic Resources and Associated Traditional Knowledge (GRATK), 2024
●	Adoption: Adopted by consensus 24 May 2024 at WIPO headquarters, Geneva — the first WIPO treaty with provisions specifically for Indigenous Peoples and local communities.
●	Core obligation: Once in force, patent applicants whose inventions are based on genetic resources and/or associated TK must disclose the country of origin of the genetic resources and/or the Indigenous Peoples or local community that provided the associated TK; if unknown, the source; if neither is known, a declaration to that effect. Patent offices must provide guidance but are not obliged to verify authenticity.
●	Relationship to TKDL: The Treaty does not replace TKDL-style defensive publication — it complements it with a procedural disclosure obligation at the patent-application stage, and is expected to give patent examiners worldwide additional reason to weigh TKDL citations as prior art.
●	Ratification status (as of August 2026): Entry into force requires 15 ratifications, three months after the 15th deposit. Source K counts 45 signatories (as of June 2026) and 3 ratifications/accessions as of April 2026 — Albania (13 March 2026), Malawi (5 December 2024), and Uganda (variously dated 4 December 2024 or 9 July 2025 across sources) — plus Peru, reported ratified by August 2026 per WIPO Lex. Source P counts 3 ratifications as of August 2026 — Malawi (5 December 2024), Uganda (9 July 2025), and Peru (24 July 2026) — and does not list Albania.
●	India's status: India signed the Treaty on 24 May 2024 but had not deposited its instrument of ratification as of 26 August 2026. No implementing bill has been introduced in Parliament; amendments to the Patents Act, 1970 and Patents Rules will likely be needed, with (per Source P) MoEFCC/DPIIT consultation reported ongoing. At the current ratification pace (roughly 3–4 per year), Source K estimates entry into force may not occur until 2028–2029.
Reconciliation note: The two sources disagree on both the ratification count's composition (Source K includes Albania; Source P does not) and Uganda's ratification date (4 December 2024 vs. 9 July 2025 per Source K's own note of source variance, vs. 9 July 2025 per Source P). Given how fast this figure moves and how directly it matters to any "is GRATK in force" answer the assistant would give, treat the current count as approximate and re-verify against the live WIPO GRATK treaty page before using it in the final submission or in the product itself.
C.4 Patent Cooperation Treaty (PCT)
●	India is a PCT member; Indian applicants can file via the Indian Patent Office (RO/IN) or directly with the WIPO International Bureau (RO/IB) via ePCT. A single application covers 150+ PCT member states, with national-phase entry due 30/31 months from the priority date (commonly cited as 31 months), deferred national fees, and an International Search Report to aid prior-art assessment. 57.4% of non-resident patent applications were filed via the PCT route in 2023 (Source P). No Ayurveda-specific PCT guidance exists.
C.5 Madrid System (international trademark registration)
●	India joined the Madrid Protocol in 2013. Ayurveda brands can file a single international application via IP India (MM2 form; fees vary by designated country), designating 130+ member jurisdictions, with centralised renewals/assignments/recordals through WIPO — generally cheaper than filing separate national applications. Registration validity: 10 years, renewable.
C.6 Hague System (international design registration)
●	India acceded to the Geneva Act of the Hague Agreement in 2018. A single application (DM/1 form; fees vary by country) filed via IP India or WIPO can designate 70+ member jurisdictions, protecting Ayurveda packaging designs, bottle shapes, and label layouts. Validity: 5 years, renewable up to 25 years.
C.7 Budapest Treaty (microorganism deposits)
●	India is a party. Fermented Ayurvedic formulations and probiotic preparations may require a microorganism deposit at a recognised International Depositary Authority — in India, the Microbial Type Culture Collection (MTCC), Chandigarh — followed by referencing the resulting deposit certificate in the patent application.
C.8 Export Market Regulations
●	Top verified export markets, FY 2024–25 (Source P): United States (largest single market — dietary supplements, cosmetics), European Union (Germany, UK, France — traditional herbal medicines, nutraceuticals), ASEAN (Malaysia, Thailand, Indonesia — traditional-medicine recognition), and the Middle East (Saudi Arabia, UAE — halal-certified herbal products).
United States
●	Dietary supplements (DSHEA, 1994): No pre-market approval required; New Dietary Ingredient (NDI) notification is mandatory for ingredients not marketed before 1994 — many Ayurvedic herbs (e.g., Ashwagandha, Turmeric) were marketed before that date and so do not require NDI notification. Structure/function claims are allowed but disease-treatment claims are not. GMP compliance under 21 CFR Part 111 is mandatory.
●	Drugs: Therapeutic claims require FDA approval via the OTC monograph or NDA/IND pathway, with clinical trials for new indications and stringent labelling.
●	Cosmetics: Regulated under the FD&C Act; no pre-market approval (except colour additives) but safety substantiation is required, voluntary registration is available via VCRP, and MoCRA (2022) enhanced safety-reporting requirements.
●	FTC advertising rules: All claims require competent, reliable scientific substantiation; deceptive or unsubstantiated health claims are prohibited.
●	Import Alerts and contamination flags (Source K): FDA Import Alert 54-14 (updated 2023/2025) lists multiple Ayurvedic manufacturers for GMP deviations, subjecting products to detention without physical examination — flagged products include Triphala Guggul Powder, Kaishore Guggul Powder, Shwas Herbal Tea, Avipattikar, Sanshamani, and Mansyadi. Ayurvedic products are frequently flagged for lead, mercury, and arsenic contamination, and the FDA has issued multiple related warnings.
European Union
●	Traditional Herbal Medicinal Products Directive (2004/24/EC): Simplified registration for herbal medicines with 30+ years of traditional use (including 15+ years in the EU), via a national competent authority (e.g., MHRA in the UK, BfArM in Germany); requires bibliographic evidence and preclinical safety data plus a qualified person for pharmacovigilance — no clinical trials required.
●	Novel Food Regulation (EU) 2015/2283: Many Ayurvedic ingredients (e.g., Ashwagandha root extract) require Novel Food authorisation if not consumed significantly in the EU before 15 May 1997, via EFSA safety assessment and European Commission approval — Source P estimates a 17–24 month timeline and €50,000–200,000+ in costs. The European Commission maintains a searchable Novel Food Catalogue.
●	Cosmetic Regulation (EC) 1223/2009: Requires a Cosmetic Product Safety Report and pre-market notification via the CPNP portal, with ingredient restrictions under Annex II (prohibited) and Annex III (restricted).
●	Health claims: Only claims authorised under Regulation (EC) No 1924/2006 may appear on packaging — traditional Ayurvedic claims are generally not EU-authorised.
●	Heavy metals: Commission Regulation (EC) No 1881/2006 sets maximum levels for lead, cadmium, mercury, and arsenic; Indian herbal products are among the most frequently flagged at EU borders.
ASEAN
●	Regulations are still in early stages and vary by country, though harmonisation is progressing under the ASEAN Traditional Medicines Harmonization Framework / ASEAN Common Technical Requirements for Traditional Medicines and Health Supplements (ACTTHMS), including harmonised regional GMP standards (Source P).
●	Malaysia: Regulated under the Traditional and Complementary Medicine Act 2016 by NPRA; product registration is mandatory before sale and requires scientific evidence.
●	Thailand: Regulated under the Thai Traditional Medicine Act, B.E. 2542 (1999) by the Thai FDA; requires scientific evidence and GMP-WHO certification.
●	Indonesia: Regulated as "traditional medicines" (Jamu) by BPOM under 35 TMHSC regulations (2020–2024) covering service delivery, GMP compliance, and research standards; requires scientific proof of safety, efficacy, and quality.
●	Philippines (Source K): Regulated as "food supplements" by the FDA; requires scientific proof.
●	No country-specific Ayurveda export-volume data was located by either source.
Middle East
●	The GCC Standardization Organization (GSO) publishes harmonised standards (GSO 2233, GSO 9, GSO 21, GSO 150, GSO 654), with national implementation varying by country (Source K).
●	Saudi Arabia (SFDA): Two pathways for herbal/health products — Class A (safe, meets quality standards, no unacceptable claims) vs. Class B (full evaluation of quality, safety, and efficacy) — submitted in CTD format via eSDR (Modules 1, 3, 5), with Arabic and English labelling mandatory. SFDA registration is the most rigorous in the GCC.
●	UAE (MoHAP/EDE): Federal Decree-Law No. 38 of 2024 established the Emirates Drug Establishment (EDE), effective 2 January 2025. Herbal/traditional medicines follow Ministerial Decree No. 35 of 2014 guidelines, submitted in CTD format via EIRIS, requiring a GMP certificate, CPP/Free Sale Certificate, and Arabic + English labelling. There is a dual pathway: MoHAP for health-function claims/herbal products, and Dubai Municipality/ADAFSA for general food supplements at the federal import level.
Section D — Data Sources & Corpus for RAG
D.1 Authoritative Open Databases
Source	URL	Format / access	Licensing
India Code	indiacode.nic.in	HTML/PDF; no open API or bulk download	Government copyright; fair use for research
IP India — Patents / InPASS	ipindia.gov.in ; iprsearch.ipindia.gov.in/publicsearch	HTML/PDF; weekly updates; no official API (third-party Parse.bot API available, ~₹3/call per Source P)	Public domain for published patents
IP India — Trade Marks	ipindiaservices.gov.in	Web interface, search only	Public domain
IP India — Designs	ipindiaservices.gov.in	Web interface, search only	Public domain
IP India — GI Registry	search.ipindia.gov.in/GIRPublicSearch ; ipindia.gov.in/geographical-indications-track-application	HTML lists; as registered	Public domain
TKDL	tkdl.res.in	Proprietary structured database; no open API — restricted to patent offices under NDA (16 offices per Source K; 18 per Source P). Cabinet approved a paid-subscription model for wider access in 2022; operational status unclear as of Aug 2026	Restricted; NDA required; CSIR ownership
NBA India	nbaindia.org ; nbaindia.nic.in ; absefiling.nbaindia.in (ABS e-filing)	PDF/HTML guidelines; online application portal with status tracker	Public for guidelines
CDSCO / AYUSH portal	cdsco.gov.in	PDF/HTML notifications; no official API	Public domain
FSSAI	fssai.gov.in	PDF/HTML regulations; FoSCoS portal for licensing; no open API	Public domain
WIPO Lex	wipolex.wipo.int	HTML/XML treaties & laws; API available for some datasets	Open access / public domain
WIPO Pearl	wipopearl.wipo.int	Terminology database, search only	Open access
WTO legal texts	wto.org	HTML/PDF, static	Open access / public domain
Reconciliation note: Source K counts 16 patent offices with TKDL NDA access; Source P counts 18 and names them (India, EPO, USPTO, JPO, and the German, Canadian, Australian, UK, Malaysian, Russian, Peruvian, Spanish, Chilean, Philippine offices, among others). Use the higher, named figure with a re-verification flag rather than treating either as final.
D.2 Paid / Restricted Sources
Platform	Coverage	Pricing (publicly stated)	API access
SCC Online	Supreme Court/High Court judgments, statutes, commentaries	₹15,000–50,000/year individual; institutional pricing higher	No public API; bulk licensing negotiable
Manupatra	Case law, statutes, regulations, news	₹20,000–60,000/year individual	No public API
LexisNexis India	Case law, statutes, international materials	₹25,000–70,000/year individual	No public API
Westlaw (India content)	Select Indian case law, international materials	USD 100–300/month	API via Thomson Reuters (enterprise)
Indian Kanoon	Judgments, 25+ structured fields per case	Pay-per-call: search page (10 results) ₹0.50; document metainfo ₹0.02; full HTML ₹0.20; original PDF ₹0.50; ₹500 free trial credit for new accounts	Yes — api.indiankanoon.org
TKDL	Full-text traditional-knowledge formulations	Paid-subscription model approved by Cabinet (2022); pricing not publicly disclosed	Restricted
D.3 Case Law Corpus
Case	Court / forum	Outcome	Citation (as reported)
Turmeric Patent Revocation	USPTO (re-examination)	Revoked 1997; CSIR proved prior art	US 5,401,504; re-exam cert. 1998
Neem Patent Revocation	EPO (Opposition + Appeals)	Revoked 2000; upheld 2005	EPO 436257
Basmati GI/Patent	USPTO	15/20 claims withdrawn Jan 2002; GI tag later granted	US 5,663,484
Zero Brand Zone v. Controller	Madras HC	Section 3(p) upheld; patent rejected	Source K: 5 July 2024, OA/32/2020/Pt/CHN. Source P: Dec 2024, W.P. No. 12345/2023 — see reconciliation note above
Divya Pharmacy v. Uttarakhand SBB	Uttarakhand HC, Dec 2018	Indian companies held liable for ABS; ~₹20.4M ordered	Unreported in SCC at time of research (Source K)
Hygienic Research Inst. v. HP SBB	Himachal Pradesh HC, 2024	Indian firms need only "prior intimation" under Section 7	Unreported in SCC at time of research (Source K)
Shaafi Naturcure LLP v. Assistant Controller of Patents	Delhi HC, 2026	Section 3(p) rejection upheld; "in effect" TK test clarified	W.P.(C) 4567/2025 (Source P)
●	Machine-readable judgments: Indian Kanoon (api.indiankanoon.org) provides structured data — case title, court, publish date, author, citation counts, cited cases, acts cited, and full text — via a paid-per-call API. The government eCourts platform does not offer a public bulk-extraction API as of August 2026. Source P additionally notes an Indian Supreme Court judgments dataset available in parsed JSONL form via Hugging Face, sourced from main.sci.gov.in.
Section E — Technology & Product Landscape
E.1 Existing AI Tools in Legal/IP/Regulatory Space
Indian examples
●	Neither source located a verifiable AYUSH-specific chatbot or government AI assistant for IP/regulatory guidance.
●	Bhashini-powered assistants (Source P): Samadhan Didi (voice-based citizen grievance redressal, Hindi), VANI voice (multilingual government-service voice interface), and UP Police 112's CONVERSE capability for multilingual ASR — all general-purpose, none AYUSH-focused.
●	NyayaBot: A Supreme Court Legal Services Committee legal-aid chatbot offering basic Q&A on legal rights — general-purpose, no AYUSH IP functionality. Udyam Assist: MSME registration support, not IP/regulatory focused.
●	IP India AI tools: No publicly announced AI-powered prior-art search tool from IP India; InPASS itself uses keyword/Boolean search only. PatentAssist.ai offers free AI patent search across IP India, USPTO, and EPO databases (Source K).
Global examples
Tool	Domain / core features	Pricing (public)	Gap for Ayurveda
Harvey AI	Legal research, document Q&A/drafting, redlining, chronology, regulatory compliance	USD 1,200+/seat/year	No India-specific content; no Ayurveda/TK domain knowledge
CoCounsel (Thomson Reuters/Casetext)	Westlaw-grounded research, document drafting, deposition prep	~USD 225/user/month add-on (USD 300–600 total)	US/UK focus; no Indian statutes or AYUSH regulations
Lexis+ AI (Protégé)	Conversational research, drafting, Shepard's citation validation	USD 128–494/user/month	Limited India content; no Ayurveda-specific guidance
PatentPal	Patent-drafting automation, prior-art search	USD 200–500/month	No TKDL integration; no Section 3(p) awareness
Cipher	Patent analytics, competitive intelligence	Enterprise pricing	No Ayurveda/TK classification
Anaqua	IP portfolio management	Enterprise pricing	No India-specific regulatory workflows
LegalBench-RAG	Benchmark only, not a product	N/A	N/A
●	Cross-cutting gaps (Source P): no tool integrates Section 3(p), TKDL citations, D&C Act classification, FSSAI Ayurveda-Aahar rules, and NBA/ABS processes in one place; global tools are English-only versus the 22-language coverage Indian users need; Harvey/CoCounsel ground answers in Westlaw/Lexis rather than India Code or IP India; and pricing (USD 200–1,200+/month) is prohibitive for Indian MSMEs/startups.
E.2 RAG & Knowledge Graph Architecture
●	Citation-grounded retrieval: LegalBench-RAG (2024) emphasises retrieving precise, minimal, highly relevant text segments rather than large chunks, to reduce hallucination and support accurate citation generation. Recommended practice combines hybrid retrieval (dense/vector + sparse/BM25 search) with cross-encoder re-ranking and explicit citation tracking back to the source document, statute section, or case citation.
●	Hallucination baseline: General-purpose LLMs hallucinate in 58–82% of legal queries; customised legal-AI systems still show 17–33% hallucination rates. BM25 (lexical matching) consistently outperforms dense retrievers (E5) on claim recall and context precision for legal text — keyword methods remain competitive. The ClaimRAG-LAW benchmark evaluates precision, recall, faithfulness, and hallucination; the best systems (E5+GPT-4) achieve ~70% precision and ~95% faithfulness on legal datasets.
●	Handling conflicting/overlapping statutes (Source P): apply temporal precedence (later amendments override earlier provisions), the specificity principle (a specific provision, e.g. FSSAI Ayurveda Aahara, overrides a general one, e.g. general FSSAI food regulations), and jurisdiction tagging (India Central vs. State vs. International) to route queries to the right corpus.
●	Knowledge graph construction: Extract entities (formulation, ingredient, statute, section, case, court, form, fee, timeline, jurisdiction) and relationships (AMENDS, OVERRIDES, CITES, INTERPRETS, GOVERNS, REQUIRES, EXCLUDES) using legal ontologies; no pre-built Ayurveda-IP ontology exists. Source P reports a two-stage LLM-assisted approach — ontology engineering from a sample corpus, then closed extraction using the induced ontology — informed by standards such as ELI, DCTERMS, SKOS, PROV, and Web Annotation, with reported performance of ~89.3% entity-extraction accuracy, ~96% relation-extraction precision, and ~95% case-similarity scoring in the research literature it drew on.
●	Evaluation benchmarks for legal RAG: hallucination rate (share of responses with fabricated citations/statutes/fees), citation accuracy (do cited sections actually exist and support the claim), answer faithfulness (do retrieved chunks actually support the generated answer), and jurisdiction accuracy (correctly identifying India vs. US vs. EU law).
E.3 Multilingual & Accessibility Infrastructure
●	Bhashini platform: Offers ASR, NMT, TTS, and combined ASR+NMT+TTS pipelines across 22 scheduled languages, drawing on 350+ deployed language models from multiple providers (IIIT Hyderabad's bhashini/iiith/nmt-all covering 34 languages, AI4Bharat's IndicTrans v2 covering 18 languages, plus IIT Madras, CDAC, and AUKBC models). Access uses a two-call architecture (pipeline config to obtain serviceId/modelId and an inference endpoint, then a compute call to the Dhruva API). End-to-end voice-pipeline latency under 2 seconds is achievable, with Source P specifying this for 14 languages.
●	Readiness tiers (Source P): Tier 1 (production-ready) — Hindi, with mature ASR+TTS and live deployments such as Samadhan Didi and VANI; Tier 2 (beta) — Bengali, Tamil, Telugu, Marathi, Gujarati, with ASR+TTS available; Tier 3 (early access) — the remaining 16 languages, limited to text translation or limited voice support.
●	Alternative/complementary Indic LLMs surfaced by the two sources: Sarvam-1 / Sarvam-2b-v0.5 / Sarvam-M (Sarvam AI; ~2B parameters; custom research licence, commercial licensing available; 10 Indic languages), OpenHathi (7B, Llama 2 Community License, Hindi+English), Airavata and IndicLLM (AI4Bharat, Apache 2.0/open-source, 11 Indic languages, instruction-tuned variants), and IndicTrans2 / IndicASR / IndicTTS (AI4Bharat, open-source machine-translation and ASR/TTS models).
●	Jurisdiction toggle design: Backend — maintain separate vector indices or tagged document collections per jurisdiction (India, USA, EU, ASEAN, Middle East), with each chunk tagged by jurisdiction, regime (patent/drug/food/ABS), and language, and route queries accordingly. UI/UX — a prominent "India" vs. "International" toggle with a secondary region dropdown, flag icons and text labels, contextual hints (e.g., "Showing regulations for exporting to the USA"), and a fallback clarifying question when the jurisdiction is ambiguous. Never conflate Indian statutory requirements with international treaty obligations in the same answer stream.
E.4 Guardrails Against Hallucination
●	Disclaimer pattern: Both sources converge on the same style — a persistent banner stating that the tool provides general information, not legal advice, and that a qualified professional should be consulted for specific matters. Source P proposes a fuller model disclaimer: "IP-SAKTI Sahayak provides general information on intellectual property, regulatory, and ABS requirements for Ayurveda products. This information is based on publicly available sources as of [DATE] and does not constitute legal, regulatory, or professional advice. Regulations change frequently; verify all information with official sources (IP India, CDSCO, FSSAI, NBA) or consult a qualified attorney/regulatory consultant before making decisions. The developers are not liable for any losses arising from reliance on this information." The MeitY Advisory additionally requires a "consent popup" flagging possible AI-output unreliability.
●	Comparable-tool disclaimers (Source P): Harvey AI — "AI-generated content should be verified by qualified legal professionals"; CoCounsel — "Grounded in Westlaw content; verify citations before relying"; Lexis+ AI — "Shepard's citation validation included; still requires attorney review."
●	Retrieval-time controls: retrieve only from authoritative sources (India Code, IP India, FSSAI, NBA), exclude SEO/marketing content from the corpus, and tag every statute/regulation chunk with its amendment date for version control.
●	Generation-time controls: enforce citation of a source URL and section number for every factual claim; use template-based, database-pulled (not generated) responses for forms/fees/timelines; and set a confidence threshold below which the assistant abstains — e.g., "I could not find reliable information on this topic. Please check [official source URL]" — rather than guessing.
●	Post-generation and feedback controls: a citation checker verifying cited sections actually exist; a fee/timeline validator cross-checked against official schedules; human-in-the-loop review for high-stakes queries (patent filing, drug approval); and a user feedback loop ("Was this helpful?" / "Report incorrect information") that logs flagged responses for corpus updates.
Section F — Recent Developments (2023–2026), Time-Stamped
Development	Date	Status as of 26 Aug 2026
Draft AYUSH Patent Guidelines	Feb 2025	Open for stakeholder consultation, not yet finalised
2024 Patents Rules	Notified 15 Mar 2024	In force; reinforced Section 3(p) application; mandates TKDL prior-art search for AYUSH inventions
CGPDTM Guidelines for AYUSH inventions	23 Sep 2025	In force per Source P
Biological Diversity (Amendment) Act, 2023	Assent 3 Aug 2023	In force since 1 Apr 2024
Biological Diversity Rules, 2024 (+ 2025 ABS Regulations per Source P)	Notified 22 Oct 2024	Effective 22 Dec 2024; three-tier NBA/SBB/BMC structure and ABS e-filing portal operational
WIPO GRATK Treaty	Adopted 24 May 2024	3–4 ratifications reported (composition disputed between sources); NOT in force — needs 15
FSSAI Ayurveda-Aahar KoB / Category A recipes	Order 25 Jul 2025; KoB live 1 Sep 2025	Active on FoSCoS portal; 91 pre-approved recipes
Madras HC Section 3(p) ruling (Zero Brand Zone)	2024 (dates disputed between sources)	Binding in Madras HC; persuasive elsewhere
Delhi HC Section 3(p) ruling (Shaafi Naturcure)	2026 (Source P)	Recent jurisprudence refining the "in effect" TK test
PRIP scheme inclusion for AYUSH drugs	2024–2025	~₹4,250 crore available for R&D (Source K)
National Ayush Mission (NAM)	Ongoing	12,500+ Ayushman Arogya Mandirs (AHWCs) operationalised (Source K)
AIIA-ICAINE incubation centre / Ayush entrepreneurship support	2023–2025	Supporting Ayush startups (Source P)
Section G — Competitive Gap Analysis
G.1 Why No Comprehensive Tool Currently Exists
●	Domain fragmentation: Ayurveda IP sits at the intersection of patent law, biodiversity law, drug regulation, food regulation, and international trade law, spanning 6+ regulatory regimes with no single owning department.
●	Data/corpus fragmentation: Authoritative sources are scattered across 10+ government portals (India Code, IP India, NBA, CDSCO, FSSAI, WIPO) with case law dispersed and TKDL restricted — no unified API exists.
●	Multilingual gap: Most legal-tech tools are English-only, while AYUSH practitioners often operate in Hindi, Sanskrit, Tamil, Malayalam, and other regional languages — a gap Bhashini is beginning to close but has not fully closed (per readiness tiers above).
●	Hallucination risk: Legal/regulatory AI needs near-zero hallucination tolerance that general-purpose LLMs cannot yet guarantee (58–82% hallucination rates on unconstrained legal queries).
●	Market perception and liability (Source P): The ~USD 43bn AYUSH market is fragmented across 92,000+ MSMEs and can be perceived as low-margin for legal-tech investment, while legal/regulatory advice carries malpractice-style liability risk that makes startups hesitant to enter without a clear disclaimer framework.
G.2 What Practitioners/Startups Currently Do Instead
●	Consultants and law firms: High cost relative to MSME budgets (₹15,000–50,000+ per IP matter; ₹20,000–100,000 per regulatory project per Source P), and largely inaccessible outside metro clusters.
●	DIY filings: Entrepreneurs navigate IP India, FSSAI, and NBA portals directly, often without understanding Section 3(p) or ABS requirements, leading to rejections, high error rates, and delays.
●	Government helplines: Single-domain support (IP India helpdesk, FSSAI FoSCoS support, NBA ABS e-filing helpdesk) with no integrated cross-regime guidance.
●	Industry associations and Pharmacovigilance Centres: Provide limited IP/regulatory guidance or monitor misleading advertisements reactively, but do not offer proactive, integrated guidance.
G.3 Minimum Viable Product (MVP) Feature Set
Combining both sources' 80/20 prioritisation into a single staged roadmap:
MVP v1.0 — core
●	Formulation classifier: 3–5 clarifying questions to classify as classical / proprietary / new drug / phytopharmaceutical / Ayurveda-Aahar / cosmetic.
●	Jurisdiction toggle: India (default) vs. International, with a secondary region selector (USA/EU/ASEAN/Middle East).
●	Regime detection and IP-pathway routing: classify the query as patent, trademark, GI, design, copyright, drug licensing, FSSAI, or ABS, and route to the applicable sections/forms.
●	ABS compliance checker: a simple questionnaire on biological-resource use that flags NBA/SBB requirements, and a TKDL pointer directing users to the correct access route (patent-office NDA vs. pending paid subscription).
●	Mandatory source citations with a confidence indicator on every answer, plus pre-populated (not generated) forms/fees/timelines templates for common applications.
●	Persistent "information, not legal advice" disclaimer and MeitY-compliant consent popup.
●	Multilingual baseline: Hindi + English via Bhashini's Tier-1 languages.
MVP v2.0 — enhanced
●	Voice interface via Bhashini ASR/TTS for Tier-2 languages (Bengali, Tamil, Telugu, Marathi, Gujarati).
●	Document upload: users submit formulation details and the assistant identifies applicable regulations.
●	Export-market wizard: step-by-step guidance for USA (FDA/DSHEA), EU (THMPD/Novel Food), ASEAN (ACTTHMS), and the Middle East (SFDA/MoHAP).
●	Automated alert system for regulatory updates (new FSSAI notifications, Patents Rules amendments) via email/SMS.
v3.0+ — advanced
●	Relational knowledge-graph visualisation linking formulation → applicable law → required form → timeline, with click-through to source documents; agentic multi-source orchestration for deeper multi-step reasoning.
●	Case-law search integrating the Indian Kanoon API, with curated summaries for Section 3(p), GI, and trademark disputes.
●	Collaboration tools: share responses with attorneys/consultants; export to PDF.
●	Paid-source connectors (SCC Online/Manupatra) and the full multilingual + voice experience, once budget and licensing allow.
G.4 Top 3 Risks and Mitigations
Risk	Likelihood	Impact	Mitigation
Hallucination of statutes/forms/fees	High	Critical (legal liability, credibility loss)	Hybrid RAG + knowledge graph; citation enforcement on every claim; template-based (not generated) forms/fees; post-generation citation validator; human-in-the-loop for low-confidence queries; user "report incorrect information" feedback loop; version-locked corpus
Corpus staleness / regulatory obsolescence	Medium–High	High (wrong advice due to law change; reduced trust)	Automated monitoring of India Code, Gazette, IP India, FSSAI, and NBA for updates; effective-date/version tagging; quarterly corpus audits; "last updated [DATE]" shown on every response
DPDP Act non-compliance / regulatory pushback / licensing risk	Medium	High (regulatory penalties, reputational damage)	Audit-trail logging (input, output, actor, timestamp) with a defined retention policy; explicit consent for personal-data collection; data minimisation; proactive engagement with Ministry of AYUSH, MeitY, and IP India; position the product as an "information facilitator," not a legal advisor
 
Appendix I — Source Index (Deduplicated)
Sources cited by both dossiers are listed once. Sources unique to one dossier are marked (K) for Research_for_PS_26041.docx (Kimi) or (P) for Research_for_PS_26045.docx (Perplexity).
Tier 1 — Primary official sources
●	India Code (indiacode.nic.in) — statutes including the Drugs and Magic Remedies Act, 1954; Patents Act; Biological Diversity Act; D&C Act; FSSAI Act
●	IP India (ipindia.gov.in) — Patents Rules 2024, GI Registry, Trade Marks, Designs; InPASS public search (iprsearch.ipindia.gov.in)
●	TKDL official website (tkdl.res.in)
●	National Biodiversity Authority (nbaindia.org / nbaindia.nic.in) — ABS Regulations 2025, guidelines, application tracker
●	FSSAI (fssai.gov.in) — Ayurveda Aahara Regulations 2022, 2025 notifications, FoSCoS portal
●	CDSCO (cdsco.gov.in) — drug approvals, phytopharmaceutical guidelines (P)
●	WIPO (wipo.int) — GRATK Treaty Resource Center, WIPO Lex, WIPO Pearl, PCT Applicant's Guide
●	WTO (wto.org) — TRIPS Agreement text
●	FDA Import Alert 54-14 (accessdata.fda.gov) (K)
●	PIB (pib.gov.in) — misleading-ads release 22 Mar 2022 (K); AYUSH market/FSSAI/NBA/Bhashini press releases (P)
●	Lok Sabha unstarred question on DMR Act enforcement (sansad.in) (K)
●	Madras High Court judgment, OA/32/2020/Pt/CHN, 5 July 2024 (indiankanoon.org) (K) — cf. citation discrepancy noted in Section A.2/Appendix D.3
●	PM India — Cabinet approval for TKDL access widening, 2022 (K)
●	SFDA, Saudi Arabia (sfda.gov.sa) (P); UAE MoHAP/EDE — Federal Decree-Law No. 38 of 2024 (P)
●	Indian Supreme Court API (main.sci.gov.in) and its Hugging Face judgments dataset (P)
Tier 2 — Reputable secondary sources
●	IBEF AYUSH Industry Report (Feb 2026) (K); Mordor Intelligence — Alternative Medicine in India (Jul 2026) (K, P); Market Research Future — Ayurveda Market (Aug 2026) (K)
●	Lexology — AYUSH Patent Guidelines (Feb 2025) and Biological Diversity Rules 2024 (Nov 2024) (K)
●	Frontline / The Hindu — Biodiversity Amendment analysis (Dec 2023) (K); PMC/NIH — Herbal Drug Regulation (2013) (K); PMC — ASEAN traditional-medicine harmonisation table (P)
●	arXiv — LegalBench-RAG (Aug 2024); ClaimRAG-LAW/fine-grained RAG benchmark for law (Aug 2026); Indic-language LLM capability analysis (Jan 2025); LLM-assisted ontology engineering and contract-graph modelling (P)
●	JSA Law — revised MeitY Advisory (Apr 2024) (K); ELP Law — navigating AI regulation in India (Apr 2024) (K)
●	LiveLaw (biopiracy commentary) (P); Mongabay India (neem-patent analysis) (P); LKS Law and Legal Service India (Section 3(p)/Shaafi Naturcure summaries) (P); NLSIU Law Gratis (Ayurveda copyright/TK, biopiracy) (P)
●	Express Pharma (phytopharmaceuticals) (P); Food Navigator and Samir for India/CliniExperts (FSSAI Ayurveda Aahara) (P); PolicyIndex.ai (TKDL Parliament question) (P); Tensor Analytics/Yuverse/Protecto AI (DPDP compliance) (P)
●	Deemed Consulting (ASEAN harmonisation) (P); Pharma Regulatory and Kayrouz & Associates (UAE herbal registration) (P); PharmaKnowl and V5 Ultimate (SFDA/GCC registration) (P); NITI Aayog — AYUSH strategic roadmap (P)
Tier 3 — Corroborating / industry sources
●	Intepat IP Blog — Trademarks & GI in Ayurveda (Jan 2025) (K); Intepat — PCT filing from India guide (P)
●	NexaCrest (EU Novel Food/THMPD) (K); Netyex (export herbal products to Europe) (K); Medium and CodePrism (Bhashini technical guides/case studies) (K, P); Apify (Indian Kanoon API scraper) (K); Vals.ai (Legal AI report, Feb 2025) (K)
●	File Trademark/IPForte (PPV&FR Act, Ayush compliance) (P); KNALLP (AYUSH patent guidelines) (P); Narahari & Co (IP law advisory) (P); Law Journals/CELNET (IP challenges in herbal medicine) (P)
●	AI Vortex, Toppe Consulting, Attorney AI Tools, AI Made For (legal-AI tool comparisons) (P); Caller Digital, AiSewak, Schemes in India, The AI Tools Box, CodePrism Technologies (Bhashini reviews/pipelines) (P)
●	ShipScout, Ayurovia, Market.us, Mordor Intelligence, OC Academy (Ayurveda market/export data) (P); LinkedIn posts and SlideShare/Scribd (various market/regulatory updates) (P)
●	Legacy IAS, BNB Legal, Drishti IAS (biopiracy/GI explainers for competitive exams) (P); Informatica, Frontiers in AI, OpenReview, Sciety, The Moonlight, Studocu, EA Journals, Scribd, UFRN Repositorio (legal knowledge-graph research literature) (P)
●	Hugging Face and Parse.bot (API/dataset access) (P); PolicyEdge (NBA ABS reforms) (P); Sansad Online (IP India search guide) (P); Cultural IP, EU IP Helpdesk, FIRAT Rwanda, Stanford Law, AIPPI, Oxford GRUR Int., Wiley JWIP/REEL (WIPO GRATK commentary and analysis) (P)
●	Journal UMPR (Indonesia TMHSC reform) (P); The Law Institute and JMSR Online (PPV&FR Act analysis) (P); Chambers Practice Guides (India IP law comparison) (P); CSIR (India–Brazil TKDL access agreement) (P); R Discovery (Bhashini API research) (P)
Reconciliation note: Source P's own index states a total of 86 unique URLs (Tier 1: 12, Tier 2: 13, Tier 3: 61); Source K's index lists 9/13/8 across the same tiers. Combined and deduplicated above, the totals are lower than the raw sum because several sources (Mordor Intelligence, Bhashini technical guides, CodePrism, V5 Ultimate) were independently found by both research passes.
Appendix II — Glossary of Terms
Term	Definition
ABS	Access and Benefit Sharing — framework under CBD/Nagoya Protocol and the Biological Diversity Act for equitable sharing of benefits from genetic resources and associated traditional knowledge
ASR	Automatic Speech Recognition — converts spoken language to written text
ASU	Ayurveda, Siddha, Unani — systems regulated under the Drugs and Cosmetics Act
AYUSH	Ayurveda, Yoga & Naturopathy, Unani, Siddha, Sowa Rigpa, and Homoeopathy
BDA	Biological Diversity Act, 2002 (amended 2023) — regulates access to biological resources and associated traditional knowledge
BMC	Biodiversity Management Committee — local-level body under the Biological Diversity Act
Category A (Ayurveda-Aahar)	Standardised food products from classical Ayurvedic texts; no additional FSSAI approval needed
Classical Medicine	Formulations from First-Schedule texts (Charaka, Sushruta, etc.); exempt from clinical trials
DSI	Digital Sequence Information — covered under the Biodiversity Act's 2023 amendment
FEBS	Fair and Equitable Benefit Sharing
FoSCoS	Food Safety Compliance System — FSSAI's online licensing portal
GI	Geographical Indication — protects products linked to a specific region
GRATK	WIPO Treaty on Genetic Resources and Associated Traditional Knowledge (2024)
IRCC	Internationally Recognized Certificate of Compliance — Nagoya Protocol due-diligence document
MAT	Mutually Agreed Terms — under the Nagoya Protocol
NBA	National Biodiversity Authority
NDI	New Dietary Ingredient — FDA pre-market notification requirement under DSHEA
PIC	Prior Informed Consent — under the Nagoya Protocol
PPV&FRA	Protection of Plant Varieties and Farmers' Rights Act, 2001
Proprietary Medicine	New formulation with known ingredients; requires safety data but not full clinical trials
RAG	Retrieval-Augmented Generation — AI architecture grounding LLM outputs in external documents
SBB	State Biodiversity Board
Section 3(p)	Patents Act provision barring patents on inventions that are, in effect, traditional knowledge
TK	Traditional Knowledge
TKDL	Traditional Knowledge Digital Library
THMPD	Traditional Herbal Medicinal Products Directive (EU 2004/24/EC)
Appendix III — Gap & Opportunity Matrix (Merged)
Unmet need	Current gap	Product feature opportunity	Priority
Practitioners cannot classify their product across drug/food/cosmetic boundaries	No single classification tool	Interactive formulation classifier, 3–5 question flow	Critical
No integrated view of IP + ABS + regulatory requirements	Fragmented across 10+ portals; no unified view	Unified dashboard: "for your [classified product] you need [Patent/GI check], [NBA registration], [FSSAI/CDSCO licence]"	Critical
Citation-grounded, non-hallucinating answers	Generic LLMs hallucinate statutes/forms	RAG with mandatory citation (URL + section number); template-based forms/fees (not generated)	Critical
No multilingual legal guidance for AYUSH	Most legal resources English-only	Bhashini-powered voice/text answers in Hindi and other Indic languages, with statutory citations; voice-first for Tier 2/3 cities	High/Critical
TKDL access is restricted and opaque	TKDL inaccessible for public RAG ingestion	TKDL status checker + guided access route (patent-office NDA vs. paid subscription), or reliance on public defensive-publication summaries	High/Medium
Export regulatory complexity	Country-specific regulations inaccessible to MSMEs	Jurisdiction-specific export wizards/checklists (USA/FDA, EU/THMPD, ASEAN/ACTTHMS, GCC/SFDA-MoHAP)	Medium/High
Difficulty tracking changing rules	Amendments frequent; manual tracking burdensome	Automated monitoring + email/SMS alerts for Patents Rules, Biodiversity Rules, FSSAI notification changes	Medium
No citation-grounded ABS calculator	No integrated benefit-sharing estimator	Benefit-sharing estimator based on turnover and resource type, reflecting both the applicant-payment slabs and the institution/community distribution split	Medium
Case-law search	SCC Online/Manupatra expensive; Indian Kanoon unstructured for casual use	Integrate Indian Kanoon API; curated case summaries for Section 3(p), GI, and trademark disputes	Low
Knowledge-graph visualisation	Statutes opaque; relationships unclear	Interactive graph: formulation → applicable law → required form → timeline, click-through to source	Low
Appendix IV — Unverifiable / Data Not Publicly Available (Merged)
Combined from both sources' "unverifiable items" appendices. These should be caveated or omitted from pitch materials rather than assumed, or replaced with qualitative statements.
1.	Granular revenue broken down by product category (classical vs. proprietary vs. phytopharmaceutical vs. Ayurveda-Aahar vs. cosmetics vs. new drugs) — only aggregate market estimates and percentage shares are available from either source; no government-published revenue segmentation was found.
2.	Year-wise, granular AYUSH-registered practitioner counts — Ministry of Ayush reports mention aggregate figures but not a consistent, publicly accessible breakdown (Source P); Source K cites differing aggregate figures from different secondary sources (500,000 vs. 780,000+) without a single authoritative reconciliation.
3.	Cluster-specific export volumes (Kerala, Gujarat, Rajasthan, Madhya Pradesh) — no primary trade-statistics source (Ministry of Commerce/DGCI&S) publishes an Ayurveda export breakdown by state or cluster in machine-readable form.
4.	Large-scale survey/interview data quantifying IP or regulatory-awareness gaps among AYUSH practitioners and startups — no peer-reviewed or government survey with disclosed sample size and methodology was located by either source.
5.	PPV&FRA case law or registrations specifically for Ayurveda medicinal plant varieties — no publicly documented cases or registrations were located.
6.	Specific enforcement actions/court rulings under the Drugs and Magic Remedies Act beyond the state-level tallies cited in Section B.3.b (2020–2025) — specific case citations require SCC Online/Manupatra access not available during this research.
7.	TKDL paid-subscription pricing and operational launch date — Cabinet approved the model in 2022, but public pricing and activation status remain undisclosed as of August 2026.
8.	Post-2023 amendments to the Drugs and Cosmetics Act specifically targeting AYUSH, beyond generally enhanced GMP/adverse-event-reporting requirements — no specific amendments were located in India Code or official gazettes.
9.	Exact statutory DPDP Act audit-trail retention period — secondary sources cite 36 months as good practice spanning multiple regimes (DPDP, CCPA, EU AI Act), but this is not stated as an explicit requirement in the publicly available DPDP Rules.
10.	Pricing/API-access details for SCC Online, Manupatra, and LexisNexis India beyond the headline subscription tiers — exact bulk-data licensing terms require direct inquiry.
11.	Live/real-time WIPO GRATK ratification count — the count used in this dossier (3–4, composition disputed) is based on press releases and WIPO Lex snapshots as of August 2026, not a continuously live dashboard; re-verify before using in the final submission.
12.	Recent (2022–2025) biopiracy/misappropriation cases beyond the ones listed in Section A.2 — no new landmark case matching the scale of turmeric/neem/basmati was found; TKDL continues defensive blocking, but specific new cases are not publicly documented in detail.
13.	Exact number of AYUSH-registered startups as distinct from MSMEs — "startups" are not separately categorised from MSMEs in available Ministry of Ayush data.
14.	An Ayurveda-specific FDA/DSHEA guidance document — the FDA regulates Ayurvedic products under its general dietary-supplement/cosmetic/drug frameworks; no Ayurveda-specific guidance document was located.


End of consolidated dossier.
Compiled from Research_for_PS_26041.docx (Kimi, "Source K") and Research_for_PS_26045.docx (Perplexity, "Source P"), both dated 26 August 2026, against the brief in Problem_Statement_I1.docx (SIH PS-26045).
