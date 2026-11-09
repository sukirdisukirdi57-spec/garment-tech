#!/usr/bin/env python3
"""Update image_path LH-3528A."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 18

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-lh3528a-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT id, diagram_page FROM components WHERE machine_id=? AND diagram_page IS NOT NULL", (MID,))
comps = cur.fetchall()
updated = 0
for cid, page in comps:
    path = f"images/mechanisms/juki/lh3528a/pdf-page-{page}.jpg"
    f = Path("static") / path
    if f.exists():
        cur.execute("UPDATE components SET image_path=? WHERE id=?", (path, cid))
        updated += 1

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"[HASIL] image_path: {cur.fetchone()[0]}/{len(comps)}")
conn.close()
