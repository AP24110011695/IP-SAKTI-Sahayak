# Phase 2 international guidance

## Flow

`guide()` performs these steps in order:

1. Validate language and international jurisdiction.
2. Reject India-only and unsupported country-specific market-access requests.
3. Detect the IP right and select only its verified Phase 1 records.
4. Generate from those records using the configured hosted client or the offline
   deterministic evidence client.
5. Convert returned citation IDs into stored citation metadata.
6. Validate every citation field and enforce PCT/Madrid/Hague right mappings;
   reject invented URLs, unsupported numeric deadlines, and treaty-article
   references absent from the cited sources' sections.
7. Compute confidence from routing specificity, evidence completeness, and stored
   verification status.
8. Return the stable RAG Result contract or safely abstain.

## Hosted generation

Set both `OPENAI_API_KEY` and `OPENAI_MODEL` to enable the minimal OpenAI Responses
API adapter. It requests JSON Schema output containing only `answer` and
`citation_ids`; citation metadata is never delegated to the model.

Without both variables, the implementation uses `DeterministicEvidenceClient`.
No live hosted-model call was made during Phase 2 because credentials were absent.

## Deliberate boundaries

- No India-specific procedure.
- No country-specific export or market-access guidance.
- No fees, changing membership counts, or filing deadlines.
- No multi-right combined answer in Phase 2.
- No vector database, reranker, framework, or agent workflow.

These boundaries cause explicit abstention instead of unsupported guidance.

