#!/usr/bin/env python3
"""Update image_path T-8421D via component_name prefix."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 84

# prefix component_name -> page
PREFIX_TO_PAGE = {
    "A -": 1, "B -": 3, "C -": 5, "D -": 7, "E -": 9, "F -": 11, "G -": 13, "H -": 15,
    "J1 -": 17, "J3 -": 23, "K -": 25, "L -": 27, "M -": 31, "N -": 33, "P -": 35,
    "S1 -": 43, "S2 -": 45, "T -": 47, "U -": 49, "V -": 51, "Z1 -": 53, "Z2 -": 55,
    "Q.": 39, "R.": 41,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-t8421d-v2-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT id, component_name FROM components WHERE machine_id=?", (MID,))
rows = cur.fetchall()

updated = 0
missing_prefix = 0
for cid, name in rows:
    page = None
    for prefix, p in PREFIX_TO_PAGE.items():
        if name.startswith(prefix):
            page = p
            break
    if page is None:
        print(f"  [SKIP] {name}")
        missing_prefix += 1
        continue
    path = f"images/mechanisms/brother/t8421d/pdf-page-{page}.jpg"
    cur.execute("UPDATE components SET image_path=? WHERE id=?", (path, cid))
    updated += 1
    print(f"  {name} -> {path}")

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] ter-update: {updated}, skip: {missing_prefix}")
print(f"[TOTAL] image_path terisi: {cur.fetchone()[0]}/26")
conn.close()
