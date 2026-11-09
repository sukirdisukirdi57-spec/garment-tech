#!/usr/bin/env python3
"""Parse parts HE-800C dari PDF Brother."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/he800c-partslist.pdf"
OUT = Path("audit-kelengkapan/parts_he800c_hasil_parse.csv")

# Offset: tabel A di index 4 (diagram A di index 3)
# diagram page N -> PDF idx N+2; tabel = N+3
SECTIONS = {
    "A":  (1, 4),   "B":  (3, 6),   "C":  (5, 8),   "D":  (7, 10),
    "E":  (9, 12),  "F":  (11, 14), "G":  (13, 16), "H":  (15, 18),
    "J":  (17, 20), "K":  (19, 22), "L":  (21, 24), "M":  (23, 26),
    "N":  (27, 30), "P":  (31, 34), "Q":  (33, 36), "R":  (35, 38),
    "S1": (39, 42), "S2": (41, 44), "T":  (43, 46), "U":  (45, 48),
    "V":  (47, 50), "W":  (49, 52), "Z":  (51, 54),
}

CODE_PATTERN = re.compile(r"^(?:\d{7,9}|[A-Z]{1,3}\d{5,8}(?:-[A-Z0-9]+)?)$")

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
