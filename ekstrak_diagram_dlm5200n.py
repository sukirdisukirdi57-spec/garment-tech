#!/usr/bin/env python3
"""Ekstrak diagram DLM-5200N."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "dlm5200n-partslist.pdf"
OUT = Path("static/images/mechanisms/juki/dlm5200n")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path("database/garment.db")
MID = 222

PAGE_TO_IDX = {
    1: 3, 3: 5, 5: 7, 7: 9, 9: 11, 11: 13, 13: 15, 15: 17,
    17: 19, 18: 20,
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT DISTINCT diagram_page FROM components WHERE machine_id=? ORDER BY diagram_page", (MID,))
pages = [r[0] for r in cur.fetchall()]
print(f"Pages: {pages}")

for page in pages:
    idx = PAGE_TO_IDX.get(int(page))
    if idx is None or idx >= doc.page_count:
        print(f"[SKIP] page {page}")
        continue
    pix = doc[idx].get_pixmap(matrix=mat)
    out = OUT / f"pdf-page-{page}.jpg"
    pix.save(str(out))
    print(f"[OK] page {page} -> PDF hal {idx+1} -> {out.name}")

doc.close()

for page in pages:
    path = f"images/mechanisms/juki/dlm5200n/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))
conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path: {cur.fetchone()[0]}/10")
conn.close()
