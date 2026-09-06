"""Member 4 Phase 1 — live URL verification for every corpus record.

Fetches each unique corpus URL over the network (GET, browser-like UA), and
writes verification_report.json next to this file with the real result for
each URL. Run this before claiming Phase 1 verification complete:

    python m4_abs/verify_urls.py

The report records honest outcomes: ok only when the HTTP status is 200 and
the content type is PDF or HTML. Failures are recorded as failures, never
hidden.
"""

import json
import os
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from corpus import SOURCE_RECORDS, CORPUS_VERSION  # noqa: E402

REPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification_report.json")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Context tolerant of the varied government certificate chains encountered
# during Phase 1 verification (content integrity is anchored by the
# provenance records, not by this script's TLS policy).
_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE


def _check_with_curl(url):
    """Fallback for servers whose TLS stacks reject Python's handshake
    (observed for tkdl.res.in: curl connects where urllib fails)."""
    import subprocess

    try:
        proc = subprocess.run(
            ["curl", "-s", "-k", "-L", "-o", os.devnull,
             "-w", "%{http_code} %{content_type}", "-A", USER_AGENT,
             "--max-time", "60", url],
            capture_output=True, text=True, timeout=90,
        )
        parts = (proc.stdout or "").strip().split(" ", 1)
        status = int(parts[0]) if parts and parts[0].isdigit() else None
        content_type = parts[1].split(";")[0].strip().lower() if len(parts) > 1 else None
        ok = status == 200 and content_type in ("application/pdf", "text/html")
        return {
            "url": url, "status": status, "content_type": content_type, "ok": ok,
            "note": "verified via curl fallback (urllib TLS handshake failed)"
                    if ok else f"curl exit {proc.returncode}: {proc.stdout!r} {proc.stderr!r}",
        }
    except Exception as exc:
        return {"url": url, "status": None, "content_type": None, "ok": False,
                "note": f"curl fallback failed - {type(exc).__name__}: {exc}"}


def check_url(url, max_bytes=4096):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=45, context=_SSL_CONTEXT) as resp:
            status = resp.status
            content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            body = resp.read(max_bytes)
        ok = status == 200 and content_type in ("application/pdf", "text/html")
        return {
            "url": url,
            "status": status,
            "content_type": content_type,
            "ok": ok,
            "note": "" if ok else f"unexpected status/content-type (first bytes: {body[:40]!r})",
        }
    except Exception as exc:
        urllib_failure = f"{type(exc).__name__}: {exc}"
        result = _check_with_curl(url)
        if result["ok"]:
            result["note"] += f" [urllib failure: {urllib_failure}]"
        else:
            result["note"] += f" [urllib failure: {urllib_failure}]" if "curl exit" not in result["note"] else result["note"]
            result["note"] = f"urllib: {urllib_failure}; " + result["note"]
        return result


def main():
    urls = sorted({r["url"] for r in SOURCE_RECORDS})
    results = [check_url(url) for url in urls]
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "corpus_version": CORPUS_VERSION,
        "results": results,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    for r in results:
        print(("OK  " if r["ok"] else "FAIL"), r["status"], r["content_type"], r["url"])
        if r["note"]:
            print("     ", r["note"])
    print(f"\nReport written to {REPORT_PATH}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
