#!/usr/bin/env python3
"""Ekstrak diagram RH-982A."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/rh982a-partslist.pdf"
OUT = Path("static/images/mechanisms/brother/rh982a")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 104

PAGE_TO_IDX = {
    1: 5, 5: 9, 9: 13, 11: 15, 13: 17, 15: 19, 19: 23, 21: 25,
    23: 27, 27: 31, 29: 33, 31: 35, 33: 37, 37: 41, 39: 43,
    43: 47, 47: 51, 49: 53, 51: 55, 53: 57, 55: 59, 57: 61,
    59: 63, 61: 65, 63: 67, 65: 69, 67: 71, 69: 73, 71: 75,
    73: 77, 79: 83, 81: 85, 83: 87, 89: 93, 91: 95, 93: 97,
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
    path = f"images/mechanisms/brother/rh982a/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/36")
conn.close()
