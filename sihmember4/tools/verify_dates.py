"""Confirm treaty dates from official PDFs."""
import os

import pypdf

TMP = os.path.join(os.environ["TEMP"], "m4verify")


def grab(fname, needles, window=350):
    reader = pypdf.PdfReader(os.path.join(TMP, fname))
    text = " ".join(("\n".join(p.extract_text() or "" for p in reader.pages)).split())
    low = text.lower()
    for n in needles:
        idx = low.find(n.lower())
        print(f"[{fname}] [{n}] idx={idx}")
        if idx >= 0:
            print("   ", text[max(0, idx - 150) : idx + window])


grab("nagoya.pdf", ["entered into force on 12 september 2014", "adopted on 29 october 2010", "entered into force on 12th september 2014"])
grab("cbd.pdf", ["29 december 1993"])
