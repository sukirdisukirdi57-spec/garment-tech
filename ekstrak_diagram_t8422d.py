#!/usr/bin/env python3
"""Ekstrak halaman diagram T-8422D dari PDF Brother."""
import pymupdf
from pathlib import Path

PDF = "work/brother84/t8421d_t8422d_parts_en.pdf"
OUT = Path("static/images/mechanisms/brother/t8422d")
OUT.mkdir(parents=True, exist_ok=True)

# diagram_page -> PDF index (0-based)
# diagram = manual_page + 4
PAGES = {
    1: 5, 3: 7, 5: 9, 7: 11, 9: 13, 11: 15, 13: 17, 15: 19,
    19: 23, 23: 27, 25: 29, 27: 31, 31: 35, 33: 37, 35: 39,
    39: 43, 41: 45, 43: 47, 45: 49, 47: 51, 49: 53, 51: 55,
    53: 57, 55: 59,
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

for page, pdf_idx in sorted(PAGES.items()):
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] page {page}")
        continue
    pix = doc[pdf_idx].get_pixmap(matrix=mat)
    out = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out))
    print(f"[OK] page {page:>2} -> PDF hal {pdf_idx+1} -> {out.name}")

doc.close()
print(f"\n[SELESAI] {OUT}")
