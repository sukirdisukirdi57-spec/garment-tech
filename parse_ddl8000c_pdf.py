#!/usr/bin/env python3
"""Parse parts DDL-8000C dari PDF resmi JUKI -> CSV."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/juki-ddl8000c/ddl8000c_partslist.pdf"
OUT = Path("audit-kelengkapan/parts_ddl8000c_pdf_hasil_parse.csv")

# section -> (diagram_page, table_pdf_idx_0based)
# PDF index tabel = diagram_page + 3 (0-based)
SECTIONS = {
    1:  (1, 4),   2:  (3, 6),   3:  (5, 8),   4:  (7, 10),
    5:  (9, 12),  6:  (11, 14), 7:  (13, 16), 8:  (15, 18),
    9:  (17, 20), 10: (19, 22), 11: (21, 24), 12: (23, 26),
    13: (25, 28), 14: (27, 30), 15: (29, 32), 16: (31, 34),
    17: (33, 36),
}

PN_PATTERN = re.compile(r"^(?:[A-Z]\d{4}-\d{3}-[A-Z0-9]+(?:-[A-Z0-9]+)?|[A-Z]{2,3}-\d{5,8}(?:-[A-Z0-9]{2,3})?|\d{3}-\d{5}|MDP-\d+[A-Z]\d+|\d{3}-\d{5})$")

doc = pymupdf.open(PDF)
rows = []

for section, (page, pdf_idx) in sorted(SECTIONS.items()):
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] section {section}: pdf idx {pdf_idx}")
        continue
    page_text = doc[pdf_idx].get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
    i = 0
    section_count = 0
    while i < len(lines) - 4:
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
        # next baris mungkin nama jepang, atau langsung qty
        if j+2 < len(lines) and re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', lines[j+2]):
            qty = lines[j+2]
            i = j + 3
        elif j+3 < len(lines) and re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', lines[j+3]):
            qty = lines[j+3]
            i = j + 4
        else:
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
    print(f"[section {section:>2}] {section_count} parts (PDF hal {pdf_idx+1})")

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

print(f"\n[TOTAL] {len(rows)} baris, unik: {len(unique)}")
print(f"[CSV] {OUT}")
