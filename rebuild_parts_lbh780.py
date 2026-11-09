#!/usr/bin/env python3
"""Rebuild parts LBH-780 (id=39) dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_lbh780_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 39
EXPECTED_MODEL = "LBH-780"

SECTIONS = {
    1:  "1. LBH-772NV-1,LBH-782NV (1)",
    2:  "2. LBH-772NV-1,LBH-782NV (2)",
    3:  "3. LBH-772NV-1,LBH-782NV (3)",
    4:  "4. LBH-773NV-1,LBH-783NV",
    5:  "5. LBH-774NV-1,LBH-784NV",
    6:  "6. LBH-772NB-1,LBH-782NB",
    7:  "7. LBH-773NB-1,LBH-783NB",
    8:  "8. LBH-774NB-1,LBH-784NB",
    9:  "9. THREAD STAND COMPONENTS",
    10: "10. LBH-77*NV1-1,NB1-1,LBH-78*NV1,NB1 (SEMI-CIRCULAR BARTACKING)",
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-parts-lbh780-{ts}")
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
