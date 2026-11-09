#!/usr/bin/env python3
"""Parse parts EX2200 dari PDF Pegasus."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/pegasus-EX2200_9B6006.pdf"
OUT = Path("audit-kelengkapan/parts_ex2200_hasil_parse.csv")

# section -> (diagram_page, table_pdf_idx_0based)
# page 2 -> tabel idx 4 (PDF hal 5)
# page 4 -> tabel idx 6
# Offset: tabel = page + 2
SECTIONS = {
    "BED":     (2, 4),
    "COVER1":  (4, 6),
    "COVER2":  (6, 8),
    "CRANK":   (8, 10),
    "TENSION": (10, 12),
    "GUIDE":   (12, 14),
    "NEEDLE1": (14, 16),
    "NEEDLE2": (16, 18),
    "NEEDLE3": (18, 20),
    "LOOPER1": (20, 22),
    "LOOPER2": (22, 24),
    "LOOPER3": (24, 26),
    "FEED1":   (26, 28),
    "FEED2":   (28, 30),
    "KNIFE":   (30, 32),
    "PRESSER": (32, 34),
    "LUBE1":   (34, 36),
    "LUBE2":   (36, 38),
    "HR":      (38, 40),
    "TSTAND":  (40, 42),
    "SEMI":    (42, 44),
    "SPEC":    (44, 46),
}

# Part number Pegasus: 7 digit (2010020) atau format lain
PART_PATTERN = re.compile(r"^\d{7,8}$")

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
        if not re.match(r'^\d+$', lines[i]):
            i += 1; continue
        ref = int(lines[i])
        pn = lines[i+1]
        if not PART_PATTERN.match(pn):
            i += 1; continue
        # nama_jp, lalu description (English), lalu qty
        name_jp = lines[i+2] if i+2 < len(lines) else ""
        name_en = lines[i+3] if i+3 < len(lines) else ""
        qty = lines[i+4] if i+4 < len(lines) else ""
        # Jika name_en masih Jepang, geser
        k = i+3
        while k < len(lines) and (not name_en or re.search(r'[ぁ-んァ-ヶ一-龠]', name_en)):
            k += 1
            name_en = lines[k] if k < len(lines) else ""
            if k > i+5: break
        # Cari qty (angka) setelah name_en
        qty = None
        for q in range(k+1, min(k+3, len(lines))):
            if re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', lines[q]):
                qty = lines[q]
                k = q
                break
        if qty is None:
            i += 1; continue
        if not name_en or re.search(r'[ぁ-んァ-ヶ一-龠]', name_en):
            name_en = name_jp
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
        print(f"[section {section:>8}] {section_count} parts")

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
