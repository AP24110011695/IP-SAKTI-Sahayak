# IP-SAKTI Sahayak — Member 5

Standalone international IP source foundation for Team CyberSapien's SIH-26045 MVP.

## Phase status

Member 5 Phases 1–3 are complete and the standalone workstream is `READY`.
Phase 1 provides:

- 12 short, curated records from official WTO, WIPO, and CBD sources;
- explicit international jurisdiction and IP-right metadata;
- enforced route mapping: PCT to patents, Madrid to trademarks, and Hague to industrial designs;
- a small deterministic retrieval seam for corpus validation;
- local metadata/mapping/retrieval tests and an opt-in live URL test.

Phase 2 adds:

- deterministic international/India and region-aware routing;
- right-specific evidence selection and PCT/Madrid/Hague guardrails;
- validated citations constructed only from stored records;
- evidence-based confidence and safe abstention;
- English and Hindi evidence-only responses;
- a hosted OpenAI Responses API adapter with Structured Outputs.

When both `OPENAI_API_KEY` and `OPENAI_MODEL` are configured, `guide()` uses the
hosted adapter. Otherwise it uses a deterministic evidence-only client so the
standalone feature remains testable without pretending a live model call occurred.

## Run checks and demos

Requires Python 3.10+ and no third-party packages.

```sh
python3 -m unittest discover -s tests -v
RUN_NETWORK_TESTS=1 python3 -m unittest discover -s tests -v
python3 scripts/verify_urls.py
python3 scripts/demo_member5.py
python3 -m member5 "I want to file a patent internationally."
```

The network-enabled commands contact only the official URLs stored in the corpus.

## Standalone interface

```python
from member5 import guide

result = guide(
    "I want to file a patent internationally.",
    language="en",                 # "en" or "hi"
    jurisdiction="International", # Member 5 rejects India-only requests
)
```

The returned dictionary contains exactly `answer`, `citations`, `confidence`,
`confidence_score`, `abstention`, `abstention_reason`, and `status`.

See `docs/MEMBER_5_STANDALONE.md` for supported scope, safety boundaries, golden
scenarios, and the complete Member 6 integration contract.
