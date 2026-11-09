#!/usr/bin/env python3
"""Update image_path LBH-780."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 39

SECTION_TO_PAGE = {
    1: 1, 2: 3, 3: 5, 4: 7, 5: 8, 6: 9, 7: 11, 8: 12, 9: 13, 10: 15,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-lbh780-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for ref, page in SECTION_TO_PAGE.items():
    path = f"images/mechanisms/juki/lbh780/pdf-page-{page}.jpg"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=?""",
                (path, MID, ref))
    print(f"  section {ref:>2} -> {path}")

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"\n[HASIL] image_path terisi: {cur.fetchone()[0]}/10")

missing = 0
for page in SECTION_TO_PAGE.values():
    f = Path("static") / f"images/mechanisms/juki/lbh780/pdf-page-{page}.jpg"
    if not f.exists():
        print(f"  MISSING: {f}")
        missing += 1
print("✅ Semua file ada" if missing == 0 else f"❌ {missing} file hilang")
conn.close()
