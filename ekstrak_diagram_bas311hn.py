#!/usr/bin/env python3
"""Ekstrak diagram 3 mesin BAS-311HN/326H."""
import pymupdf, sqlite3
from pathlib import Path

PDF = "tmp/bas311hn/bas311hn_326h_pb.pdf"
DB = Path("database/garment.db")

MACHINES = [(227, "bas311hn-03s"), (113, "bas311hx"), (114, "bas326hx")]

# diagram_page -> PDF index (0-based)
# diagram page N -> idx N-1 (karena page 1 = idx 0, tapi diagram A di idx 5 = page 6?)
# Sebenarnya: diagram A di PDF page 6 (index 5), diagram B di page 8 (index 7), dst.
# Formula: idx = (N - 1) + 5 = N + 4 (karena diagram A page 1 di index 5)
PAGE_TO_IDX = {}
for page in [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 35, 37, 39, 43, 45, 47, 49, 51, 53, 61, 67, 69]:
    PAGE_TO_IDX[page] = page + 4

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
