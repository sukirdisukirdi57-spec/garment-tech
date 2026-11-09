#!/usr/bin/env python3
"""Parse parts BAS-311HN/BAS-326H dari PDF Brother."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/bas311hn/bas311hn_326h_pb.pdf"
OUT = Path("audit-kelengkapan/parts_bas311hn_hasil_parse.csv")

# section -> (diagram_page, table_pdf_idx_0based)
# Page 6 = diagram A (index 5), page 7 = tabel A (index 6)
# Offset: tabel idx = PDF page - 1 (0-based); untuk A: page 7 -> idx 6
SECTIONS = {
    "A":  (1, 6),
    "B":  (3, 8),
    "C1": (5, 10), "C2": (7, 12), "C3": (9, 14), "C4": (11, 16),
    "C5": (13, 18), "C6": (15, 20), "C7": (17, 22), "C8": (19, 24), "C9": (21, 26),
    "D1": (23, 28), "D2": (25, 30), "D3": (27, 32),
    "E":  (29, 34),
    "F":  (31, 36),
    "G":  (35, 40),
    "H":  (37, 42),
    "J":  (39, 44),
    "K":  (43, 48),
    "L1": (45, 50), "L2": (47, 52),
    "M1": (49, 54), "M2": (51, 56),
    "N":  (53, 58),
    "T1": (61, 66), "T2": (67, 72), "T3": (69, 74),
}

# Part code Brother: 7-9 digit atau SA/SB/SM/... + angka
CODE_PATTERN = re.compile(r"^(?:\d{7,9}|[A-Z]{1,3}\d{5,8}(?:-[A-Z0-9]+)?)$")

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
        # ref: angka atau angka+ (misal "1", "2", "46+")
        if not re.match(r'^\d+\+?$', lines[i]):
            i += 1; continue
        ref = int(re.match(r'^(\d+)', lines[i]).group(1))
        code = lines[i+1]
        if not CODE_PATTERN.match(code):
            i += 1; continue
        # qty: angka (bisa di baris terpisah)
        qty = None
        name_en = ""
        # Coba format: ref, code, qty, name_jp, name_en
        if i+4 < len(lines) and re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', lines[i+2]):
            qty = lines[i+2]
            # name_en di i+4 (setelah name_jp di i+3)
            name_en = lines[i+4]
            k = i+4
        else:
            # Coba format: ref, code, name_jp, name_en, qty
            name_en = lines[i+3] if i+3 < len(lines) else ""
            k = i+3
            # cari qty setelah name_en
            for q in range(k+1, min(k+3, len(lines))):
                if re.match(r'^[\(]?\d+(\.\d+)?[\)]?$', lines[q]):
                    qty = lines[q]
                    k = q
                    break
        if qty is None:
            i += 1; continue
        # Bersihkan name_en dari karakter Jepang
        if re.search(r'[ぁ-んァ-ヶ一-龠]', name_en):
            # coba ambil nama inggris di baris berikut
            name_en = lines[k+1] if k+1 < len(lines) else name_en
        rows.append({
            "section_ref": section,
            "diagram_page": page,
            "catalog_ref": ref,
            "part_number": code,
            "part_name": name_en.strip(),
            "quantity": qty,
        })
        section_count += 1
        i = k + 1
    if section_count > 0:
        print(f"[section {section:>3}] {section_count} parts")

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
