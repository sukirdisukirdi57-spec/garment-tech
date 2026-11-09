#!/usr/bin/env python3
"""Parse parts LK-1900S dari PDF -> CSV."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/juki-lk1900s/partslist.pdf"
OUT = Path("audit-kelengkapan/parts_lk1900s_hasil_parse.csv")

# section -> (diagram_page, table_pdf_index_0based)
SECTIONS = {
    1: (1, 6), 2: (3, 8), 3: (5, 10), 4: (7, 12), 5: (9, 14),
    6: (11, 16), 7: (13, 18), 8: (15, 20), 9: (17, 22), 10: (19, 24),
    11: (21, 26), 12: (23, 28), 14: (27, 32), 15: (29, 34), 16: (31, 36),
    17: (33, 38), 18: (35, 40), 19: (37, 42), 20: (39, 44),
}

PN_PATTERN = re.compile(r"^(?:[A-Z]{2,3}-\d{5,8}(?:-[A-Z0-9]{2,3})?|\d{3}-\d{5}|MDP-\d+[A-Z]\d+)$")

doc = pymupdf.open(PDF)
rows = []

for section, (page, pdf_idx) in sorted(SECTIONS.items()):
    page_text = doc[pdf_idx].get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
    # Skip header (REF.NO NOTE PART NO DESCRIPTION 品名 Qty) 
    # Cari pola 5-baris berturut: angka, partno, nama_en, nama_jp, angka(qty)
    i = 0
    section_count = 0
    while i < len(lines) - 4:
        # ref (angka)
        if not re.match(r'^\d+(\s+[☆◎*#][\w\d]*)?$', lines[i]): 
            i += 1; continue
        ref = int(re.match(r'^(\d+)', lines[i]).group(1))
        # part number
        pn_candidate = lines[i+1]
        if not PN_PATTERN.match(pn_candidate):
            i += 1; continue
        pn = pn_candidate
        # nama inggris (boleh kosong?)
        name_en = lines[i+2]
        # nama jepang (biasanya ada karakter Jepang / CJK)
        name_jp = lines[i+3]
        # qty
        qty_candidate = lines[i+4]
        if not re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', qty_candidate):
            i += 1; continue
        rows.append({
            "section_ref": section,
            "diagram_page": page,
            "catalog_ref": ref,
            "part_number": pn,
            "part_name": name_en,
            "quantity": qty_candidate,
        })
        section_count += 1
        i += 5
    print(f"[section {section:>2}] {section_count} parts (PDF hal {pdf_idx+1})")

doc.close()

# Dedupe berdasarkan (part_number, section_ref, catalog_ref)
seen = set()
unique_rows = []
for r in rows:
    key = (r['part_number'], r['section_ref'], r['catalog_ref'])
    if key in seen: continue
    seen.add(key)
    unique_rows.append(r)

OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["section_ref","diagram_page","catalog_ref","part_number","part_name","quantity"])
    w.writeheader()
    w.writerows(unique_rows)

print(f"\n[TOTAL] {len(rows)} baris, unik: {len(unique_rows)}")
print(f"[CSV] {OUT}")

# Preview 3 baris
print("\nPreview 3 baris pertama:")
for r in unique_rows[:3]:
    print(r)
