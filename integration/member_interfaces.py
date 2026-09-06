"""Machine-readable record of the ACTUAL member workstream interfaces.

Task 1 deliverable (M6 Phase 1): what each completed workstream really
exposes, verified by direct inspection and offline execution on 2026-09-07
(NOT taken from the members' completion reports). Import mechanics are
included because they differ per workstream and are the first thing a Phase
2 adapter needs.

Everything here was verified by running code:
- sihmember1: python -m pytest tests/ -q                      → 131 passed
- sihmember2: unittest via 'member2' alias (see finding F-01)  → 93 passed
- sihmember3: unittest via 'member3' alias (see finding F-01)  → 118 passed
- sihmember4: python -m unittest discover -s tests -t .        → 149 passed
- sihmember5: python -m unittest discover -s tests             → 64 passed, 1 skipped
"""

# ---------------------------------------------------------------------------
# Import mechanics per workstream (what a Phase 2 adapter must do)
# ---------------------------------------------------------------------------

IMPORT_MECHANICS = {
    "M1": (
        "Add repo-relative dir 'sihmember1' to sys.path, then 'import m1'. "
        "Package m1 uses relative imports. m1.models needs pydantic; m1.api "
        "additionally needs fastapi/uvicorn."
    ),
    "M2": (
        "Add repo root to sys.path, then 'import sihmember2' (the directory IS "
        "the package; it has __init__.py and only relative imports). M2's own "
        "tests/README use the legacy name 'member2' — see finding F-01."
    ),
    "M3": (
        "Add repo root to sys.path, then 'import sihmember3'. M3's own "
        "tests/README use the legacy name 'member3' — see finding F-01."
    ),
    "M4": (
        "Add the 'sihmember4' DIRECTORY itself to sys.path, then import the "
        "top-level modules ('import guidance', 'import corpus', ...). M4 uses "
        "ABSOLUTE imports and is not importable as a package by its module "
        "names. Clean up sys.path/sys.modules afterwards: the module names "
        "('corpus', 'guidance', 'hindi', 'llm_client', 'retrieval') are generic."
    ),
    "M5": (
        "Add the 'sihmember5' DIRECTORY itself to sys.path, then 'import "
        "member5' (the package is sihmember5/member5; sihmember5 itself has "
        "no __init__.py)."
    ),
}


# ---------------------------------------------------------------------------
# Actual public entry points (verified 2026-09-07)
# ---------------------------------------------------------------------------

MEMBER_INTERFACES = {
    "M1": {
        "directory": "sihmember1",
        "form": "fastapi_service",
        "http_api": ["POST /api/query", "GET /api/health"],
        "programmatic_entry": (
            "m1.assistant.handle_query(QueryRequest, config=None) -> "
            "AssistantResult(response: QueryResponse, status: 'ok'|'abstained', "
            "routing: RoutingDecision, generator_used: str)"
        ),
        "request_shape": "m1.models.QueryRequest (pydantic) — matches the Plan.md §7 contract exactly",
        "response_shape": "m1.models.QueryResponse (pydantic) — matches the contract exactly; "
                          "internal RAG 'status' is carried on AssistantResult, not on the HTTP body",
        "routing_mechanism": (
            "m1.routing.route(request) -> RoutingDecision(domain, specialist_registered, rationale); "
            "keyword heuristic: ABS/TK signals > classification signals > jurisdiction toggle. "
            "INTEGRATION SEAM (built for M6): m1.routing.register_specialist(Domain, name) plus "
            "Config.specialists_wired (env SPECIALISTS_WIRED=1) activates the corpus-safety rule: "
            "a specialist-domain query with no registered specialist abstains instead of "
            "answering from M1's standalone corpus."
        ),
        "fallback_behavior": (
            "Specialist unavailable + specialists_wired → HTTP 200 abstention with a "
            "domain-specific reason (en/hi). Insufficient evidence / failed citation "
            "validation / malformed LLM output → HTTP 200 abstention with fallback text. "
            "Internal failure (retrieval/generation crash) → ProcessingError → 502."
        ),
        "env": [
            "LLM_API_KEY (empty → deterministic extractive generator)",
            "LLM_BASE_URL (default https://api.openai.com/v1)",
            "LLM_MODEL (default gpt-4o-mini)",
            "LLM_TIMEOUT_SECS (30)", "RETRIEVAL_TOP_K (3)",
            "MIN_EVIDENCE_SCORE (0.5)", "SUFFICIENCY_THRESHOLD (2.5)",
            "SPECIALISTS_WIRED (off; M6 flips at integration)",
        ],
        "notes_for_m6": [
            "N-01: no POST /api/classify endpoint exists — M1 exposes only /api/query and "
            "/api/health. The contract's third endpoint must be added at integration "
            "(assembler.handle_classify shows the target behavior).",
            "N-02: escalation_available is always False (human-facilitator path out of scope).",
            "N-03: jurisdiction defaults to 'India'; invalid values are rejected 400.",
            "N-04: history is capped at 20 messages; Message.role is user|assistant only.",
            "N-05: no SERVICE_UNAVAILABLE/503 path exists in M1 (it has no downstream "
            "services standalone). The 503 mapping for an unreachable wired specialist is "
            "defined by the integration layer (contracts.ERROR_HTTP_STATUS).",
        ],
        "test_status": "131 pytest tests passed (2026-09-07)",
    },
    "M2": {
        "directory": "sihmember2",
        "form": "python_library (no HTTP service)",
        "programmatic_entry": (
            "classify(answers: dict[question_id -> value], jurisdiction='India', "
            "language='en') -> ClassificationResult dict; "
            "apply_clarification(answers, clarification_answers, ...) — one clarification "
            "round; get_questions() — bilingual guided questions; "
            "validate_classification_result(result) -> problems; ValidationError"
        ),
        "classification_result": (
            "All 7 contract fields present. Additive extras: confidence_score, "
            "clarification_question_ids, jurisdiction, language, category_labels, "
            "suggested_questions, reasoning. Machine values (formulation_class, "
            "confidence) are always English/uppercase regardless of language."
        ),
        "formulation_class_values": [
            "Classical", "Proprietary", "Phytopharmaceutical", "Ayurveda-Aahar",
            "Cosmetic", "New Drug", "Uncertain",
        ],
        "confidence_values": ["HIGH", "MEDIUM", "LOW"],
        "language_values": ["en", "hi"],
        "jurisdiction_values": ["India", "International"],
        "tkdl_pointer_behavior": (
            "tkdl_pointer is a pointer/description string only for the Classical category "
            "(names tkdl.res.in, describes restricted access); None for every other category. "
            "Never quotes TKDL content."
        ),
        "notes_for_m6": [
            "N-06: M2 is answers-driven, not free-text — /api/query traffic routed to "
            "CLASSIFICATION needs the guided-questions flow; a bare query cannot be classified.",
            "N-07: M2's ClassificationResult includes confidence_score with its own "
            "label↔score thresholds (HIGH ≥ 0.85, MEDIUM ≥ 0.60, else LOW).",
        ],
        "test_status": "93 unittest tests passed via 'member2' alias (2026-09-07)",
    },
    "M3": {
        "directory": "sihmember3",
        "form": "python_library (no HTTP service)",
        "programmatic_entry": (
            "answer_india_question(query, language=None, jurisdiction=None, llm=None) -> "
            "RAG Result dict (exactly the 7 contract fields). llm: injected client with "
            ".complete(system, user), or 'template', or None (env M3_LLM_*; falls back to a "
            "deterministic evidence-only template mode when unconfigured — offline-safe)."
        ),
        "rag_result_shape": "exactly the 7 contract fields (validate_rag_result enforces exact keys)",
        "status_semantics": (
            "ok / abstained / processing_error exactly per Plan.md §7; abstention_reason is "
            "'<machine_code>: <detail>' (e.g. out_of_scope_international, insufficient_evidence, "
            "unsupported_content, citation_validation_failed, llm_output_invalid)."
        ),
        "cross_domain_refusal": (
            "M3 refuses and abstains on international-only questions (reason code "
            "out_of_scope_international) and deep ABS/TK questions (out_of_scope_abs_tk) — "
            "India/International separation is enforced inside M3 itself."
        ),
        "tkdl_pointer_behavior": (
            "No tkdl_pointer field. For traditional-knowledge patentability questions the "
            "answer TEXT embeds a limited TKDL description with the URL https://tkdl.res.in "
            "(an allow-listed pointer; deep TKDL content is never stated)."
        ),
        "env": ["M3_LLM_BASE_URL", "M3_LLM_API_KEY", "M3_LLM_MODEL", "M3_LLM_TIMEOUT"],
        "notes_for_m6": [
            "N-08: M3's abstention answers always carry fallback text and the disclaimer; "
            "its ok-answers embed the disclaimer in the answer text — the assembler's "
            "QueryResponse.disclaimer field will duplicate it visibly (harmless but worth "
            "a Phase 2 presentation decision).",
        ],
        "test_status": "118 unittest tests passed via 'member3' alias (2026-09-07)",
    },
    "M4": {
        "directory": "sihmember4",
        "form": "python_library (no HTTP service; absolute-import modules)",
        "programmatic_entry": (
            "guidance.answer(query, language=None, llm=None) -> result dict with the 7 "
            "contract fields PLUS tkdl_pointer (string | None). llm: injected client — "
            "guidance.build_prompt(query, lang, evidence) -> (system, user), client.complete(...)"
            " -> raw text, guidance.parse_llm_output(raw) -> {'answer', 'citations': [record ids]} "
            "— or None for the deterministic offline stand-in."
        ),
        "relevance_behavior": (
            "Deterministic classify_query → ABS | TK | OTHER_IP | UNCLEAR. OTHER_IP and "
            "UNCLEAR queries abstain with 'unrelated'/'unclear' reasons (never ABS guidance); "
            "a biological-resource + patent query is a genuine ABS/IPR intersection and stays "
            "in-domain; a bare trademark question routes away."
        ),
        "tkdl_pointer_behavior": (
            "tkdl_pointer is set only for TK-domain queries or queries with TK phrases; it is "
            "a public-level pointer naming tkdl.res.in and the patent-office NDA restriction — "
            "never TKDL database content. Fee/amount questions always abstain (the corpus "
            "contains no fee figures); case-specific exemption determinations abstain."
        ),
        "env": ["M4_LLM_API_KEY (empty → offline stand-in)", "M4_LLM_BASE_URL", "M4_LLM_MODEL"],
        "notes_for_m6": [
            "N-09: M4's result has 8 fields (adds tkdl_pointer) — integration validators "
            "accept the additive field; do NOT run M3's exact-7-keys validator on M4 output.",
        ],
        "test_status": "149 unittest tests passed (2026-09-07)",
    },
    "M5": {
        "directory": "sihmember5",
        "form": "python_library (no HTTP service)",
        "programmatic_entry": (
            "member5.guide(query, *, language='en', jurisdiction='International', client=None) "
            "-> RAG Result dict (exactly the 7 contract fields). client: GenerationClient "
            "protocol with .generate(query=, evidence=, language=, region=) -> "
            "{'answer', 'citation_ids'}; None → deterministic evidence-only client "
            "(offline-safe) unless OPENAI_API_KEY+OPENAI_MODEL are set."
        ),
        "routing_mechanism": (
            "route_query(query, jurisdiction) -> RouteDecision(supported, intent, ip_right, "
            "system, evidence_ids, region, reason, specificity). India-jurisdiction queries "
            "abstain ('Member 5 handles International jurisdiction only'); unsupported "
            "languages ('en'/'hi' only) abstain."
        ),
        "treaty_guardrail": (
            "Built-in mapping guardrail: PCT→patents, Madrid→trademarks, Hague→industrial "
            "designs; an answer that mentions a system mismatched with the routed IP right "
            "is rejected before returning (abstains)."
        ),
        "env": ["OPENAI_API_KEY + OPENAI_MODEL (both set → hosted OpenAI Responses client)"],
        "notes_for_m6": [
            "N-10: M5's abstention results carry answer='' (empty string) — the assembler "
            "substitutes fallback text (see F-06).",
            "N-11: M5's confidence thresholds differ (abstains when score < 0.65).",
        ],
        "test_status": "64 unittest tests passed, 1 skipped (network opt-in) (2026-09-07)",
    },
}


# ---------------------------------------------------------------------------
# Compatibility findings (Task 6) — actual mismatches discovered by
# inspection/execution. severity: "adapt" = Phase 2 adapter work;
# "record" = behavioral difference to be aware of / verify in Phase 3 QA.
# Nothing here requires modifying member code in Phase 1.
# ---------------------------------------------------------------------------

COMPATIBILITY_FINDINGS = [
    {
        "id": "F-01",
        "member": "M2/M3 (and M4's README)",
        "area": "package naming",
        "severity": "adapt",
        "detail": (
            "M2's tests/README import 'member2' and M3's tests/README import 'member3', "
            "but the actual directories are 'sihmember2'/'sihmember3'. The library code "
            "itself uses relative imports and imports fine under the real names; only the "
            "self-tests/docs reference the legacy names. M4's README references 'm4_abs' "
            "for the directory now named 'sihmember4'."
        ),
        "phase2_action": (
            "Run M2/M3 self-tests via a sys.modules alias (integration/live_probe.py shows "
            "the pattern); adapters import the real package names. No member code change."
        ),
    },
    {
        "id": "F-02",
        "member": "M1",
        "area": "missing /api/classify endpoint",
        "severity": "adapt",
        "detail": (
            "The contract defines POST /api/classify, but M1's FastAPI app exposes only "
            "POST /api/query and GET /api/health."
        ),
        "phase2_action": (
            "Add the endpoint to M1's app (or a thin integration app) backed by "
            "assembler.handle_classify + the M2 adapter."
        ),
        "resolution": (
        "RESOLVED (Phase 2): adapters use the real package names; integration/adapters.alias_legacy_member_packages() provides the legacy alias for running M2/M3 self-tests. No member file changed."
    ),
},
    {
        "id": "F-03",
        "member": "M1 routing vs golden scenario 2",
        "area": "routing",
        "severity": "adapt",
        "detail": (
            "M1's ABS/TK keyword signals do NOT catch the golden ABS query ('I want to "
            "commercialise a formulation using a plant collected in India — what approvals "
            "do I need?'): it contains none of M1's ABS_TK_SIGNALS, so M1's heuristic would "
            "route it to INDIA_IP. M4's own classify_query DOES recognise it as ABS. "
            "integration.stubs.ABS_TK_SIGNALS adds 'plant collected'/'collected in india' "
            "to encode the TARGET routing for the harness."
        ),
        "phase2_action": (
            "Extend M1's ABS_TK_SIGNALS (small, safe data change) or defer ABS relevance "
            "to M4's classify_query during Phase 2 wiring; re-run scenario 2 after wiring."
        ),
        "resolution": (
        "RESOLVED (Phase 2): POST /api/classify added to m1/api.py; it serves the real M2 classifier via the specialist-handler seam (no duplicated classification logic); 503 when no handler is registered."
    ),
},
    {
        "id": "F-04",
        "member": "M5",
        "area": "processing_error shape",
        "severity": "record",
        "detail": (
            "On a generation failure M5 returns status='processing_error' but with "
            "abstention=True and a non-null abstention_reason (its _abstained helper), and "
            "answer=''. M3's processing_error is abstention=False/abstention_reason=None, "
            "which matches Plan.md's semantics ('processing_error' is not an abstention). "
            "contracts.validate_rag_result_semantics detects the M5 shape as invalid."
        ),
        "phase2_action": (
            "The assembler already treats status as authoritative (processing_error → 502 "
            "regardless of the abstention flag), so no disguise is possible. Optionally "
            "normalise M5's flags in its Phase 2 adapter."
        ),
        "resolution": (
        "RESOLVED (Phase 2): M1's ABS_TK_SIGNALS extended with 'plant collected'/'collected in india' (data-only change to sihmember1/m1/routing.py); the golden ABS query now routes ABS_TK (regression test: test_real_integration.py::test_abs_golden_query_routes_to_real_m4)."
    ),
},
    {
        "id": "F-05",
        "member": "M3 vs M4",
        "area": "tkdl_pointer placement",
        "severity": "record",
        "detail": (
            "The RAG Result contract has no tkdl_pointer field, but M4 adds one (8 fields) "
            "and M3 embeds its TKDL pointer in the answer text instead. M2 sets "
            "tkdl_pointer only for Classical."
        ),
        "phase2_action": (
            "Integration validators accept the additive field; M1's Phase 2 assembly should "
            "surface M4's tkdl_pointer when present (scenario 1 accepts the pointer in "
            "either form: answer text or field)."
        ),
        "resolution": (
        "RESOLVED at the boundary (Phase 2): integration/adapters._validated_rag_result treats status as authoritative for EVERY member (M4's failure path has the same shape as M5's) — processing_error raises AdapterError → M1 → HTTP 502; regression tests cover both members. Member code unchanged."
    ),
},
    {
        "id": "F-06",
        "member": "M5 vs M3/M4",
        "area": "abstention answer text",
        "severity": "record",
        "detail": (
            "M5's abstention results carry answer='' while M3/M4 return explanatory "
            "fallback text. M1's own abstentions always carry fallback text (en/hi)."
        ),
        "phase2_action": (
            "The assembler substitutes its fallback text when a specialist abstention has "
            "an empty answer — behavior encoded and tested."
        ),
    },
    {
        "id": "F-07",
        "member": "all",
        "area": "confidence thresholds",
        "severity": "record",
        "detail": (
            "Each member's label↔score mapping and abstention thresholds differ "
            "(M2 HIGH ≥ 0.85; M5 abstains < 0.65; M4 requires top-evidence ≥ 6.0 raw and "
            "confidence ≥ 0.5; M1 HIGH ≥ 0.5). The contract only fixes the vocabulary and "
            "the 0.0–1.0 range."
        ),
        "phase2_action": (
            "Do not harmonise — each domain's confidence is authoritative for its own "
            "result. Integration validation is vocabulary/range only."
        ),
        "resolution": (
        "RESOLVED at the boundary (Phase 2): m1.assistant substitutes its fallback text when a specialist abstention has an empty answer (regression test: test_f06_empty_specialist_abstention_gets_fallback_text). Member code unchanged."
    ),
},
    {
        "id": "F-08",
        "member": "M1 vs M3/M4/M5",
        "area": "citation field optionality",
        "severity": "record",
        "detail": (
            "M1's Citation model declares section/url/effective_date Optional; M3/M4/M5 "
            "always populate all seven fields from stored records. Contract validators "
            "allow None for those three, require the other four non-empty."
        ),
        "phase2_action": "None needed; documented for the Phase 3 citation audit.",
    },
    {
        "id": "F-09",
        "member": "M5",
        "area": "abstention gate breadth",
        "severity": "record",
        "detail": (
            "M5's abstention gate is specificity/score-based: a weakly-related patent "
            "question ('filing fee for patents in Antarctica?') still matched the PCT "
            "evidence and returned a generic ok answer rather than abstaining in a spot "
            "check on 2026-09-07."
        ),
        "phase2_action": (
            "No Phase 1 change (member code untouched). Phase 3 final QA must run the "
            "out-of-corpus abstention variants against the real integrated app and "
            "evaluate whether the gate needs tightening."
        ),
    },
    {
        "id": "F-10",
        "member": "M1 vs M3",
        "area": "503 semantics",
        "severity": "record",
        "detail": (
            "Plan.md §7 defines SERVICE_UNAVAILABLE → 503, but no member implements a 503 "
            "path (M1 maps its own failures to 502; M3/M4/M5 report status="
            "'processing_error'). M1's corpus-safety rule treats a MISSING specialist as an "
            "abstention (200), not 503."
        ),
        "phase2_action": (
            "Integration policy (encoded in the assembler): unregistered specialist → 200 "
            "abstention; registered-but-unreachable (SpecialistUnavailable) → 503; "
            "processing failure → 502. Confirm in Phase 2 review."
        ),
        "resolution": (
        "RESOLVED (Phase 2): minimal fee/cost guard added to sihmember5/member5/guidance.route_query (same documented rule M4 enforces — the corpus holds no amount figures). The F-09 query now abstains; M5's own 64-test suite still passes; regression test: test_f09_weak_fee_query_abstains_over_http."
    ),
},
    {
        "id": "F-11",
        "member": "M3",
        "area": "duplicate disclaimer",
        "severity": "record",
        "detail": (
            "M3/M4/M5 embed a not-legal-advice disclaimer in their answer text; the "
            "QueryResponse contract also carries a standing disclaimer field. Assembled "
            "responses will show the disclaimer twice when a domain answer is used verbatim."
        ),
        "phase2_action": "Presentation decision in Phase 2 (harmless duplication; do not strip member text mechanically).",
    },
]
