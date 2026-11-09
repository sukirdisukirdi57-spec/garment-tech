#!/usr/bin/env python3
"""Parse parts MF-7500 Series dari PDF."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/mf7500-partslist.pdf"
OUT = Path("audit-kelengkapan/parts_mf7500_hasil_parse.csv")

SECTIONS = {
    1:  (1, 4),   2:  (3, 6),   3:  (5, 8),   4:  (7, 10),
    5:  (9, 12),  6:  (11, 14),
    7:  (12, 14),  # 1 page
    8:  (13, 15),  # 1 page
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
