"""Locate notification header + key rules in the BDR 2024 PDF text."""
import os
import re

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")
reader = pypdf.PdfReader(os.path.join(TMP, "bdr2024.pdf"))
pages = [p.extract_text() or "" for p in reader.pages]
text = "\n".join(pages)
print("PAGES:", len(pages), "CHARS:", len(text))

# English text begins around page 50 per WIPO Lex; find the G.S.R. header
for i, pg in enumerate(pages):
    low = pg.lower()
    if "g.s.r" in low or "gsr" in low or "22nd october" in low or "october, 2024" in low:
        print(f"--- page {i+1} header hit ---")
        print(" ".join(pg[:1200].split()))
        break

low = text.lower()
for needle in ("form 2", "export", "commercial utilisation shall make an application"):
    idx = low.find(needle.lower())
    print(f"[{needle}] -> idx {idx}")
    if idx >= 0:
        # find which rule number this belongs to: search backwards for '5.' style
        window = text[max(0, idx - 600) : idx + 700]
        print("   ", " ".join(window.split()))
    print("-" * 80)
