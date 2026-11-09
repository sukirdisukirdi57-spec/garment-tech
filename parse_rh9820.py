#!/usr/bin/env python3
"""Parse parts RH-9820 dari PDF Brother (pendekatan linear)."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/rh9820-partslist.pdf"
OUT = Path("audit-kelengkapan/parts_rh9820_hasil_parse.csv")

# section -> (diagram_page, table_pdf_idx_0based)
# Offset: diagram page N -> PDF idx N+5; tabel = N+6
SECTIONS = {
    "A":  (1, 6),   "B":  (5, 10),  "C":  (7, 12),  "D":  (9, 14),
    "E":  (11, 16), "F1": (13, 18), "F2": (17, 22), "F3": (19, 24),
    "G":  (21, 26), "H":  (25, 30), "J":  (27, 32), "K":  (29, 34),
    "L":  (31, 36), "M":  (35, 40), "N":  (37, 42), "P1": (41, 46),
    "P2": (45, 50), "P3": (47, 52), "Q1": (49, 54), "Q2": (51, 56),
    "R":  (53, 58), "S1": (55, 60), "T":  (59, 64), "U1": (61, 66),
    "U2": (63, 68), "V":  (65, 70), "W":  (67, 72), "X":  (69, 74),
    "Y":  (71, 76),
    "AA1": (73, 78), "AA2": (79, 84), "AA3": (81, 86), "AA4": (83, 88),
    "AA5": (89, 94), "AA6": (93, 98), "AB": (95, 100), "AC": (95, 100),
    "AD": (97, 102), "AE": (101, 106), "AF": (105, 110), "Z": (109, 114),
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
        # Bersihkan qty dari karakter aneh (diakritik, dll)
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
