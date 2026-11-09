#!/usr/bin/env python3
"""Ekstrak diagram LZ-2290A."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/lz2290a-partslist.pdf"
OUT = Path("static/images/mechanisms/juki/lz2290a")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 36

# diagram_page -> PDF index (0-based)
PAGE_TO_IDX = {
    1: 5, 3: 7, 5: 9, 7: 11, 9: 13, 11: 15, 13: 17, 15: 19,
    17: 21, 19: 23, 21: 25, 23: 27, 25: 28, 26: 29, 27: 30,
    28: 31, 29: 32, 31: 34, 33: 36, 35: 38, 37: 40, 39: 42,
    40: 43, 41: 44, 43: 46, 45: 48, 46: 49, 47: 50, 48: 51,
    49: 52, 51: 54, 53: 56, 55: 58, 56: 59,
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
    path = f"images/mechanisms/juki/lz2290a/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/34")
conn.close()
