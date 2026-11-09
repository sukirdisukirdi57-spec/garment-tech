#!/usr/bin/env python3
"""Ekstrak halaman diagram DDL-9000C-S dari partslist PDF -> JPG."""
import pymupdf
from pathlib import Path

PDF = "downloads/JUKI_DDL9000CS_partslist.pdf"
OUT = Path("assets/images/machines/juki/ddl9000cs")
OUT.mkdir(parents=True, exist_ok=True)

# halaman_manual -> section_ref
PAGES = {
    1: 1, 3: 2, 5: 3, 7: 4, 9: 5, 11: 6, 13: 7, 15: 8,
    17: 9, 19: 10, 20: 11, 21: 12, 22: 13, 23: 14, 25: 16,
}

PDF_OFFSET = 3  # halaman manual N = PDF page (N + 3) -> index N+2

doc = pymupdf.open(PDF)
print(f"PDF total halaman: {doc.page_count}")

# Matrix resolusi ~150 DPI
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

for manual_page, section_ref in sorted(PAGES.items()):
    pdf_index = manual_page + PDF_OFFSET - 1  # 0-based
    if pdf_index >= doc.page_count:
        print(f"[SKIP] section {section_ref}: PDF page {pdf_index+1} > total")
        continue
    page = doc[pdf_index]
    pix = page.get_pixmap(matrix=mat)
    out_file = OUT / f"section-{section_ref:02d}-page-{manual_page}.jpg"
    pix.save(str(out_file))
    print(f"[OK] section {section_ref:2d} -> PDF hal {pdf_index+1} -> {out_file.name} ({pix.width}x{pix.height})")

doc.close()
print(f"\n[SELESAI] output di {OUT}")
