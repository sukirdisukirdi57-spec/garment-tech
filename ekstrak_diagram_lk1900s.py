#!/usr/bin/env python3
"""Ekstrak halaman diagram LK-1900S dari partslist PDF -> JPG."""
import pymupdf
from pathlib import Path

PDF = "tmp/juki-lk1900s/partslist.pdf"
OUT = Path("static/images/mechanisms/juki/lk1900s")
OUT.mkdir(parents=True, exist_ok=True)

# diagram_page -> PDF index (0-based)
PAGES = {
    1: 5, 3: 7, 5: 9, 7: 11, 9: 13, 11: 15, 13: 17, 15: 19,
    17: 21, 19: 23, 21: 25, 23: 27, 27: 31, 29: 33, 31: 35,
    33: 37, 35: 39, 37: 41, 39: 43,
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

for page, pdf_idx in sorted(PAGES.items()):
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] page {page}: PDF idx {pdf_idx} > total")
        continue
    pix = doc[pdf_idx].get_pixmap(matrix=mat)
    out_file = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out_file))
    print(f"[OK] page {page:>2} -> PDF hal {pdf_idx+1} -> {out_file.name}")

doc.close()
print(f"\n[SELESAI] {OUT}")
