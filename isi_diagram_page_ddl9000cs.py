#!/usr/bin/env python3
"""Isi diagram_page di parts DDL-9000C-S berdasarkan section_ref."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB  = Path("database/garment.db")
MID = 17

SECTION_TO_PAGE = {
    1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15,
    9: 17, 10: 19, 11: 20, 12: 21, 13: 22, 14: 23, 16: 25,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-diagram-page-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

total = 0
for ref, page in SECTION_TO_PAGE.items():
    cur.execute("""UPDATE parts SET diagram_page=?
                   WHERE machine_id=? AND section_ref=?""",
                (page, MID, ref))
    total += cur.rowcount
    print(f"  section {ref} -> page {page}: {cur.rowcount} parts")

conn.commit()

cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=? AND diagram_page IS NOT NULL", (MID,))
print(f"\n[HASIL] parts dengan diagram_page: {cur.fetchone()[0]}/{total}")

conn.close()
