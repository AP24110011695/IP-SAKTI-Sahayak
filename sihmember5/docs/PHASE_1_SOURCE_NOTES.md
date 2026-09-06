# Phase 1 source notes

Verified on 2026-09-06 against official pages maintained by the WTO, WIPO,
and the Secretariat of the Convention on Biological Diversity.

## Selection and safety decisions

- The corpus contains exactly 12 short, verbatim-extract records. It is evidence for an MVP, not a
  complete statement of international law.
- PCT is tagged only as `patent`, Madrid only as `trademark`, and Hague only as
  `industrial_design`.
- PCT is described as an international patent **filing route**. A separate record
  preserves WIPO's warning that national or regional Offices grant patents during
  the national phase.
- The GRATK Treaty records distinguish adoption from entry into force. No volatile
  ratification count or claim of current entry into force is stored.
- CBD and Nagoya records stay at international-framework level and preserve the
  role of domestic access and benefit-sharing law.
- Fees, changing membership totals, country-specific deadlines, and export-market
  requirements are excluded from this foundation. They should be added only after
  separate current official-source verification.
- Claims in the supplied consolidated `Research.md` were treated as research leads,
  not as authorities.

## Official source set

- WTO: TRIPS Part II, Section 5, Article 27.
- WIPO Lex: WIPO GRATK Treaty, Articles 3 and 17.
- WIPO: PCT, Madrid, and Hague official system introductions.
- CBD Secretariat: CBD Article 15 and Nagoya Protocol Articles 5 and 6.

Each corpus record includes its precise URL, section, verification date, and
provenance note. Run `scripts/verify_urls.py` to repeat the live availability check.
