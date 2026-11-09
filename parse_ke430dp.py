#!/usr/bin/env python3
"""Parse parts KE-430DP/BE-438DP (format 5 baris: ref/code/qty/jp/en)."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/ke430dp_be438dp-partslist.pdf"
OUT = Path("audit-kelengkapan/parts_ke430dp_hasil_parse.csv")

SECTIONS = {
    "A":  (1, 4),   "B":  (3, 6),   "C":  (5, 8),   "D":  (9, 12),
    "F":  (11, 14), "G":  (13, 16), "H":  (15, 18), "J":  (17, 20),
    "K":  (19, 22), "L":  (23, 26), "M":  (25, 28), "R":  (27, 30),
    "Z":  (29, 32), "Wa": (31, 34),
}

CODE_PATTERN = re.compile(r"^(?:\d{7,9}|[A-Z]{2,3}\d{5,8}(?:-[A-Z0-9]+)?)$")

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
    while i < len(lines) - 4:
        if not re.match(r'^\d+$', lines[i]):
            i += 1; continue
        ref = int(lines[i])
        code = lines[i+1]
        if not CODE_PATTERN.match(code):
            i += 1; continue
        qty = lines[i+2]
        if not re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', qty):
            i += 1; continue
        name_jp = lines[i+3]
        name_en = lines[i+4] if i+4 < len(lines) else ""
        # Jika name_en masih Jepang/kosong, cari berikutnya
        k = i+4
        while k < len(lines) and (not name_en or re.search(r'[ぁ-んァ-ヶ一-龠]', name_en)):
            k += 1
            name_en = lines[k] if k < len(lines) else ""
            if k > i+6: break
        if not name_en or re.search(r'[ぁ-んァ-ヶ一-龠]', name_en):
            name_en = name_jp
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
