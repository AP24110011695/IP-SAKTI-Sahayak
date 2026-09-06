# Member 5 — standalone international IP guidance

## Run

From the repository root, no third-party Python packages are required:

```sh
python3 -m member5 "I want to file a patent internationally."
python3 -m member5 --language hi "मैं विदेश में पेटेंट दाखिल करना चाहता हूँ।"
python3 scripts/demo_member5.py
python3 -m unittest discover -s tests -v
RUN_NETWORK_TESTS=1 python3 -m unittest discover -s tests -v
```

## Supported scope

- PCT international patent filing pathway and national-phase limitation.
- Madrid international trademark registration system.
- Hague international industrial-design registration system.
- TRIPS Article 27.3(b).
- WIPO GRATK Treaty Articles 3.1, 3.2, and 17.
- International CBD Article 15 and Nagoya Protocol Articles 5 and 6 material.
- English and Hindi for the supported filing-route scenarios.

The hard route mapping is:

| IP right | International system |
|---|---|
| Patent | PCT |
| Trademark | Madrid |
| Industrial design | Hague |

## Jurisdiction and abstention

Member 5 accepts the `International` jurisdiction only. India-only procedure,
mixed India/international requests, ambiguous IP-right requests, multi-right
questions, unsupported domestic law, and country-specific export or market-access
requirements abstain without an answer or citations.

The Phase 1 corpus contains no sufficiently detailed official export-market record,
so export questions intentionally abstain. This avoids converting the supplied
secondary research dossier into unsupported legal guidance.

## Evidence, citations, and confidence

Evidence comes only from the 12 stored Phase 1 records. A generator may return only
an answer and selected record IDs. The application constructs each citation from
the corpus and rejects unknown IDs or any altered name, type, section, excerpt, URL,
or effective date. A final guard verifies PCT/Madrid/Hague against the detected IP
right and rejects invented URLs, unsupported numeric deadlines, and treaty-article
references absent from the cited sources' sections.

Confidence is deterministic. It is computed from route specificity, evidence
completeness, and stored verification status—not model self-confidence.

## Hosted-model behavior

If both `OPENAI_API_KEY` and `OPENAI_MODEL` are present, the OpenAI Responses API
adapter is selected. Otherwise the same interface uses the deterministic
evidence-only client. Phase 3 was validated offline because credentials were not
available; no live hosted call is claimed.

## M6 integration contract

Call:

```python
from member5 import guide

result = guide(query, language="en", jurisdiction="International")
```

Exact RAG Result shape:

```text
answer: string
citations: Citation[]
confidence: "HIGH" | "MEDIUM" | "LOW"
confidence_score: number from 0.0 through 1.0
abstention: boolean
abstention_reason: string | null
status: "ok" | "abstained" | "processing_error"
```

Exact Citation shape:

```text
id
source_name
source_type
section
excerpt
url
effective_date
```

An abstention is a valid result, not a processing error. Provider failures use
`processing_error` and never return fabricated guidance.

