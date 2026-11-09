#!/usr/bin/env python3
"""Parse parts DDL-8000C dari TXT -> CSV."""
import re, csv
from pathlib import Path

SRC = Path("tmp/ddl8000c-partslist-extracted.txt")
OUT = Path("audit-kelengkapan/parts_ddl8000c_hasil_parse.csv")

# Section boundaries (baris heading di TXT)
SECTIONS = [
    (111, 1,  "1. MACHINE FRAME & MISCELLANEOUS COVER COMPONENTS"),
    (265, 2,  "2. UPPER SHAFT AND PICK LINE COMPONENTS"),
    (375, 3,  "3. NEEDLE BAR & THREAD TENSION COMPONENTS"),
    (481, 4,  "4. HAND LIFTER COMPONENTS"),
    (604, 5,  "5. UPRIGHT SHAFT & HOOK DRIVING SHAFT COMPONENTS"),
    (701, 6,  "6. FEED MECHANISM COMPONENTS"),
    (832, 7,  "7. FEED ADJUST MECHANISM COMPONENTS"),
    (928, 8,  "8. THREAD TRIMMER COMPONENTS"),
    (1048, 9, "9. AUTOMATIC REVERSE FEED & NB COMPONENTS"),
    (1078, 10, "10. OIL LUBRICATION COMPONENTS"),
    (1184, 11, "11. OIL SHIELD COMPONENTS"),
    (1312, 12, "12. THREAD STAND COMPONENTS"),
    (1340, 13, "13. ACCESSORIE PART COMPONENTS"),
    # section 14 (1457+) SKIP - khusus SC/SH
]

# diagram_page mapping
PAGES = {1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15, 9: 17, 10: 19, 11: 21, 12: 23, 13: 25}

# Format: "  ref   PARTNO   NAMA   qty"
PATTERN = re.compile(r"^\s*(\d+)\s+(?:#\d+\s+)?([A-Z0-9][A-Z0-9\-]+)\s+(.+?)\s+\(?(\d+(?:\.\d+)?)\)?\s*$")

def get_section(ln):
    for start, ref, name in SECTIONS:
        if ln >= start:
            current = (ref, name)
        else:
            break
    return current if 'current' in dir() else None

rows = []
with SRC.open(encoding="utf-8", errors="ignore") as f:
    for ln, line in enumerate(f, 1):
        sec = get_section(ln)
        if not sec: continue
        m = PATTERN.match(line)
        if not m: continue
        ref_str, pn, name, qty = m.groups()
        # Skip jika pn bukan part number valid
        if not re.match(r'^[A-Z0-9]', pn): continue
        if len(name) < 2: continue
        rows.append({
            "section_ref": sec[0],
            "section_name": sec[1],
            "diagram_page": PAGES.get(sec[0], 1),
            "catalog_ref": int(ref_str),
            "part_number": pn,
            "part_name": name.strip(),
            "quantity": qty,
        })

# Dedupe per section
seen = set()
unique = []
for r in rows:
    k = (r['section_ref'], r['catalog_ref'], r['part_number'])
    if k in seen: continue
    seen.add(k)
    unique.append(r)

OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["section_ref","section_name","diagram_page","catalog_ref","part_number","part_name","quantity"])
    w.writeheader()
    w.writerows(unique)

print(f"[TOTAL] {len(rows)} baris, unik: {len(unique)}")

# Per section
from collections import Counter
c = Counter(r['section_ref'] for r in unique)
for ref in sorted(c):
    print(f"  section {ref:>2}: {c[ref]} parts")
print(f"\n[CSV] {OUT}")
