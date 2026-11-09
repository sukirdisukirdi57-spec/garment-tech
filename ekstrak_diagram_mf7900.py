#!/usr/bin/env python3
"""Ekstrak diagram MF-7900 series."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/mf7900-partslist.pdf"
DB = Path("database/garment.db")

MACHINES = [(31, "mf7900h11"), (30, "mf7900u11")]

PAGE_TO_IDX = {
    1: 3, 3: 5, 5: 7, 7: 9, 9: 11, 11: 13, 13: 15, 14: 15,
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
