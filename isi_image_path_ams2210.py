#!/usr/bin/env python3
"""Update image_path AMS-210EN-2210."""
import sqlite3, shutil, glob
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 44

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-ams2210-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

avail = sorted(int(p.split('-')[-1].split('.')[0]) for p in glob.glob("static/images/mechanisms/juki/ams210en/pdf-page-*.jpg"))
print(f"Available pages: {len(avail)}")

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT id, diagram_page FROM components WHERE machine_id=? AND diagram_page IS NOT NULL", (MID,))
comps = cur.fetchall()

updated = 0
for cid, page in comps:
    path = f"images/mechanisms/juki/ams210en/pdf-page-{page}.jpg"
    if not (Path("static") / path).exists():
        nearest = min(avail, key=lambda p: abs(p - page))
        path = f"images/mechanisms/juki/ams210en/pdf-page-{nearest}.jpg"
    cur.execute("UPDATE components SET image_path=? WHERE id=?", (path, cid))
    updated += 1

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"[HASIL] image_path: {cur.fetchone()[0]}/{len(comps)}")
conn.close()
