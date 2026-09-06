"""IP-SAKTI Sahayak — Member 1: Main Legal AI Assistant.

Standalone Phase 1 build: query handling, language/jurisdiction context,
retrieval over its own small curated real-source corpus, evidence ranking,
grounded prompt construction, hosted-LLM answer generation (with a
deterministic extractive fallback when no LLM API key is configured), and the
basic QueryResponse contract shape.
"""

__version__ = "0.1.0"
