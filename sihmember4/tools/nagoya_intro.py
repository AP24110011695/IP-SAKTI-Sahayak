"""Find adoption/entry-into-force phrasing in Nagoya PDF intro."""
import os

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")
reader = pypdf.PdfReader(os.path.join(TMP, "nagoya.pdf"))
text = " ".join(("\n".join(p.extract_text() or "" for p in reader.pages)).split())
low = text.lower()
for n in ("nagoya, japan", "12 september 2014", "september 2014", "29 october 2010", "ratifi"):
    idx = low.find(n)
    print(f"[{n}] idx={idx}")
    if idx >= 0:
        print("   ", text[max(0, idx - 250) : idx + 250])
    print("-" * 70)
