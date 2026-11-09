#!/usr/bin/env python3
"""Update image_path di components LK-1900S (semua section)."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 37

# section_ref -> diagram_page (semua 19 section)
SECTION_TO_PAGE = {
    1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15,
    9: 17, 10: 19, 11: 21, 12: 23, 14: 27, 15: 29, 16: 31,
    17: 33, 18: 35, 19: 37, 20: 39,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-lk1900s-v2-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for ref, page in SECTION_TO_PAGE.items():
    path = f"images/mechanisms/juki/lk1900s/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=?""",
                (path, MID, ref))
    print(f"  section {ref:>2} -> {path}")

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] components dengan image_path: {cur.fetchone()[0]}/19")
conn.close()
