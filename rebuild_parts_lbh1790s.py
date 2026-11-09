#!/usr/bin/env python3
"""Rebuild parts LBH-1790S (id=38): hapus lama, insert baru dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_lbh1790s_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 38
EXPECTED_MODEL = "LBH-1790S"

SECTIONS = {
    1:  "1. FRAME & MISCELLANEOUS COVER COMPONENTS (1)",
    2:  "2. FRAME & MISCELLANEOUS COVER COMPONENTS (2)",
    3:  "3. MAIN SHAFT COMPONENTS",
    4:  "4. HOOK DRIVING SHAFT COMPONENTS",
    5:  "5. PRESSER & FEED COMPONENTS",
    6:  "6. NEEDLE BAR ROCKING COMPONENTS",
    7:  "7. NEEDLE THREAD TRIMMER COMPONENTS",
    8:  "8. BOBBIN THREAD TRIMMER COMPONENTS",
    9:  "9. CLOTH CUTTING KNIFE COMPONENTS",
    10: "10. TABLE COMPONENTS",
    11: "11. OPERATION BOX COMPONENTS (ACCESSORIES OF A CONTROL BOX)",
    12: "12. CONTROL BOX COMPONENTS",
    14: "14. ACCESSORIE PARTS COMPONENTS",
    15: "15. THREAD STAND COMPONENTS",
    16: "16. SPECIAL SPECIFICATIONS COMPONENTS (1)",
    17: "17. SPECIAL SPECIFICATIONS COMPONENTS (2)",
    18: "18. EXCHANGING PARTS",
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-parts-lbh1790s-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
row = cur.fetchone()
if not row or row[0] != EXPECTED_MODEL:
    raise SystemExit(f"BATAL: machine_id={MID} bukan {EXPECTED_MODEL}")

# Hapus relasi komponen yang ada (jika ada)
cur.execute("""DELETE FROM component_parts WHERE component_id IN
               (SELECT id FROM components WHERE machine_id=?)""", (MID,))
print(f"[HAPUS] relasi component_parts: {cur.rowcount}")

# Hapus parts lama
cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
print(f"[HAPUS] parts lama: {cur.rowcount}")

# Insert baru
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
