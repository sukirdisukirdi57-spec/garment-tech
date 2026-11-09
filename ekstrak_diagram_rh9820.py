#!/usr/bin/env python3
"""Ekstrak diagram RH-9820."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/rh9820-partslist.pdf"
OUT = Path("static/images/mechanisms/brother/rh9820")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 105

# diagram_page -> PDF index (0-based)
PAGE_TO_IDX = {
    1: 5, 5: 9, 7: 11, 9: 13, 11: 15, 13: 17, 17: 21, 19: 23,
    21: 25, 25: 29, 27: 31, 29: 33, 31: 35, 35: 39, 37: 41,
    41: 45, 45: 49, 47: 51, 49: 53, 51: 55, 53: 57, 55: 59,
    59: 63, 61: 65, 63: 67, 65: 69, 67: 71, 69: 73, 71: 75,
    73: 77, 79: 83, 81: 85, 83: 87, 89: 93, 93: 97, 95: 99,
    97: 101, 101: 105, 105: 109, 109: 113,
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
    path = f"images/mechanisms/brother/rh9820/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/41")
conn.close()
