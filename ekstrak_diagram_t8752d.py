#!/usr/bin/env python3
"""Ekstrak diagram T-8752D."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/t8752d-partslist.pdf"
OUT = Path("static/images/mechanisms/brother/t8752d")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 88

PAGE_TO_IDX = {
    1: 5, 3: 7, 5: 9, 9: 13, 11: 15, 13: 17, 15: 19, 17: 21,
    19: 23, 21: 25, 25: 29, 27: 31, 29: 33, 33: 37, 35: 39,
    37: 41, 41: 45, 43: 47, 45: 49, 47: 51, 49: 53, 51: 55,
    53: 57, 55: 59, 57: 61,
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT DISTINCT diagram_page FROM components WHERE machine_id=? ORDER BY diagram_page", (MID,))
pages = [r[0] for r in cur.fetchall()]
print(f"Pages: {len(pages)}")

for page in pages:
    idx = PAGE_TO_IDX.get(int(page))
    if idx is None or idx >= doc.page_count:
        print(f"[SKIP] page {page}")
        continue
    pix = doc[idx].get_pixmap(matrix=mat)
    out = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out))
    path = f"images/mechanisms/brother/t8752d/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/25")
conn.close()
