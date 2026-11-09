#!/usr/bin/env python3
"""Ekstrak diagram KE-430DP & BE-438DP."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/pdf-baru/ke430dp_be438dp-partslist.pdf"
DB = Path("database/garment.db")

MACHINES = [(111, "ke430dp"), (108, "be438dp")]

# diagram_page -> PDF index (0-based)
PAGE_TO_IDX = {
    1: 3, 3: 5, 5: 7, 9: 11, 11: 13, 13: 15, 15: 17,
    17: 19, 19: 21, 23: 25, 25: 27, 27: 29, 29: 31, 31: 33,
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
