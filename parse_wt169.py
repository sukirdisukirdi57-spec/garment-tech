#!/usr/bin/env python3
"""Parse parts WT169 dari PDF Pegasus."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/pegasus2-wt100.pdf"
OUT = Path("audit-kelengkapan/parts_wt169_hasil_parse.csv")

# Offset: tabel = page + 3
SECTIONS = {
    "BED":      (2, 4),
    "COVER1":   (4, 6),
    "COVER2":   (6, 8),
    "CRANK":    (8, 10),
    "ARMSHAFT": (10, 12),
    "NEEDLEBAR":(12, 14),
    "LOOPER":   (14, 16),
    "FEED":     (16, 18),
    "TOPFEED1": (18, 20),
    "TOPFEED2": (20, 22),
    "TOPFEED3": (22, 24),
    "PRESSER":  (24, 26),
    "SPREADER": (26, 28),
    "TENSION":  (28, 30),
    "RELEASE":  (30, 32),
    "NDLTHREAD":(32, 34),
    "BOBBIN":   (34, 36),
    "LUBE1":    (36, 38),
    "LUBE2":    (38, 40),
    "HR":       (40, 42),
    "INSTALL":  (42, 44),
    "TSTAND":   (44, 46),
    "SPEC":     (46, 48),
    "TRIM1":    (48, 50),
    "TRIM2":    (50, 52),
    "UPTRIM":   (52, 54),
    "UPWIPE":   (54, 56),
    "UTACC":    (56, 58),
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
        if m:
            name_en = m.group(2).strip()
        else:
            name_en = name_jp_en
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
