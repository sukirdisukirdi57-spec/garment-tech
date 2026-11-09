#!/usr/bin/env python3
"""Ekstrak halaman diagram LBH-1790S dari partslist PDF -> JPG."""
import pymupdf
from pathlib import Path

PDF = "tmp/lbh1790s/partslist.pdf"
OUT = Path("static/images/mechanisms/juki/lbh1790s")
OUT.mkdir(parents=True, exist_ok=True)

# diagram_page -> PDF index (0-based)
# formula: pdf_index = diagram_page + 3 (karena diagram_pages = 1,3,5,... = +4 1-based)
PAGES = {
    1: 4, 3: 6, 5: 8, 7: 10, 9: 12, 11: 14, 13: 16, 15: 18,
    17: 20, 19: 22, 21: 24, 23: 26, 27: 30, 29: 32, 31: 34,
    33: 36, 35: 38,
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

for page, pdf_idx in sorted(PAGES.items()):
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] page {page}: pdf idx {pdf_idx} >= total")
        continue
    pix = doc[pdf_idx].get_pixmap(matrix=mat)
    out = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out))
    print(f"[OK] page {page:>2} -> PDF hal {pdf_idx+1} -> {out.name}")

doc.close()
print(f"\n[SELESAI] {OUT}")
