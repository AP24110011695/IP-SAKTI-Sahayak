"""Inspect downloaded HTML: title, matching hrefs, and text around a keyword."""
import os
import re
import sys

TMP = os.path.join(os.environ["TEMP"], "m4verify")


def main():
    name = sys.argv[1]
    keyword = sys.argv[2] if len(sys.argv) > 2 else "act"
    path = os.path.join(TMP, name)
    h = open(path, encoding="utf-8", errors="replace").read()
    titles = re.findall(r"<title>(.*?)</title>", h, re.S | re.I)
    print("TITLE:", titles[0].strip() if titles else "(none)", "| LEN:", len(h))
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', h)
    print("TOTAL HREFS:", len(hrefs))
    seen = set()
    for u in hrefs:
        if keyword.lower() in u.lower() and u not in seen:
            seen.add(u)
            print("HREF:", u)
    if len(seen) < 15:
        print("--- first 40 hrefs ---")
        for u in hrefs[:40]:
            print("  ", u)
    # text around keyword occurrences (tags stripped)
    text = re.sub(r"<[^>]+>", " ", h)
    text = re.sub(r"\s+", " ", text)
    low = text.lower()
    idx = 0
    for _ in range(3):
        idx = low.find(keyword.lower(), idx)
        if idx == -1:
            break
        print("TEXT>...", text[idx : idx + 300])
        idx += len(keyword)


if __name__ == "__main__":
    main()
