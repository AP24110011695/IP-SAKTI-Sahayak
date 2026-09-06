"""Show Rule 14 (and SBB-related rules) from the BDR 2024 PDF text."""
import os

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")
reader = pypdf.PdfReader(os.path.join(TMP, "bdr2024.pdf"))
text = "\n".join(p.extract_text() or "" for p in reader.pages)
low = text.lower()
for needle in ("14. registration", "14. procedure for", "state biodiversity board shall register", "registration with the state biodiversity board", "intimation to the state"):
    idx = low.find(needle.lower())
    print(f"[{needle}] -> idx {idx}")
    if idx >= 0:
        print("   ", " ".join(text[max(0, idx - 200) : idx + 1100].split()))
    print("-" * 80)
