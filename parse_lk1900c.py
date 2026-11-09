#!/usr/bin/env python3
"""Parse parts LK-1900C Series dari PDF."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/lk1900c-partslist.pdf"
OUT = Path("audit-kelengkapan/parts_lk1900c_hasil_parse.csv")

# section -> (diagram_page, table_pdf_idx_0based)
# Offset: diagram page N -> PDF idx N+4 (0-based); tabel = +1
# Section 14, 16, 29 = 1 page
SECTIONS = {
    1:  (1, 6),   2:  (3, 8),   3:  (5, 10),  4:  (7, 12),
    5:  (9, 14),  6:  (11, 16), 7:  (13, 18), 8:  (15, 20),
    10: (19, 24), 11: (21, 26), 12: (23, 28), 13: (25, 30),
    14: (27, 32),
    16: (31, 36),
    17: (33, 38), 18: (35, 40), 19: (37, 42), 20: (39, 44),
    21: (41, 46), 22: (43, 48), 23: (45, 50), 24: (47, 52),
    25: (49, 54), 26: (51, 56), 27: (53, 58), 28: (55, 60),
    29: (57, 62),
    30: (59, 64), 31: (61, 66), 32: (63, 68), 33: (65, 70),
    34: (67, 72), 35: (69, 74), 36: (71, 76), 37: (73, 78), 38: (75, 80),
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
