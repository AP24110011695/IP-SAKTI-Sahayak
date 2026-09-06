"""Dump anchor text + href pairs for a downloaded HTML page."""
import os
import re
import sys

TMP = os.path.join(os.environ["TEMP"], "m4verify")


def main():
    name = sys.argv[1]
    h = open(os.path.join(TMP, name), encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', h, re.S | re.I):
        href, inner = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        inner = " ".join(inner.split())
        if inner:
            print(f"{href}  ||  {inner[:110]}")


if __name__ == "__main__":
    main()
