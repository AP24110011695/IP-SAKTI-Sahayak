"""Temporary PDF text extraction used during Phase 1 source verification.

Not part of the deliverable runtime; kept so the verification step is repeatable.
"""
import os
import sys

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")

FILES = {
    "nagoya": "nagoya.pdf",
    "amendment": "bda_amendment_2023.pdf",
    "commencement": "commencement.pdf",
    "bdr": "bdr2024.pdf",
}


def full_text(name):
    reader = pypdf.PdfReader(os.path.join(TMP, name))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def main():
    which = sys.argv[1]
    text = full_text(FILES[which])
    if which == "commencement":
        print(" ".join(text[:2500].split()))
    elif which == "bdr":
        print("TOTAL CHARS:", len(text))
        low = text.lower()
        for needle in ("gsr", "come into force", "commercial utilisation", "rules, 2024"):
            count = low.count(needle)
            print(f"[{needle}] -> {count}")
            idx = low.find(needle)
            if idx >= 0:
                print("   ...", " ".join(text[idx : idx + 900].split()))
            print("-" * 90)


if __name__ == "__main__":
    main()
