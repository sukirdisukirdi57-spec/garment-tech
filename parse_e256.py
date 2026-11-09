#!/usr/bin/env python3
"""Parse parts E256 dari PDF Pegasus."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/pegasus-E256_95460_1.pdf"
OUT = Path("audit-kelengkapan/parts_e256_hasil_parse.csv")

# section -> (diagram_page, table_pdf_idx_0based)
# page 2 -> diagram idx 3, tabel idx 4
# page 4 -> diagram idx 5, tabel idx 6
SECTIONS = {
    "BED":     (2, 4),
    "COVER1":  (4, 6),
    "COVER2":  (6, 8),
    "CRANK":   (8, 10),
    "NEEDLE":  (10, 12),
    "UPLOOPER":(12, 14),
    "LOWLOOPER":(14, 16),
    "FEED1":   (16, 18),
    "FEED2":   (18, 20),
    "KNIFE":   (20, 22),
    "PRESSER": (22, 24),
    "LUBE":    (24, 26),
    "HR":      (26, 28),
    "TSTAND":  (28, 30),
    "INSTALL1":(30, 32),
    "INSTALL2":(32, 34),
    "SPEC1":   (34, 36),
    "SPEC2":   (36, 38),
    "SPEC3":   (38, 40),
    "SPEC4":   (40, 42),
    "SPEC5":   (42, 44),
    "SPEC6":   (44, 46),
    "SPEC7":   (46, 48),
    "SPEC8":   (48, 50),
    "SPEC9":   (50, 52),
}

# Part number Pegasus: 7 digit, atau 6 digit + huruf (210336A910), atau 4 digit
PART_PATTERN = re.compile(r"^(?:\d{6,8}[A-Z0-9]*|[A-Z]\d{5,8})$")

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
        name_jp = lines[i+2] if i+2 < len(lines) else ""
        name_en = lines[i+3] if i+3 < len(lines) else ""
        k = i+3
        while k < len(lines) and (not name_en or re.search(r'[ぁ-んァ-ヶ一-龠]', name_en)):
            k += 1
            name_en = lines[k] if k < len(lines) else ""
            if k > i+5: break
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
        print(f"[section {section:>10}] {section_count} parts")

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
