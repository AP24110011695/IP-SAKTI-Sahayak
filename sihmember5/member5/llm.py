"""Hosted and offline generation clients for grounded Member 5 guidance."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol


class GenerationError(RuntimeError):
    """Raised when a generation provider cannot return usable output."""


class GenerationClient(Protocol):
    def generate(
        self,
        *,
        query: str,
        evidence: list[dict[str, Any]],
        language: str,
        region: str | None,
    ) -> dict[str, Any]: ...


class DeterministicEvidenceClient:
    """Offline evidence-only stand-in used when API credentials are unavailable."""

    def generate(
        self,
        *,
        query: str,
        evidence: list[dict[str, Any]],
        language: str,
        region: str | None,
    ) -> dict[str, Any]:
        systems = {item["system"] for item in evidence}
        is_hindi = language == "hi"

        if "PCT" in systems:
            answer = (
                "कई देशों में किसी आविष्कार के लिए पेटेंट संरक्षण माँगने का प्रासंगिक अंतरराष्ट्रीय दाखिला मार्ग पेटेंट सहयोग संधि (PCT) है। "
                "PCT स्वयं विश्वव्यापी पेटेंट प्रदान नहीं करता; राष्ट्रीय चरण में पेटेंट राष्ट्रीय कार्यालय प्रदान करते हैं।"
                if is_hindi
                else "The relevant international filing route for seeking patent protection for an invention in multiple countries is the Patent Cooperation Treaty (PCT). "
                "The PCT does not itself grant a worldwide patent; national Offices grant patents during the national phase."
            )
        elif "Madrid" in systems:
            answer = (
                "कई देशों या क्षेत्रों में ब्रांड के ट्रेडमार्क संरक्षण के लिए प्रासंगिक अंतरराष्ट्रीय व्यवस्था मैड्रिड सिस्टम है। "
                "यह पेटेंट दाखिल करने की व्यवस्था नहीं है।"
                if is_hindi
                else "The relevant international system for seeking trademark protection for a brand in multiple countries or regions is the Madrid System. "
                "It is not a patent filing system."
            )
        elif "Hague" in systems:
            answer = (
                "कई देशों में औद्योगिक डिज़ाइन संरक्षण के लिए प्रासंगिक अंतरराष्ट्रीय व्यवस्था हेग सिस्टम है। "
                "यह पेटेंट या ट्रेडमार्क दाखिल करने की व्यवस्था नहीं है।"
                if is_hindi
                else "The relevant international system for seeking industrial-design protection in multiple countries is the Hague System. "
                "It is not a patent or trademark filing system."
            )
        elif "TRIPS" in systems:
            answer = (
                "TRIPS अनुच्छेद 27.3(b) सदस्यों को कुछ पौधों, पशुओं और मूलतः जैविक प्रक्रियाओं को पेटेंट-योग्यता से बाहर रखने की अनुमति देता है।"
                if is_hindi
                else "TRIPS Article 27.3(b) permits Members to exclude specified plants, animals, and essentially biological processes from patentability."
            )
        elif "WIPO_GRATK" in systems:
            answer = (
                "WIPO GRATK संधि का अनुच्छेद 3 आनुवंशिक संसाधनों या उनसे संबद्ध पारंपरिक ज्ञान पर आधारित पेटेंट आवेदनों के लिए प्रकटीकरण आवश्यकताओं से संबंधित है।"
                if is_hindi
                else "Article 3 of the WIPO GRATK Treaty addresses disclosure for patent applications based on genetic resources or associated traditional knowledge."
            )
        elif systems.intersection({"CBD", "Nagoya"}):
            answer = (
                "CBD और नागोया प्रोटोकॉल आनुवंशिक संसाधनों तक पहुँच, पूर्व सूचित सहमति और लाभ-साझाकरण का अंतरराष्ट्रीय ढाँचा देते हैं; लागू घरेलू नियम अलग से जाँचे जाने चाहिए।"
                if is_hindi
                else "The CBD and Nagoya Protocol provide an international framework for access to genetic resources, prior informed consent, and benefit-sharing; applicable domestic rules must be checked separately."
            )
        else:
            raise GenerationError("No deterministic template exists for the evidence.")

        if region:
            suffix = (
                f" अनुरोधित क्षेत्र: {region}; यह उत्तर वहाँ के घरेलू नियमों का वर्णन नहीं करता।"
                if is_hindi
                else f" Requested region: {region}; this answer does not describe its domestic rules."
            )
            answer += suffix

        return {"answer": answer, "citation_ids": [item["id"] for item in evidence]}


class OpenAIResponsesClient:
    """Minimal hosted adapter using OpenAI's Responses API and Structured Outputs."""

    endpoint = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 45,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL")
        self.timeout = timeout
        if not self.api_key or not self.model:
            raise GenerationError(
                "OPENAI_API_KEY and OPENAI_MODEL are required for hosted generation."
            )

    def generate(
        self,
        *,
        query: str,
        evidence: list[dict[str, Any]],
        language: str,
        region: str | None,
    ) -> dict[str, Any]:
        evidence_payload = [
            {
                "id": item["id"],
                "source_name": item["source_name"],
                "section": item["section"],
                "excerpt": item["excerpt"],
                "system": item["system"],
                "ip_right": item["ip_right"],
                "region": item["region"],
            }
            for item in evidence
        ]
        payload = {
            "model": self.model,
            "store": False,
            "instructions": (
                "Answer only from the supplied evidence. Do not add fees, deadlines, "
                "filing requirements, treaty rules, URLs, or legal conclusions absent "
                "from it. Return only an answer and IDs from the supplied evidence. "
                "PCT is patents, Madrid is trademarks, and Hague is industrial designs. "
                "The answer is general information, not legal advice."
            ),
            "input": json.dumps(
                {
                    "query": query,
                    "language": language,
                    "requested_region": region,
                    "evidence": evidence_payload,
                },
                ensure_ascii=False,
            ),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "grounded_international_guidance",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string"},
                            "citation_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["answer", "citation_ids"],
                        "additionalProperties": False,
                    },
                }
            },
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_payload = json.load(response)
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            raise GenerationError(f"Hosted generation failed: {error}") from error

        output_text = _extract_output_text(response_payload)
        try:
            return json.loads(output_text)
        except (TypeError, json.JSONDecodeError) as error:
            raise GenerationError("Hosted model returned malformed JSON.") from error


def _extract_output_text(payload: dict[str, Any]) -> str:
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise GenerationError("Hosted response contained no output text.")


def default_generation_client() -> GenerationClient:
    if os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_MODEL"):
        return OpenAIResponsesClient()
    return DeterministicEvidenceClient()

