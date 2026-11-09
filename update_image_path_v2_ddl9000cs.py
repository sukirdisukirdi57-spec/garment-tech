#!/usr/bin/env python3
"""Update image_path ke pola AMS: images/mechanisms/juki/ddl9000cs/pdf-page-N.jpg."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 17

SECTION_TO_PAGE = {
    1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15,
    9: 17, 10: 19, 11: 20, 12: 21, 13: 22, 14: 23, 16: 25,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-v2-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for ref, page in SECTION_TO_PAGE.items():
    path = f"images/mechanisms/juki/ddl9000cs/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=?""",
                (path, MID, ref))
    print(f"  section {ref:2d} -> {path}")

conn.commit()

cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] components dengan image_path: {cur.fetchone()[0]}/15")

# Verifikasi file fisik
import os
print("\n[VERIFIKASI FILE FISIK]")
missing = 0
for ref, page in SECTION_TO_PAGE.items():
    fpath = Path("static") / f"images/mechanisms/juki/ddl9000cs/pdf-page-{page}.jpg"
    if not fpath.exists():
        print(f"  MISSING: {fpath}")
        missing += 1
if missing == 0:
    print("  ✅ Semua file ada")

conn.close()
