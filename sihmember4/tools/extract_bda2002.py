"""Extract Section 3(2) of the BDA 2002 from the Meghalaya-hosted PDF."""
import os

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")
reader = pypdf.PdfReader(os.path.join(TMP, "bda_2002_meg.pdf"))
text = "\n".join(p.extract_text() or "" for p in reader.pages)
print("CHARS:", len(text))
low = text.lower()
for needle in ("Certain persons not to undertake", "not a citizen of India", "obtain any biological resource occurring in India"):
    idx = low.find(needle.lower())
    print(f"[{needle}] -> idx {idx}")
    if idx >= 0:
        print("   ", " ".join(text[max(0, idx - 200) : idx + 1500].split()))
    print("-" * 80)
