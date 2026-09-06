"""Member 4 Phase 2 — LLM transport layer.

Two modes, selected from environment variables (never faked):

- HostedLLM: a real OpenAI-compatible chat-completions client (urllib, no
  SDK dependency). Enabled only when M4_LLM_API_KEY is set; base URL and
  model are configurable via M4_LLM_BASE_URL / M4_LLM_MODEL.
- Stand-in (offline): when no credentials are configured, guidance.py
  composes the answer deterministically from the retrieved evidence records
  via the same validation path. This is NOT an LLM and is never presented as
  one; the phase report documents that no live API call was made.

The hosted client is deliberately thin: it sends the constrained prompt and
returns raw text. All grounding/citation/safety validation happens in
guidance.py regardless of mode.
"""

import json
import os
import ssl
import urllib.request

API_KEY_ENV = "M4_LLM_API_KEY"
BASE_URL_ENV = "M4_LLM_BASE_URL"
MODEL_ENV = "M4_LLM_MODEL"

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"

_SSL_CONTEXT = ssl.create_default_context()


class HostedLLM:
    """OpenAI-compatible chat-completions client (implemented, used only when
    credentials exist)."""

    def __init__(self, api_key, model=None, base_url=None):
        self.api_key = api_key
        self.model = model or os.environ.get(MODEL_ENV, DEFAULT_MODEL)
        self.base_url = (base_url or os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)).rstrip("/")

    def build_payload(self, system, user, temperature=0.0):
        """Build the request body (pure, unit-testable, no network)."""
        return {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

    def complete(self, system, user, timeout=60):
        payload = self.build_payload(system, user)
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]


class StandInLLM:
    """Marker for the deterministic offline mode (no network, no LLM)."""

    is_llm = False


def get_llm_client(env=None):
    """Return (mode, client). mode is 'hosted' or 'stand-in'.

    Reads os.environ unless an explicit mapping is passed (used by tests).
    """
    env = os.environ if env is None else env
    api_key = env.get(API_KEY_ENV)
    if api_key:
        return "hosted", HostedLLM(api_key)
    return "stand-in", StandInLLM()
