"""Show rules 14-16, 18, 20 context from BDR 2024 text."""
import os
import re

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")
reader = pypdf.PdfReader(os.path.join(TMP, "bdr2024.pdf"))
text = "\n".join(p.extract_text() or "" for p in reader.pages)
flat = " ".join(text.split())
for num in ("14.", "15.", "16.", "18.", "20."):
    pat = re.compile(r"\b" + re.escape(num) + r"\s+([A-Z][A-Za-z ,’'\-()&/]{5,90}\.)")
    m = pat.search(flat)
    if m:
        idx = m.start()
        print(num, "->", m.group(1))
        print("   ", flat[idx : idx + 450])
        print("-" * 80)
