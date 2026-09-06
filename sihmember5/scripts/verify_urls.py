#!/usr/bin/env python3
"""Resolve every unique official URL stored in the Phase 1 corpus."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from member5.corpus import load_sources  # noqa: E402


def main() -> int:
    failed = False
    urls = sorted({source["url"] for source in load_sources()})
    for url in urls:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 IP-SAKTI-Phase1-URL-Check/1.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                ok = response.status < 400 and response.geturl().startswith("https://")
                print(f"{'PASS' if ok else 'FAIL'} {response.status} {url}")
                failed = failed or not ok
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"FAIL {url} ({error})")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

