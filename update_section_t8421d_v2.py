#!/usr/bin/env python3
"""Update section_ref & diagram_page T-8421D via part_number + CAST(catalog_ref)."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_t8421d_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 84

SECTIONS = {
    "A":  "A. Machine body", "B":  "B. Upper shaft mechanism",
    "C":  "C. Needle bar rocking mechanism", "D":  "D. Presser foot mechanism",
    "E":  "E. Feed mechanism", "F":  "F. Quick reverse mechanism",
    "G":  "G. Feed shaft mechanism", "H":  "H. Gauge parts",
    "J1": "J1. Rotary hook mechanism (T-8421D)", "J3": "J3. Rotary hook mechanism",
    "K":  "K. Lower shaft mechanism", "L":  "L. Lubrication",
    "M":  "M. Threading mechanism", "N":  "N. Bobbin winder mechanism",
    "P":  "P. Thread trimmer mechanism",
    "S1": "S1. Control box", "S2": "S2. Control box",
    "T":  "T. Quick reverse switch mechanism", "U":  "U. Operation panel",
    "V":  "V. Power supply equipment and motor mechanism",
    "Z1": "Z1. Accessories", "Z2": "Z2. Accessories",
}
SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-update-section-t8421d-v2-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

updated = 0
unmatched = 0
for r in rows:
    sec = r["section_ref"]
    if sec not in SECTION_ORDER: continue
    cur.execute("""UPDATE parts SET section_ref=?, section_name=?, diagram_page=?
                   WHERE machine_id=? AND part_number=? 
                     AND CAST(REPLACE(catalog_ref,'+','') AS INTEGER)=?""",
                (SECTION_ORDER[sec], SECTIONS[sec], int(r["diagram_page"]),
                 MID, r["part_number"], int(r["catalog_ref"])))
    if cur.rowcount > 0:
        updated += cur.rowcount
    else:
        unmatched += 1

conn.commit()
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=? AND section_ref IS NOT NULL", (MID,))
assigned = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
total = cur.fetchone()[0]
print(f"[UPDATE] updated={updated}, unmatched={unmatched}")
print(f"[HASIL] parts dengan section_ref: {assigned}/{total}")
conn.close()
