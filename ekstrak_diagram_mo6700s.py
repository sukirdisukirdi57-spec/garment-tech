#!/usr/bin/env python3
"""Ekstrak diagram MO-6700S."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/juki-mo6700s/partslist.pdf"
OUT = Path("static/images/mechanisms/juki/mo6700s")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 5

# diagram_page -> PDF index (0-based)
PAGE_TO_IDX = {
    1: 3, 3: 5, 5: 7, 7: 9, 9: 11, 11: 13, 13: 15, 15: 17,
    16: 18, 17: 19, 19: 21, 21: 23, 23: 25, 24: 26, 25: 27,
    27: 29, 28: 30, 29: 31, 31: 33, 33: 35, 35: 37, 37: 39,
    39: 41, 41: 43,
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
    print(f"[OK] page {page} -> PDF hal {idx+1}")
    path = f"images/mechanisms/juki/mo6700s/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/24")
conn.close()
