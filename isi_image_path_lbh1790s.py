#!/usr/bin/env python3
"""Update image_path di components LBH-1790S."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 38

SECTION_TO_PAGE = {
    1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15,
    9: 17, 10: 19, 11: 21, 12: 23, 14: 27, 15: 29, 16: 31,
    17: 33, 18: 35,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-lbh1790s-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for ref, page in SECTION_TO_PAGE.items():
    path = f"images/mechanisms/juki/lbh1790s/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=?""",
                (path, MID, ref))
    print(f"  section {ref:>2} -> {path}")

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path terisi: {cur.fetchone()[0]}/17")

# Verifikasi file fisik
missing = 0
for page in SECTION_TO_PAGE.values():
    f = Path("static") / f"images/mechanisms/juki/lbh1790s/pdf-page-{page}.jpg"
    if not f.exists():
        print(f"  MISSING: {f}")
        missing += 1
print("✅ Semua file ada" if missing == 0 else f"❌ {missing} file hilang")

conn.close()
