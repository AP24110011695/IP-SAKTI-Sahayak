"""Print selected scenario outputs from the Phase 3 demo capture."""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

path = r"C:\Users\Devesh\AppData\Local\Temp\m4verify\demo3_out.txt"
text = open(path, encoding="utf-8").read()
blocks = re.split(r"={78}\n", text)
wanted = sys.argv[1:] or ["edge_part_abs_patent", "edge_nba_before_patent", "edge_species", "tkdl_details_query"]
for block in blocks:
    for name in wanted:
        if block.startswith(f"SCENARIO: {name} "):
            # compact: drop long excerpt fields for readability
            compact = re.sub(r'("excerpt": ")("?.{120})[^"]*("?.*)', r"\2...[full excerpt in citations]", block)
            print(compact[:3200])
            print("~" * 60)
