#!/usr/bin/env python3
"""Update image_path di components LK-1900S."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 37

PAGES = {
    1: 1, 3: 3, 5: 5, 7: 7, 9: 9, 11: 11, 13: 13, 15: 15,
    17: 17, 19: 19, 21: 21, 23: 23, 27: 27, 29: 29, 31: 31,
    33: 33, 35: 35, 37: 37, 39: 39,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-lk1900s-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for ref, page in PAGES.items():
    path = f"images/mechanisms/juki/lk1900s/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=?""",
                (path, MID, ref))
    print(f"  section {ref:>2} -> {path}")

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] components dengan image_path: {cur.fetchone()[0]}/19")

# Verifikasi file fisik
print("\n[VERIFIKASI FILE]")
missing = 0
for page in PAGES.values():
    fpath = Path("static") / f"images/mechanisms/juki/lk1900s/pdf-page-{page}.jpg"
    if not fpath.exists():
        print(f"  MISSING: {fpath}")
        missing += 1
if missing == 0:
    print("  ✅ Semua file ada")

conn.close()
