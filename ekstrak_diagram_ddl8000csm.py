#!/usr/bin/env python3
"""Ekstrak halaman diagram DDL-8000CSM dari PDF partslist."""
import pymupdf
from pathlib import Path

PDF = "tmp/juki-ddl8000c/ddl8000c_partslist.pdf"
OUT = Path("static/images/mechanisms/juki/ddl8000csm")
OUT.mkdir(parents=True, exist_ok=True)

# diagram_page -> PDF index (0-based). Offset +2 (diagram page N -> pdf idx N+2)
PAGES = {
    1: 3, 3: 5, 5: 7, 7: 9, 9: 11, 11: 13, 13: 15, 15: 17,
    17: 19, 19: 21, 21: 23, 23: 25, 25: 27, 27: 29, 29: 31,
    31: 33, 33: 35,
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
