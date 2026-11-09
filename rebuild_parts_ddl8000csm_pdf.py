#!/usr/bin/env python3
"""Rebuild parts DDL-8000CSM (id=225) dari CSV PDF parse."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_ddl8000c_pdf_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 225
EXPECTED_MODEL = "DDL-8000CSM"

SECTIONS = {
    1:  "1. MACHINE FRAME & MISCELLANEOUS COVER COMPONENTS",
    2:  "2. UPPER SHAFT AND PICK LINE COMPONENTS",
    3:  "3. NEEDLE BAR & THREAD TENSION COMPONENTS",
    4:  "4. HAND LIFTER COMPONENTS",
    5:  "5. UPRIGHT SHAFT & HOOK DRIVING SHAFT COMPONENTS",
    6:  "6. FEED MECHANISM COMPONENTS",
    7:  "7. FEED ADJUST MECHANISM COMPONENTS",
    8:  "8. THREAD TRIMMER COMPONENTS",
    9:  "9. AUTOMATIC REVERSE FEED & NB COMPONENTS",
    10: "10. OIL LUBRICATION COMPONENTS",
    11: "11. OIL SHIELD COMPONENTS",
    12: "12. THREAD STAND COMPONENTS",
    13: "13. ACCESSORIE PART COMPONENTS",
    14: "14. FOR DDL-8000C-SC,SH",
    15: "15. OPTION CLOTH PRESS SENSOR DEVICE",
    16: "16. OPTION ONE TOUCH PRESSER DEVICE",
    17: "17. OPTION LONG PITCH DEVICE",
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-parts-ddl8000csm-pdf-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
row = cur.fetchone()
if not row or row[0] != EXPECTED_MODEL:
    raise SystemExit(f"BATAL: machine_id={MID} bukan {EXPECTED_MODEL}")

cur.execute("""DELETE FROM component_parts WHERE component_id IN
               (SELECT id FROM components WHERE machine_id=?)""", (MID,))
print(f"[HAPUS] relasi: {cur.rowcount}")

cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
print(f"[HAPUS] parts lama: {cur.rowcount}")

with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    qty_clean = r["quantity"].strip("()")
    try:
        qty = int(float(qty_clean)) if qty_clean else None
    except ValueError:
        qty = None

    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page, section_ref, section_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (MID, r["part_number"], r["part_name"], qty,
                 int(r["catalog_ref"]),
                 int(r["diagram_page"]),
                 int(r["section_ref"]),
                 SECTIONS.get(int(r["section_ref"]))))

conn.commit()
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
print(f"[HASIL] parts sekarang: {cur.fetchone()[0]}")
conn.close()
