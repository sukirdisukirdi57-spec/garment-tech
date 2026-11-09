#!/usr/bin/env python3
"""Ekstrak diagram 3 mesin 430H series."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/430h-partslist.pdf"
DB = Path("database/garment.db")

MACHINES = [(109, "ke430hx"), (55, "ke430hs"), (106, "be438hx")]

PAGE_TO_IDX = {
    1: 5, 3: 7, 7: 11, 11: 15, 13: 17, 15: 19, 17: 21, 19: 23,
    21: 25, 23: 27, 25: 29, 27: 31, 29: 33, 31: 35, 33: 37,
    35: 39, 37: 41, 39: 43, 41: 45, 43: 47, 45: 49,
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

for MID, folder in MACHINES:
    print(f"\n=== {folder} ===")
    out_dir = Path(f"static/images/mechanisms/brother/{folder}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT diagram_page FROM components WHERE machine_id=? ORDER BY diagram_page", (MID,))
    pages = [r[0] for r in cur.fetchall()]
    
    for page in pages:
        idx = PAGE_TO_IDX.get(int(page))
        if idx is None or idx >= doc.page_count:
            print(f"  [SKIP] page {page}")
            continue
        pix = doc[idx].get_pixmap(matrix=mat)
        out = out_dir / f"pdf-page-{page}.jpg"
        pix.save(str(out))
        path = f"images/mechanisms/brother/{folder}/pdf-page-{page}.jpg"
        cur.execute("""UPDATE components SET image_path=?
                       WHERE machine_id=? AND diagram_page=?""", (path, MID, page))
    
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
    print(f"  image_path: {cur.fetchone()[0]}/{len(pages)}")
    conn.close()

doc.close()
