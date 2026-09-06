"""Dump visible text of TKDL homepage; locate CBD Article 8(j) in treaty PDF."""
import os
import re
import sys

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")


def tkdl_text():
    h = open(os.path.join(TMP, "tkdl_home.html"), encoding="utf-8", errors="replace").read()
    h = re.sub(r"<script[\s\S]*?</script>", " ", h, flags=re.I)
    h = re.sub(r"<style[\s\S]*?</style>", " ", h, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", h)
    text = re.sub(r"\s+", " ", text)
    print("TKDL HOME TEXT:")
    print(text[:3500])


def cbd_8j():
    reader = pypdf.PdfReader(os.path.join(TMP, "cbd.pdf"))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    low = text.lower()
    print("CBD TOTAL CHARS:", len(text))
    for needle in ("innovations and practices", "article 8", "8 (j)", "8.(j)", "8(j)"):
        idx = low.find(needle.lower())
        print(f"[{needle}] -> idx {idx}")
        if idx >= 0 and needle == "innovations and practices":
            window = text[max(0, idx - 500) : idx + 700]
            print("   ", " ".join(window.split()))


if __name__ == "__main__":
    if sys.argv[1] == "tkdl":
        tkdl_text()
    elif sys.argv[1] == "cbd":
        cbd_8j()
