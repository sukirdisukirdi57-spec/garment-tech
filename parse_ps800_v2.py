#!/usr/bin/env python3
"""Parse parts PS-800 v2 (format: ref/pn/en/jp/qty)."""
import pymupdf, re, csv
from pathlib import Path

PDF = "ps800-parts.pdf"
OUT = Path("audit-kelengkapan/parts_ps800_hasil_parse.csv")

SECTIONS = {i: (2*i-1, 2*i+4) for i in range(1, 38)}

PN_PATTERN = re.compile(r"^(?:[A-Z]\d{4}-\d{3}-[A-Z0-9]+(?:-[A-Z0-9]+)?|[A-Z]{2,3}-\d{5,8}(?:-[A-Z0-9]{2,3})?|\d{3}-\d{5}|[A-Z]{2}-\d{7}|\d{3}-\d{5}-[A-Z0-9]+|\d{3}-\d{5})$")

doc = pymupdf.open(PDF)
rows = []

for section, (page, pdf_idx) in sorted(SECTIONS.items()):
    if pdf_idx >= doc.page_count:
        continue
    page_text = doc[pdf_idx].get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
    i = 0
    section_count = 0
    while i < len(lines) - 4:
        # ref: angka atau "-"
        if not re.match(r'^(\d+|-)$', lines[i]):
            i += 1; continue
        ref_str = lines[i]
        ref = int(ref_str) if ref_str.isdigit() else 0
        pn = lines[i+1]
        name_en = lines[i+2] if i+2 < len(lines) else ""
        if pn == "-":
            # PART NO kosong: pakai nama part sebagai identifier
            if not name_en:
                i += 1; continue
            pn = f"SEC{section}-REF{ref}-" + re.sub(r'[^A-Z0-9]', '_', name_en.upper())[:30]
        elif not PN_PATTERN.match(pn):
            i += 1; continue
        if not name_en:
            i += 1; continue
        # baris berikutnya = name_jp, setelah itu qty
        name_jp = lines[i+3] if i+3 < len(lines) else ""
        qty = None
        for q in range(i+4, min(i+6, len(lines))):
            if re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', lines[q]):
                qty = lines[q]
                i = q
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
        i += 1
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
