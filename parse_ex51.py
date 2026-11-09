#!/usr/bin/env python3
"""Parse parts EX5100 Series dari PDF Pegasus."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/pegasus2-ex51_97290-1.pdf"
OUT = Path("audit-kelengkapan/parts_ex5100_hasil_parse.csv")

SECTIONS = {
    "BED":      (2, 4),
    "COVER1":   (4, 6),
    "COVER2":   (6, 8),
    "CRANK":    (8, 10),
    "NEEDLE":   (10, 12),
    "UPLOOPER": (12, 14),
    "LOWLOOPER":(14, 16),
    "FEED1":    (16, 18),
    "FEED2":    (18, 20),
    "KNIFE":    (20, 22),
    "PRESSER":  (22, 24),
    "TENSION":  (24, 26),
    "GUIDE":    (26, 28),
    "LUBE1":    (28, 30),
    "LUBE2":    (30, 32),
    "HR":       (32, 34),
    "TSTAND":   (34, 36),
    "SEMI":     (36, 38),
    "SPEC1":    (38, 40),
    "SPEC2":    (40, 42),
    "SPEC3":    (42, 44),
    "SPEC4":    (44, 46),
    "SPEC5":    (46, 48),
}

PART_PATTERN = re.compile(r"^(?:\d{5,8}[A-Z0-9]*|[A-Z]\d{5,8})$")

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
        name_jp_en = lines[i+2] if i+2 < len(lines) else ""
        m = re.match(r'^([ぁ-んァ-ヶ一-龠\s]+)([A-Za-z][A-Za-z0-9 \-&.,/]+)$', name_jp_en)
        name_en = m.group(2).strip() if m else name_jp_en
        qty = lines[i+3] if i+3 < len(lines) else ""
        if not re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', qty):
            if i+4 < len(lines) and re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', lines[i+4]):
                qty = lines[i+4]
                i += 1
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
        i += 3
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
