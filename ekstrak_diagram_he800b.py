#!/usr/bin/env python3
"""Ekstrak diagram HE-800B."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/he800b-partslist.pdf"
OUT = Path("static/images/mechanisms/brother/he800b")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 103

# diagram_page -> PDF index (0-based)
PAGE_TO_IDX = {
    1: 3, 3: 5, 5: 7, 7: 9, 9: 11, 11: 13, 13: 15, 15: 17,
    17: 19, 19: 21, 21: 23, 23: 25, 27: 29, 31: 33, 33: 35,
    35: 37, 39: 41, 41: 43, 43: 45, 45: 47, 47: 49, 49: 51, 51: 53,
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
    path = f"images/mechanisms/brother/he800b/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/23")
conn.close()
