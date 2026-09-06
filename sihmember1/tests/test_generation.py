"""Generation tests: grounded prompt construction, extractive composition
(incl. Hindi renderings), and the hosted-LLM path — including the Phase 2
malformed-output rule (any LLM failure → insufficient, never fabricated)."""
import pytest

from m1.config import Config
from m1.corpus import load_corpus
from m1.generation import (
    INSUFFICIENT_MARKER,
    LLM_UNAVAILABLE_REASON,
    LLM_UNGROUNDED_REASON,
    ExtractiveGenerator,
    LLMGenerator,
    build_messages,
    _grounded_tags,
    _post_json,
)
from m1.models import QueryRequest


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


def make_req(**overrides):
    data = dict(
        id="g-1",
        query="How do I file a patent application outside India?",
        jurisdiction="International",
    )
    data.update(overrides)
    return QueryRequest(**data)


def test_prompt_contains_evidence_and_guards(corpus):
    req = make_req()
    evidence = corpus[5:8]
    messages = build_messages(req, evidence, Config())
    system = messages[0]["content"]
    user = messages[1]["content"]

    assert "jurisdiction = International" in system
    assert "English" in system
    assert INSUFFICIENT_MARKER in system
    assert "Never invent" in system

    for i, ev in enumerate(evidence, start=1):
        assert ev.source_name in user
        assert ev.text in user
        assert f"[E{i}]" in user
    assert req.query in user


def test_prompt_respects_india_jurisdiction(corpus):
    req = make_req(jurisdiction="India")
    system = build_messages(req, corpus[:2], Config())[0]["content"]
    assert "jurisdiction = India" in system


def test_prompt_hindi_language_instruction(corpus):
    req = make_req(language="hi")
    system = build_messages(req, corpus[:1], Config())[0]["content"]
    assert "Hindi" in system


def test_prompt_uses_hindi_excerpt_when_available(corpus):
    by_id = {e.id: e for e in corpus}
    ev = by_id["in-patents-act-3p"]
    assert ev.text_hi, "3(p) entry must carry a Hindi rendering"
    req = make_req(language="hi", jurisdiction="India")
    user = build_messages(req, [ev], Config())[1]["content"]
    assert ev.text_hi in user
    assert ev.text not in user  # English original not used when Hindi exists


def test_prompt_uses_english_when_no_hindi_rendering(corpus):
    ev = next(e for e in corpus if e.text_hi is None)
    req = make_req(language="hi")
    user = build_messages(req, [ev], Config())[1]["content"]
    assert ev.text in user


def test_extractive_answer_quotes_evidence_with_tags(corpus):
    req = make_req()
    evidence = corpus[5:7]
    out = ExtractiveGenerator(Config()).generate(req, evidence)
    assert out.generator == "extractive"
    assert not out.insufficient
    assert out.text
    for i, ev in enumerate(evidence, start=1):
        assert f"[E{i}]" in out.text
        assert ev.source_name in out.text
        assert ev.text in out.text


def test_extractive_no_evidence_is_insufficient():
    out = ExtractiveGenerator(Config()).generate(make_req(), [])
    assert out.insufficient
    assert out.text is None
    assert out.reason


def test_extractive_hindi_uses_hindi_renderings(corpus):
    by_id = {e.id: e for e in corpus}
    evidence = [by_id["in-patents-act-3p"], by_id["in-tkdl-pointer"]]
    req = make_req(language="hi", jurisdiction="India")
    out = ExtractiveGenerator(Config()).generate(req, evidence)
    assert not out.insufficient
    assert out.text
    assert "कानूनी सलाह नहीं" in out.text
    for ev in evidence:
        assert ev.text_hi in out.text  # Hindi rendering served
        assert ev.text not in out.text  # English original not used
    assert "अंग्रेज़ी" not in out.text  # no English-note needed


def test_extractive_hindi_notes_english_only_entries(corpus):
    by_id = {e.id: e for e in corpus}
    evidence = [by_id["in-patents-act-3p"], by_id["intl-trips-27-3b"]]
    req = make_req(language="hi")
    out = ExtractiveGenerator(Config()).generate(req, evidence)
    assert out.text
    assert by_id["in-patents-act-3p"].text_hi in out.text
    assert by_id["intl-trips-27-3b"].text in out.text  # no Hindi rendering
    assert "अंग्रेज़ी" in out.text  # honest note that some text is English


def test_grounded_tags_helper():
    assert _grounded_tags("Use the PCT route [E1].", 3)
    assert _grounded_tags("[E1] and [E3] say...", 3)
    assert not _grounded_tags("no tags at all", 3)
    assert not _grounded_tags("references [E9] out of range", 3)


def test_llm_uses_transport_response(monkeypatch, corpus):
    gen = LLMGenerator(Config(llm_api_key="test-key"))
    monkeypatch.setattr(
        gen,
        "_call_transport",
        lambda messages: {"choices": [{"message": {"content": "Use the PCT route [E1]."}}]},
    )
    out = gen.generate(make_req(), corpus[5:6])
    assert out.generator == "llm"
    assert out.text == "Use the PCT route [E1]."
    assert not out.insufficient


def test_llm_insufficient_marker_recognised(monkeypatch, corpus):
    gen = LLMGenerator(Config(llm_api_key="k"))
    monkeypatch.setattr(
        gen,
        "_call_transport",
        lambda m: {"choices": [{"message": {"content": INSUFFICIENT_MARKER}}]},
    )
    out = gen.generate(make_req(), corpus[:1])
    assert out.insufficient
    assert out.text is None
    assert out.reason


def test_llm_transport_error_abstains(monkeypatch, corpus):
    """Phase 2 malformed-output rule: an LLM failure must not silently fall
    back — the assistant abstains instead of guessing."""
    def boom(messages):
        raise RuntimeError("network down")

    gen = LLMGenerator(Config(llm_api_key="k"))
    monkeypatch.setattr(gen, "_call_transport", boom)
    out = gen.generate(make_req(), corpus[5:7])
    assert out.insufficient
    assert out.text is None
    assert out.reason == LLM_UNAVAILABLE_REASON


def test_llm_malformed_output_abstains(monkeypatch, corpus):
    gen = LLMGenerator(Config(llm_api_key="k"))
    monkeypatch.setattr(gen, "_call_transport", lambda m: {"choices": []})
    out = gen.generate(make_req(), corpus[:1])
    assert out.insufficient
    assert out.reason == LLM_UNAVAILABLE_REASON


def test_llm_blank_content_abstains(monkeypatch, corpus):
    gen = LLMGenerator(Config(llm_api_key="k"))
    monkeypatch.setattr(
        gen,
        "_call_transport",
        lambda m: {"choices": [{"message": {"content": "   "}}]},
    )
    out = gen.generate(make_req(), corpus[:1])
    assert out.insufficient


def test_llm_ungrounded_answer_abstains(monkeypatch, corpus):
    """An LLM answer with no [E#] evidence references cannot be traced to
    stored evidence → withhold it."""
    gen = LLMGenerator(Config(llm_api_key="k"))
    monkeypatch.setattr(
        gen,
        "_call_transport",
        lambda m: {"choices": [{"message": {"content": "Just file the form, trust me."}}]},
    )
    out = gen.generate(make_req(), corpus[:2])
    assert out.insufficient
    assert out.reason == LLM_UNGROUNDED_REASON


def test_llm_out_of_range_tag_abstains(monkeypatch, corpus):
    gen = LLMGenerator(Config(llm_api_key="k"))
    monkeypatch.setattr(
        gen,
        "_call_transport",
        lambda m: {"choices": [{"message": {"content": "See [E1] and [E9]." }}]},
    )
    out = gen.generate(make_req(), corpus[:2])
    assert out.insufficient
    assert out.reason == LLM_UNGROUNDED_REASON


def test_llm_endpoint_construction():
    gen = LLMGenerator(Config(llm_base_url="https://api.example.com/v1/"))
    assert gen._endpoint == "https://api.example.com/v1/chat/completions"


def test_post_json_real_transport():
    """Exercise the actual urllib transport against a local HTTP server: it
    must send the bearer token + JSON body and parse the JSON response."""
    import json as _json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            received["auth"] = self.headers.get("Authorization")
            received["body"] = _json.loads(self.rfile.read(length))
            payload = _json.dumps(
                {"choices": [{"message": {"content": "ok from local server"}}]}
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/chat/completions"
        resp = _post_json(
            url,
            {"model": "m", "messages": [{"role": "user", "content": "hi"}]},
            api_key="secret-key",
            timeout_secs=5,
        )
    finally:
        server.shutdown()

    assert resp["choices"][0]["message"]["content"] == "ok from local server"
    assert received["auth"] == "Bearer secret-key"
    assert received["body"]["model"] == "m"


def test_llm_generate_end_to_end_with_local_server(corpus):
    """Full hosted-LLM path over real HTTP (local stub server): an HTTP 500
    from the API must lead to abstention, never fabricated content."""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class FailingHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "boom"}')

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), FailingHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        cfg = Config(
            llm_api_key="k",
            llm_base_url=f"http://127.0.0.1:{server.server_port}",
            llm_timeout_secs=5,
        )
        out = LLMGenerator(cfg).generate(make_req(), corpus[5:7])
    finally:
        server.shutdown()

    assert out.insufficient
    assert out.text is None
    assert out.reason
