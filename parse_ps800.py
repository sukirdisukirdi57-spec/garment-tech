#!/usr/bin/env python3
"""Parse parts PS-800 dari PDF."""
import pymupdf, re, csv
from pathlib import Path

PDF = "ps800-parts.pdf"
OUT = Path("audit-kelengkapan/parts_ps800_hasil_parse.csv")

SECTIONS = {
    1:  (1, 5),   2:  (3, 7),   3:  (5, 9),   4:  (7, 11),  5:  (9, 13),
    6:  (11, 15), 7:  (13, 17), 8:  (15, 19), 9:  (17, 21), 10: (19, 23),
    11: (21, 25), 12: (23, 27), 13: (25, 29), 14: (27, 31), 15: (29, 33),
    16: (31, 35), 17: (33, 37), 18: (35, 39), 19: (37, 41), 20: (39, 43),
    21: (41, 45), 22: (43, 47), 23: (45, 49), 24: (47, 51), 25: (49, 53),
    26: (51, 55), 27: (53, 57), 28: (55, 59), 29: (57, 61), 30: (59, 63),
    31: (61, 65), 32: (63, 67), 33: (65, 69), 34: (67, 71), 35: (69, 73),
    36: (71, 75), 37: (73, 77),
}

PN_PATTERN = re.compile(r"^(?:[A-Z]\d{4}-\d{3}-[A-Z0-9]+(?:-[A-Z0-9]+)?|[A-Z]{2,3}-\d{5,8}(?:-[A-Z0-9]{2,3})?|\d{3}-\d{5}|[A-Z]{2}-\d{7}|\d{3}-\d{5}-[A-Z0-9]+)$")

doc = pymupdf.open(PDF)
rows = []

for section, (page, pdf_idx) in sorted(SECTIONS.items()):
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] section {section}")
        continue
    page_text = doc[pdf_idx].get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
    i = 0
    section_count = 0
    while i < len(lines) - 3:
        if not re.match(r'^\d+(\s+[☆◎＊*#][\w\d]*)?$', lines[i]):
            i += 1; continue
        ref = int(re.match(r'^(\d+)', lines[i]).group(1))
        j = i + 1
        while j < len(lines) and re.match(r'^[☆◎＊*#][\w\d]*$', lines[j]):
            j += 1
        pn = lines[j]
        if not PN_PATTERN.match(pn):
            i += 1; continue
        name_en = lines[j+1]
        k = j + 1
        while k < len(lines) and (not name_en or re.search(r'[ぁ-んァ-ヶ一-龠]', name_en)):
            k += 1
            name_en = lines[k] if k < len(lines) else ""
            if k > j+4: break
        qty = None
        for q in range(k+1, min(k+3, len(lines))):
            if re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', lines[q]):
                qty = lines[q]
                k = q
                break
        if qty is None:
            i += 1; continue
        rows.append({
            "section_ref": section,
            "diagram_page": page,
            "catalog_ref": ref,
            "part_number": pn,
            "part_name": name_en,
            "quantity": qty,
        })
        section_count += 1
        i = k + 1
    if section_count > 0:
        print(f"[section {section:>2}] {section_count} parts")

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
