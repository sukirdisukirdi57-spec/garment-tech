#!/usr/bin/env python3
"""Ekstrak diagram E256."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/pegasus-E256_95460_1.pdf"
OUT = Path("static/images/mechanisms/pegasus/e256")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 213

# diagram_page -> PDF index (0-based). diagram page N -> idx N+2
PAGE_TO_IDX = {
    2: 3, 4: 5, 6: 7, 8: 9, 10: 11, 12: 13, 14: 15, 16: 17,
    18: 19, 20: 21, 22: 23, 24: 25, 26: 27, 28: 29, 30: 31,
    32: 33, 34: 35, 36: 37, 38: 39, 40: 41, 42: 43, 44: 45,
    46: 47, 48: 49, 50: 51,
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
    path = f"images/mechanisms/pegasus/e256/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/25")
conn.close()
