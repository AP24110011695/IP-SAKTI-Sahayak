"""Member 3 Phase 2 — real-run demonstration script.

Runs the acceptance checks for real and prints the outputs used in the
Phase Completion Report (MEMBER_3.md requires pasted real output):

  1. golden scenario 1 (patent / Section 3(p) / TKDL pointer)
  2. golden scenario 2 (GI registration)
  3. out-of-corpus abstention
  4. Hindi golden scenarios
  5. additional in-scope + domain-guard checks
  6. confidence explainability

Every result is checked against the RAG Result contract and every citation
is re-validated against the stored corpus before printing.

Generation mode: deterministic evidence-only template (the hosted LLM is
configured via M3_LLM_BASE_URL / M3_LLM_API_KEY / M3_LLM_MODEL — see
member3/llm.py; when those are absent the pipeline falls back to this mode
automatically). Run:

    python -m member3.run_phase2_checks
"""

from . import answer_india_question
from .citations import validate_citations
from .confidence import compute_confidence
from .guidance import validate_rag_result
from .retrieval import retrieve_evidence
from .routing import route_query


def _print_result(title, query, result, show_routing=True):
    print("=" * 78)
    print(title)
    print("=" * 78)
    print("QUERY   :", query)
    if show_routing:
        decision = route_query(query)
        print("ROUTING :", decision["route"], "| scope:", decision["scope_area"],
              "| language:", decision["language"])
        print("WHY     :", decision["reason"])
    print("STATUS  :", result["status"])
    print("CONF    :", result["confidence"], "(%.4f)" % result["confidence_score"])
    print("ABSTAIN :", result["abstention"], "| reason:", result["abstention_reason"])
    print("CONTRACT:", "VALID" if validate_rag_result(result) == [] else validate_rag_result(result))
    print("CITCHECK:", "ALL VALID" if validate_citations(result["citations"]) == []
          else validate_citations(result["citations"]))
    print("-" * 78)
    print(result["answer"])
    if result["citations"]:
        print("-" * 78)
        for citation in result["citations"]:
            print("* id=%s | %s | %s" % (citation["id"], citation["source_type"], citation["section"]))
            print("  url: %s" % citation["url"])
            print("  effective_date: %s" % citation["effective_date"])
    print()


def main():
    # 1. Golden scenario 1 — patents / Section 3(p) / TKDL pointer
    q1 = ("Can I patent a classical Ayurvedic formulation from an "
          "authoritative text?")
    _print_result("GOLDEN SCENARIO 1 — classical formulation patentability",
                  q1, answer_india_question(q1))

    # 2. Golden scenario 2 — GI registration
    q2 = ("How do I register a GI tag for an Ayurvedic product tied to a "
          "region?")
    _print_result("GOLDEN SCENARIO 2 — GI registration",
                  q2, answer_india_question(q2))

    # 3. Out-of-corpus abstention
    q3 = ("What is the fee for renewing a trademark in Japan under the "
          "Madrid Protocol?")
    _print_result("OUT-OF-CORPUS — must abstain", q3, answer_india_question(q3))

    # 4. Hindi golden scenarios
    q4 = ("क्या मैं किसी प्रामाणिक ग्रंथ से लिए गए शास्त्रीय आयुर्वेदिक "
          "फॉर्मूलेशन का पेटेंट कर सकता हूँ?")
    _print_result("HINDI — golden scenario 1", q4, answer_india_question(q4))

    q5 = "मैं अपने आयुर्वेदिक उत्पाद के लिए जीआई टैग कैसे पंजीकृत करूँ?"
    _print_result("HINDI — golden scenario 2", q5, answer_india_question(q5))

    # 5. Additional real checks (confidence variety + India-only guards)
    q6 = "Can I advertise that my chyawanprash cures diabetes?"
    _print_result("IN-SCOPE — Drugs & Magic Remedies advertising",
                  q6, answer_india_question(q6))

    q7 = "What is the Nagoya Protocol benefit sharing requirement?"
    _print_result("M4-DOMAIN GUARD — ABS question must abstain",
                  q7, answer_india_question(q7))

    # 6. Confidence explanation for golden 1 (explainability check)
    hits, _suff = retrieve_evidence(q1)
    label, score, explanation = compute_confidence(
        [h["record"] for h in hits], routed_scope_area="patents",
        best_score=hits[0]["score"],
    )
    print("=" * 78)
    print("CONFIDENCE EXPLAINABILITY — golden scenario 1")
    print("=" * 78)
    print("label=%s score=%.4f" % (label, score))
    print(explanation)
    print()


if __name__ == "__main__":
    main()
