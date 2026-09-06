"""Combined IP-SAKTI Sahayak application (M6 Phase 2 integration).

Serves the integrated MVP: M1's assistant with the real specialists wired in.

    POST /api/query     → routed to the real M3 (India) / M4 (ABS-TK) /
                          M5 (International) specialists; M2 classification
                          abstains toward the guided flow
    POST /api/classify  → the real M2 classifier
    GET  /api/health    → service + specialist registration status

Run from the repository root:

    python -m uvicorn integration.app:app --port 8000

Standalone (M1's own corpus, specialists not wired) remains available via
`uvicorn m1.api:app` from sihmember1/ for demo purposes.
"""
from .adapters import app

__all__ = ["app"]
