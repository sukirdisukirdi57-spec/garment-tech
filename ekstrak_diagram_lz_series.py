#!/usr/bin/env python3
"""Ekstrak diagram LZ-2280A, LZ-2284A, LZ-2287A."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/lz2280a-partslist.pdf"
DB = Path("database/garment.db")

MACHINES = [
    (10, "lz2280a"), (33, "lz2284a"), (34, "lz2287a"),
]

PAGE_TO_IDX = {
    1: 5, 3: 7, 5: 9, 7: 11, 8: 11, 9: 13, 11: 15, 13: 17, 14: 18,
    15: 19, 17: 21, 19: 23, 20: 24, 21: 25, 22: 26, 23: 27, 24: 28,
    25: 29, 26: 30, 27: 31,
}

doc = pymupdf.open(PDF)
zoom = 150 / 72
mat = pymupdf.Matrix(zoom, zoom)

for MID, folder in MACHINES:
    print(f"\n=== {folder} ===")
    out_dir = Path(f"static/images/mechanisms/juki/{folder}")
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
        path = f"images/mechanisms/juki/{folder}/pdf-page-{page}.jpg"
        cur.execute("""UPDATE components SET image_path=?
                       WHERE machine_id=? AND diagram_page=?""", (path, MID, page))
    
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
    print(f"  image_path: {cur.fetchone()[0]}/{len(pages)}")
    conn.close()

doc.close()
