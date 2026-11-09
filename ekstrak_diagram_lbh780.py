#!/usr/bin/env python3
"""Ekstrak halaman diagram LBH-780."""
import pymupdf
from pathlib import Path

PDF = "tmp/lbh780/partslist.pdf"
OUT = Path("static/images/mechanisms/juki/lbh780")
OUT.mkdir(parents=True, exist_ok=True)

# diagram_page -> PDF index (0-based)
# diagram_page 1 -> pdf idx 3, diagram_page 3 -> pdf idx 5, dst (offset +2)
PAGES = {
    1: 3, 3: 5, 5: 7, 7: 9, 8: 10, 9: 11, 11: 13, 12: 14, 13: 15, 15: 17,
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
