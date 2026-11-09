#!/usr/bin/env python3
"""Ekstrak diagram PS-800 (37 section)."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "ps800-parts.pdf"
OUT = Path("static/images/mechanisms/juki/ps800")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 11

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT DISTINCT diagram_page FROM components WHERE machine_id=? ORDER BY diagram_page", (MID,))
pages = [r[0] for r in cur.fetchall()]
print(f"Pages: {len(pages)}")

for page in pages:
    # diagram page N -> PDF index N+4
    idx = int(page) + 4
    if idx >= doc.page_count:
        print(f"[SKIP] page {page}")
        continue
    pix = doc[idx].get_pixmap(matrix=mat)
    out = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out))
    print(f"[OK] page {page} -> PDF hal {idx+1}")
    path = f"images/mechanisms/juki/ps800/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

doc.close()
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/37")
conn.close()
