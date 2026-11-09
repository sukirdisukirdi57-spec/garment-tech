#!/usr/bin/env python3
"""Rebuild parts T-8422D (id=85) dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_t8422d_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 85
EXPECTED_MODEL = "T-8422D"

SECTIONS = {
    "A":  "A. Machine body",
    "B":  "B. Upper shaft mechanism",
    "C":  "C. Needle bar rocking mechanism",
    "D":  "D. Presser foot mechanism",
    "E":  "E. Feed mechanism",
    "F":  "F. Quick reverse mechanism",
    "G":  "G. Feed shaft mechanism",
    "H":  "H. Gauge parts",
    "J2": "J2. Rotary hook mechanism (T-8422D)",
    "J3": "J3. Rotary hook mechanism",
    "K":  "K. Lower shaft mechanism",
    "L":  "L. Lubrication",
    "M":  "M. Threading mechanism",
    "N":  "N. Bobbin winder mechanism",
    "P":  "P. Thread trimmer mechanism",
    "Q":  "Q. Tension release mechanism (T-8422D)",
    "R":  "R. Thread wiper mechanism (T-8422D)",
    "S1": "S1. Control box",
    "S2": "S2. Control box",
    "T":  "T. Quick reverse switch mechanism",
    "U":  "U. Operation panel",
    "V":  "V. Power supply equipment and motor mechanism",
    "Z1": "Z1. Accessories",
    "Z2": "Z2. Accessories",
}

# section -> urutan angka (untuk catalog_ref di components)
SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-parts-t8422d-{ts}")
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
                 SECTION_ORDER.get(r["section_ref"]),
                 SECTIONS.get(r["section_ref"])))

conn.commit()
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
print(f"[HASIL] parts sekarang: {cur.fetchone()[0]}")
conn.close()
