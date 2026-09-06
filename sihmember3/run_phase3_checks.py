"""Member 3 Phase 3 — real-run acceptance script (standalone demo).

Runs every Member 3 deliverable scenario for real through the full pipeline
(routing -> retrieval -> grounded generation -> guards -> citations ->
confidence) and prints the output pasted into the Phase Completion Report:

  - the two MEMBER_3.md Section 7 golden scenarios (English + Hindi);
  - the out-of-corpus abstention check;
  - the Phase 3 edge cases (multi-regime GI+patent, ambiguous IP type,
    food/drug boundary, BD-Act x patent intersection, cure-claim
    advertising, thin PPV&FRA evidence, unsupported procedure question).

Every result is validated against the RAG Result contract and every citation
is re-validated against the stored corpus before printing. Confidence
explainability is printed for the golden scenario.

Generation mode: deterministic evidence-only template unless a hosted LLM is
configured via M3_LLM_BASE_URL / M3_LLM_API_KEY / M3_LLM_MODEL (see
member3/llm.py) — live external generation remains environment-dependent.

Run:  python -m member3.run_phase3_checks
"""

from . import answer_india_question
from .citations import validate_citations
from .confidence import compute_confidence
from .guidance import validate_rag_result
from .retrieval import retrieve_evidence
from .routing import route_query


def _print_result(title, query):
    print("=" * 78)
    print(title)
    print("=" * 78)
    print("QUERY   :", query)
    decision = route_query(query)
    print("ROUTING :", decision["route"], "| scope:", decision["scope_area"],
          "| areas:", decision.get("matched_areas"),
          "| language:", decision["language"])
    print("STATUS  :", end=" ")
    result = answer_india_question(query)
    print(result["status"])
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
            print("* id=%s | %s | %s" % (citation["id"], citation["source_type"],
                                         citation["section"]))
            print("  url: %s" % citation["url"])
    print()


def main():
    q1 = ("Can I patent a classical Ayurvedic formulation from an "
          "authoritative text?")
    _print_result("GOLDEN SCENARIO 1 — classical formulation patentability", q1)

    q2 = ("How do I register a GI tag for an Ayurvedic product tied to a "
          "region?")
    _print_result("GOLDEN SCENARIO 2 — GI registration", q2)

    q3 = ("What is the fee for renewing a trademark in Japan under the "
          "Madrid Protocol?")
    _print_result("OUT-OF-CORPUS — must abstain", q3)

    q4 = ("क्या मैं किसी प्रामाणिक ग्रंथ से लिए गए शास्त्रीय आयुर्वेदिक "
          "फॉर्मूलेशन का पेटेंट कर सकता हूँ?")
    _print_result("HINDI — golden scenario 1", q4)

    q5 = "मैं अपने आयुर्वेदिक उत्पाद के लिए जीआई टैग कैसे पंजीकृत करूँ?"
    _print_result("HINDI — golden scenario 2", q5)

    _print_result(
        "EDGE — multi-regime: GI candidate AND classical-medicine patent "
        "question",
        "I have a classical Ayurvedic formulation and want to protect it - "
        "can I patent it, and can the region where we grow the herbs get a "
        "GI tag?")

    _print_result(
        "EDGE — ambiguous IP type (must abstain, no forced conclusion)",
        "How do I protect my Ayurvedic product in India?")

    _print_result(
        "EDGE — food vs drug regulatory boundary",
        "Is my bhasma-containing product a food or a drug in India?")

    _print_result(
        "EDGE — BD Act x patent intersection (India-IP side of ABS)",
        "Does the Biological Diversity Act affect my patent application for "
        "a herbal formulation?")

    _print_result(
        "EDGE — cure-claim advertising (Drugs & Magic Remedies)",
        "Can I claim my tonic cures diabetes and also improve sexual "
        "pleasure?")

    _print_result(
        "EDGE — thin evidence: PPV&FRA (only the real provision, no invented "
        "procedure)",
        "How do I register a new medicinal plant variety in India?")

    _print_result(
        "EDGE — unsupported procedural question (must abstain)",
        "What is the procedure to appeal before the IPAB?")

    # Confidence explainability for the golden scenario
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
