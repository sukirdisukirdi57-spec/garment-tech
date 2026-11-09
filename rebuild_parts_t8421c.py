#!/usr/bin/env python3
"""Rebuild parts T-8421C (id=89) dari CSV scrape."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_t8421c_hasil_scrape.csv")
DB  = Path("database/garment.db")
MID = 89
EXPECTED_MODEL = "T-8421C"

SECTION_TO_PAGE = {
    1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15, 9: 17,
    10: 23, 11: 25, 12: 27, 13: 31, 14: 33, 15: 35, 16: 43, 17: 45,
    18: 47, 19: 49, 20: 51, 21: 53, 22: 55, 23: 57, 24: 58, 25: 59, 26: 60,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-parts-t8421c-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
row = cur.fetchone()
if not row or row[0] != EXPECTED_MODEL:
    raise SystemExit(f"BATAL: machine_id={MID} bukan {EXPECTED_MODEL} (dapat: {row})")

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
    sec = int(r["section_ref"])
    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page, section_ref, section_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (MID, r["part_number"], r["part_name"], qty,
                 int(r["catalog_ref"]), SECTION_TO_PAGE.get(sec),
                 sec, r["section_name"]))

conn.commit()
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
print(f"[HASIL] parts sekarang: {cur.fetchone()[0]}")
conn.close()
