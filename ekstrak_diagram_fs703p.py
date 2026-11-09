#!/usr/bin/env python3
"""Ekstrak diagram FS703P."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/pegasus2-FS703_9B6007.pdf"
OUT = Path("static/images/mechanisms/pegasus/fs703p")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 194

# diagram_page -> PDF index (0-based). page N -> idx N+2
PAGE_TO_IDX = {p: p+2 for p in range(2, 39, 2)}

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
    path = f"images/mechanisms/pegasus/fs703p/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/18")
conn.close()
