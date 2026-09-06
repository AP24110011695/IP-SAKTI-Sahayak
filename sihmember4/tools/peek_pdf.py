"""Peek at start of a PDF's extracted text."""
import os
import sys

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")
reader = pypdf.PdfReader(os.path.join(TMP, sys.argv[1]))
text = "\n".join(p.extract_text() or "" for p in reader.pages)
print("PAGES:", len(reader.pages), "CHARS:", len(text))
print(" ".join(text[:1200].split()))
