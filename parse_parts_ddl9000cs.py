#!/usr/bin/env python3
"""Parser partslist JUKI DDL-9000C-S (versi ketat)."""
import re, csv
from pathlib import Path

SRC = Path("downloads/JUKI_DDL9000CS_partslist.txt")
OUT = Path("audit-kelengkapan/parts_ddl9000cs_hasil_parse.csv")

# Part number valid: XX-NNNNNNN[-XX] atau NNN-NNNNN
PN_PATTERN = re.compile(r"^(?:[A-Z]{2}-\d{6,7}(?:-[A-Z0-9]{2,3})?|\d{3}-\d{5})$")

# Format baris: ref [#kode] PARTNUMBER NAMA... qty
LINE_PATTERN = re.compile(
    r"^\s*(\d+)\s+"
    r"(?:#\d+\s+)?"
    r"([A-Z0-9][A-Z0-9\-]+)\s+"
    r"(.+?)\s+"
    r"(\d+(?:\.\d+)?)\s*$"
)

rows = []
with SRC.open(encoding="utf-8", errors="ignore") as f:
    for ln, line in enumerate(f, 1):
        if ln >= 1898:
            break
        m = LINE_PATTERN.match(line)
        if not m:
            continue
        ref, pn, name, qty = m.groups()
        if not PN_PATTERN.match(pn):
            continue
        if not name.strip():
            continue
        rows.append({
            "line": ln,
            "catalog_ref": int(ref),
            "part_number": pn,
            "part_name": name.strip(),
            "quantity": qty.strip(),
        })

print(f"Total baris ter-parse: {len(rows)}")
print(f"Part number unik  : {len(set(r['part_number'] for r in rows))}")

OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["line","catalog_ref","part_number","part_name","quantity"])
    w.writeheader()
    w.writerows(rows)
print(f"CSV: {OUT}")
print("\nContoh 8 baris pertama:")
for r in rows[:8]:
    print(r)
print("\nContoh 3 baris terakhir:")
for r in rows[-3:]:
    print(r)
