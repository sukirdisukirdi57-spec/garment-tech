#!/usr/bin/env python3
"""Insert parts LK-1900S (id=37) dari CSV + section + diagram_page."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_lk1900s_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 37
EXPECTED_MODEL = "LK-1900S"

SECTIONS = {
    1:  "1. FRAME & MISCELLANEOUS COVER COMPONENTS",
    2:  "2. MAIN SHAFT & NEEDLE BAR COMPONENTS",
    3:  "3. PRESSER LIFTER & WIPER COMPONENTS",
    4:  "4. SHUTTLE DRIVER SHAFT COMPONENTS",
    5:  "5. THREAD TENSION COMPONENTS",
    6:  "6. THREAD TRIMMER MECHANISM COMPONENTS",
    7:  "7. FEED MECHANISM COMPONENTS",
    8:  "8. SENSOR COMPONENTS",
    9:  "9. THREAD STAND COMPONENTS",
    10: "10. TABLE STAND COMPONENTS (JT-K46)",
    11: "11. CONTROL BOX COMPONENTS",
    12: "12. OPERATION PANEL COMPONENTS",
    14: "14. ACCESSORIE PARTS COMPONENTS",
    15: "15. EXCLUSIVE PARTS FOR LK-1903SS-301,LK-1903SS-302(1)",
    16: "16. EXCLUSIVE PARTS FOR LK-1903SS-301,LK-1903SS-302(2)",
    17: "17. ACCESSORIE PARTS FOR LK-1900S SUBCLASSES",
    18: "18. OPTION COMPONENTS (1)",
    19: "19. OPTION COMPONENTS (2) (FOR LK-1903S)",
    20: "20. OPTION COMPONENTS (3) (FOR LK-1903S SHANK BUTTON)",
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-parts-lk1900s-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
row = cur.fetchone()
if not row or row[0] != EXPECTED_MODEL:
    raise SystemExit(f"BATAL: machine_id={MID} bukan {EXPECTED_MODEL} (dapat: {row})")

cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
before = cur.fetchone()[0]
print(f"[CEK] parts sebelum: {before}")
if before > 0:
    raise SystemExit("BATAL: parts sudah ada, tidak mau duplikat")

with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

inserted = 0
for r in rows:
    qty_raw = r["quantity"]
    qty_clean = qty_raw.strip("()")  # buang kurung
    try:
        qty = int(float(qty_clean)) if qty_clean else None
    except ValueError:
        qty = None

    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page, section_ref, section_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (MID, r["part_number"], r["part_name"], qty,
                 int(r["catalog_ref"]) if r["catalog_ref"] else None,
                 int(r["diagram_page"]) if r["diagram_page"] else None,
                 int(r["section_ref"]) if r["section_ref"] else None,
                 SECTIONS.get(int(r["section_ref"])) if r["section_ref"] else None))
    inserted += 1

conn.commit()
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
after = cur.fetchone()[0]
print(f"[CEK] parts sesudah: {after}")
print(f"[HASIL] inserted={inserted}, selisih={after-before}")

conn.close()
