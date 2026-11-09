#!/usr/bin/env python3
"""Ekstrak diagram EX2200."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/pegasus-EX2200_9B6006.pdf"
OUT = Path("static/images/mechanisms/pegasus/ex2200")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 212

# diagram_page -> PDF index (0-based)
PAGE_TO_IDX = {
    2: 5, 4: 7, 6: 9, 8: 11, 10: 13, 12: 15, 14: 17, 16: 19,
    18: 21, 20: 23, 22: 25, 24: 27, 26: 29, 28: 31, 30: 33,
    32: 35, 34: 37, 36: 39, 38: 41, 40: 43, 42: 45, 44: 47,
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
    path = f"images/mechanisms/pegasus/ex2200/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/22")
conn.close()
