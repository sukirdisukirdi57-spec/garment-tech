#!/usr/bin/env python3
"""Update image_path untuk 6 mesin seri C."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINES = [
    (95, "t8450c"), (91, "t8452c"), (96, "t8720c"),
    (92, "t8722c"), (97, "t8750c"), (93, "t8752c"),
]

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-batch-seric-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for db_id, model_folder in MACHINES:
    print(f"=== {model_folder} ===")
    cur.execute("SELECT id, catalog_ref FROM components WHERE machine_id=?", (db_id,))
    comps = cur.fetchall()
    updated = 0
    missing = 0
    for comp_id, ref in comps:
        path = f"images/mechanisms/brother/{model_folder}/section-{int(ref):02d}.svg"
        f = Path("static") / path
        if not f.exists():
            missing += 1
            continue
        cur.execute("UPDATE components SET image_path=? WHERE id=?", (path, comp_id))
        updated += 1
    conn.commit()
    print(f"  updated: {updated}, missing: {missing}")
    cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (db_id,))
    print(f"  total image_path: {cur.fetchone()[0]}/{len(comps)}")

conn.close()
print("\n[SELESAI]")
