#!/usr/bin/env python3
"""Parse parts RH-982A dari PDF Brother."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/rh982a-partslist.pdf"
OUT = Path("audit-kelengkapan/parts_rh982a_hasil_parse.csv")

SECTIONS = {
    "A":  (1, 6),   "B":  (5, 10),  "C":  (9, 14),  "D":  (11, 16),
    "E":  (13, 18), "F1": (15, 20), "F2": (19, 24), "F3": (21, 26),
    "G":  (23, 28), "H":  (27, 32), "J":  (29, 34), "K":  (31, 36),
    "L":  (33, 38), "M":  (37, 42), "N":  (39, 44), "P1": (43, 48),
    "P2": (47, 52), "P3": (49, 54), "Q1": (51, 56), "Q2": (53, 58),
    "R":  (55, 60), "S1": (57, 62), "S2": (59, 64), "T1": (61, 66),
    "T2": (63, 68), "U":  (65, 70), "V":  (67, 72), "W":  (69, 74),
    "X":  (71, 76),
    "Y1": (73, 78), "Y2": (79, 84), "Y3": (81, 86), "Y4": (83, 88),
    "Y5": (89, 94), "Y6": (91, 96), "Z":  (93, 98),
}

CODE_PATTERN = re.compile(r"^(?:\d{6,9}|[A-Z]{1,3}\d{5,8}(?:-[A-Z0-9]+)?)$")

doc = pymupdf.open(PDF)
rows = []

for section, (page, pdf_idx) in sorted(SECTIONS.items(), key=lambda x: x[1][1]):
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] section {section}")
        continue
    page_text = doc[pdf_idx].get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
    i = 0
    section_count = 0
    while i < len(lines) - 3:
        if not re.match(r'^\d+\+?$', lines[i]):
            i += 1; continue
        ref = int(re.match(r'^(\d+)', lines[i]).group(1))
        code = lines[i+1]
        if not CODE_PATTERN.match(code):
            i += 1; continue
        qty_jp = lines[i+2]
        m = re.match(r'^[\(]?(\d+(?:\.\d+)?)[^\d\s]*[\)]?\s*(.*)$', qty_jp)
        if not m:
            i += 1; continue
        qty = m.group(1)
        name_en = lines[i+3] if i+3 < len(lines) else ""
        k = i+3
        while k < len(lines) and (not name_en or re.search(r'[ぁ-んァ-ヶ一-龠]', name_en)):
            k += 1
            name_en = lines[k] if k < len(lines) else ""
            if k > i+5: break
        if not name_en or re.search(r'[ぁ-んァ-ヶ一-龠]', name_en):
            name_en = m.group(2) if m.group(2) else code
        rows.append({
            "section_ref": section,
            "diagram_page": page,
            "catalog_ref": ref,
            "part_number": code,
            "part_name": name_en,
            "quantity": qty,
        })
        section_count += 1
        i = k + 1
    if section_count > 0:
        print(f"[section {section:>3}] {section_count} parts")

doc.close()

seen = set()
unique = []
for r in rows:
    k = (r['section_ref'], r['catalog_ref'], r['part_number'])
    if k in seen: continue
    seen.add(k)
    unique.append(r)

OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["section_ref","diagram_page","catalog_ref","part_number","part_name","quantity"])
    w.writeheader()
    w.writerows(unique)

print(f"\n[TOTAL] {len(rows)}, unik: {len(unique)}")
