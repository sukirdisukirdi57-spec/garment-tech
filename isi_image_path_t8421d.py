#!/usr/bin/env python3
"""Update image_path T-8421D."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 84

SECTION_TO_PAGE = {
    1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15,
    9: 17, 10: 23, 11: 25, 12: 27, 13: 31, 14: 33, 15: 35,
    16: 39, 17: 41, 18: 43, 19: 45, 20: 47, 21: 49, 22: 51,
    23: 53, 24: 55,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-t8421d-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for ref, page in SECTION_TO_PAGE.items():
    path = f"images/mechanisms/brother/t8421d/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=?""",
                (path, MID, ref))

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"[HASIL] image_path terisi: {cur.fetchone()[0]}/26")

missing = 0
for page in SECTION_TO_PAGE.values():
    f = Path("static") / f"images/mechanisms/brother/t8421d/pdf-page-{page}.jpg"
    if not f.exists():
        print(f"  MISSING: {f}")
        missing += 1
print("✅ Semua file ada" if missing == 0 else f"❌ {missing} file hilang")
conn.close()
