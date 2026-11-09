#!/usr/bin/env python3
"""Ekstrak halaman diagram T-8421D dari PDF Brother."""
import pymupdf
from pathlib import Path

PDF = "work/brother84/t8421d_t8422d_parts_en.pdf"
OUT = Path("static/images/mechanisms/brother/t8421d")
OUT.mkdir(parents=True, exist_ok=True)

# section_order -> (diagram_page, PDF index 0-based)
# diagram = manual_page + 4
PAGES = {
    1: 5, 2: 7, 3: 9, 4: 11, 5: 13, 6: 15, 7: 17, 8: 19,
    9: 21,    # J1 (manual page 17 -> pdf 21)
    10: 27,   # J3 (manual page 23 -> pdf 27)
    11: 29, 12: 31, 13: 35, 14: 37, 15: 39,
    16: 43,   # Q varian (manual page 39 -> pdf 43)
    17: 45,   # R varian (manual page 41 -> pdf 45)
    18: 47, 19: 49, 20: 51, 21: 53, 22: 55, 23: 57, 24: 59,
}

# diagram_page untuk image_path
SECTION_TO_PAGE = {
    1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15,
    9: 17, 10: 23, 11: 25, 12: 27, 13: 31, 14: 33, 15: 35,
    16: 39, 17: 41, 18: 43, 19: 45, 20: 47, 21: 49, 22: 51,
    23: 53, 24: 55,
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

for sec_order, pdf_idx in sorted(PAGES.items()):
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] section {sec_order}")
        continue
    pix = doc[pdf_idx].get_pixmap(matrix=mat)
    page = SECTION_TO_PAGE[sec_order]
    out = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out))
    print(f"[OK] sec {sec_order:>2} -> page {page:>2} -> PDF hal {pdf_idx+1} -> {out.name}")

doc.close()
print(f"\n[SELESAI] {OUT}")
