#!/usr/bin/env python3
"""Parse parts W674 dari PDF Pegasus."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/pegasus2-w674_9B6004.pdf"
OUT = Path("audit-kelengkapan/parts_w674_hasil_parse.csv")

# Offset: tabel = page + 3
SECTIONS = {
    "BED":      (2, 4),
    "COVER1":   (4, 6),
    "COVER2":   (6, 8),
    "COVER3":   (8, 10),
    "COVER4":   (10, 12),
    "COVER5":   (12, 14),
    "COVER6":   (14, 16),
    "COVER7":   (16, 18),
    "LOWSHAFT": (18, 20),
    "UPSHAFT":  (20, 22),
    "NEEDLEBAR":(22, 24),
    "NEEDLERECV":(24, 26),
    "LOOPER":   (26, 28),
    "FEED1":    (28, 30),
    "FEED2":    (30, 32),
    "PRESSER":  (32, 34),
    "TENSION1": (34, 36),
    "TENSION2": (36, 38),
    "NDLTHREAD":(38, 40),
    "BOBBIN":   (40, 42),
    "LUBE1":    (42, 44),
    "LUBE2":    (44, 46),
    "FT":       (46, 48),
    "RP1":      (48, 50),
    "RP2":      (50, 52),
    "CLOTH1":   (52, 54),
    "CLOTH2":   (54, 56),
    "CLOTH3":   (56, 58),
    "HG1":      (58, 60),
    "HG2":      (60, 62),
    "HG3":      (62, 64),
    "HG4":      (64, 66),
    "INSTALL":  (66, 68),
    "TSTAND":   (68, 70),
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
        # Nama jp+en gabung di baris berikut, atau terpisah
        name_jp_en = lines[i+2] if i+2 < len(lines) else ""
        # Coba pisah: jika ada huruf Latin setelah CJK
        m = re.match(r'^([ぁ-んァ-ヶ一-龠\s]+)([A-Za-z][A-Za-z0-9 \-&.,/]+)$', name_jp_en)
        if m:
            name_en = m.group(2).strip()
        else:
            name_en = name_jp_en
        # qty di baris berikut
        qty = lines[i+3] if i+3 < len(lines) else ""
        if not re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', qty):
            # coba cari qty di baris i+4
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
