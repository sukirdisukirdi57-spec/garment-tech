#!/usr/bin/env python3
"""Update image_path DDL-7000A."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 4

PAGE_TO_FILE = {
    2:  "section-01-frame_miscellaneous.png",
    4:  "section-02-bobbin_winder.png",
    6:  "section-03-main_shaft.png",
    8:  "section-04-needle_bar.png",
    10: "section-05-hand_lifter.png",
    12: "section-06-feed_mechanism.png",
    14: "section-07-thread_trimmer.png",
    15: "section-08-automatic_reverse.png",
    16: "section-09-exclusive_parts_nb.png",
    18: "section-10-oil_lubrication.png",
    20: "section-11-oil_reservoir.png",
    21: "section-12-accessories.png",
    22: "section-13-thread_stand.png",
    23: "section-14-psc_unit.png",
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-image-path-ddl7000a-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for page, fname in PAGE_TO_FILE.items():
    path = f"images/mechanisms/juki/ddl7000a/{fname}"
    cur.execute("""UPDATE components SET image_path=?
                   WHERE machine_id=? AND diagram_page=?""", (path, MID, page))

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND image_path IS NOT NULL", (MID,))
print(f"[HASIL] image_path: {cur.fetchone()[0]}/31")

missing = 0
for page, fname in PAGE_TO_FILE.items():
    f = Path("static") / f"images/mechanisms/juki/ddl7000a/{fname}"
    if not f.exists():
        print(f"  MISSING: {f}")
        missing += 1
print("✅ Semua file ada" if missing == 0 else f"❌ {missing} hilang")
conn.close()
