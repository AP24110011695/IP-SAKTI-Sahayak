"""Live URL re-verification tool for the Member 3 source corpus.

Not a unit test — this performs real network requests. Run it manually to
re-check that every record URL still responds, e.g. before a demo:

    python -m member3.verify_urls

Expected output: one line per record with the HTTP status. Notes:
- Some official government sites (notably India Code) return an HTTP 200
  HTML stub to scripted clients (bot protection) even though the page is
  fine in a browser; statuses are reported as-is, and per-record
  verification notes in sources.py document how each excerpt was verified.
- Exit code 0 always unless a record's URL is unreachable at the network
  level (000), in which case exit code 1.
"""

import sys
import urllib.request

from .sources import all_sources

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def check_url(url, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except Exception as error:
        return "ERROR: %s" % str(error)[:80]


def main():
    unreachable = 0
    for record in all_sources():
        status = check_url(record["url"])
        print("%-32s %-4s %s" % (record["id"], status, record["url"][:80]))
        if status == "ERROR: " + "" or str(status).startswith("ERROR"):
            unreachable += 1
    print()
    print("%d records checked, %d network-level failures" % (
        len(all_sources()), unreachable))
    return 1 if unreachable else 0


if __name__ == "__main__":
    sys.exit(main())
