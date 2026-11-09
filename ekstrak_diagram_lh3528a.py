#!/usr/bin/env python3
"""Ekstrak diagram LH-3528A untuk semua komponen."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/lh3528a/partslist.pdf"
OUT = Path("static/images/mechanisms/juki/lh3528a")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 18

# Offset: diagram page N -> PDF index N+4
OFFSET = 4

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT DISTINCT diagram_page FROM components WHERE machine_id=? AND diagram_page IS NOT NULL ORDER BY diagram_page", (MID,))
pages = [r[0] for r in cur.fetchall()]
print(f"Diagram pages yang dibutuhkan: {pages}")

for page in pages:
    pdf_idx = int(page) + OFFSET
    if pdf_idx >= doc.page_count:
        print(f"[SKIP] page {page}: PDF idx {pdf_idx} >= {doc.page_count}")
        continue
    pix = doc[pdf_idx].get_pixmap(matrix=mat)
    out = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out))
    print(f"[OK] page {page:>2} -> PDF hal {pdf_idx+1} -> {out.name}")

doc.close()
conn.close()
print(f"\n[SELESAI] {OUT}")
