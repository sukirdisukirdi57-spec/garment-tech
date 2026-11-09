#!/usr/bin/env python3
"""Rebuild T-8722D (id=87) dari PDF Brother."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_t8722d_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 87
EXPECTED_MODEL = "T-8722D"

SECTIONS = {
    "A":  ("A. Machine body", "Badan mesin", 1),
    "B":  ("B. Upper shaft mechanism", "Upper shaft", 3),
    "C":  ("C. Needle bar rocking mechanism", "Needle bar rocking", 5),
    "D":  ("D. Presser foot mechanism", "Presser foot", 7),
    "E":  ("E. Feed mechanism", "Feed mechanism", 9),
    "F":  ("F. Quick reverse mechanism", "Quick reverse", 11),
    "G":  ("G. Feed shaft mechanism", "Feed shaft", 13),
    "H":  ("H. Gauge parts", "Gauge parts", 15),
    "J1": ("J1. Rotary hook mechanism (1)", "Rotary hook (1)", 17),
    "J2": ("J2. Rotary hook mechanism (2)", "Rotary hook (2)", 21),
    "K":  ("K. Lower shaft mechanism", "Lower shaft", 23),
    "L":  ("L. Lubrication", "Lubrication", 25),
    "M":  ("M. Threading mechanism", "Threading", 29),
    "N":  ("N. Bobbin winder mechanism", "Bobbin winder", 31),
    "P":  ("P. Thread trimmer mechanism", "Thread trimmer", 33),
    "Q":  ("Q. Tension release mechanism", "Tension release", 37),
    "R":  ("R. Thread wiper mechanism", "Thread wiper", 39),
    "S1": ("S1. Control box (1)", "Control box (1)", 41),
    "S2": ("S2. Control box (2)", "Control box (2)", 43),
    "T":  ("T. Quick reverse switch", "Quick reverse switch", 45),
    "U":  ("U. Operation panel", "Operation panel", 47),
    "V":  ("V. Power supply & motor", "Power supply & motor", 49),
    "Z1": ("Z1. Accessories (1)", "Accessories (1)", 51),
    "Z2": ("Z2. Accessories (2)", "Accessories (2)", 53),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-t8722d-{ts}")
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
cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
print("[HAPUS] data lama")

with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    qty_clean = r["quantity"].strip("()")
    try:
        qty = int(float(qty_clean)) if qty_clean else None
    except ValueError:
        qty = None
    sec = r["section_ref"]
    sec_num = SECTION_ORDER[sec]
    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page, section_ref, section_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (MID, r["part_number"], r["part_name"], qty,
                 int(r["catalog_ref"]), int(r["diagram_page"]),
                 sec_num, SECTIONS[sec][0]))

for sec, (name, loc, page) in SECTIONS.items():
    sec_num = SECTION_ORDER[sec]
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY catalog_ref LIMIT 1""", (MID, sec_num))
    r = cur.fetchone()
    main_pn = r[0] if r else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, loc, str(sec_num), page))

conn.commit()

cur.execute("SELECT id, catalog_ref, part_number FROM components WHERE machine_id=?", (MID,))
comps = {int(r[1]): (r[0], r[2]) for r in cur.fetchall()}
total = 0
for ref, (comp_id, comp_pn) in sorted(comps.items()):
    cur.execute("SELECT id, part_number FROM parts WHERE machine_id=? AND section_ref=?", (MID, ref))
    for pid, pn in cur.fetchall():
        rel = "matched_catalog_part" if pn == comp_pn else "sub-part"
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,?)""", (comp_id, pid, rel))
            total += 1
        except sqlite3.IntegrityError:
            pass

conn.commit()
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
print(f"[PARTS] {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[KOMPONEN] {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[RELASI] {cur.fetchone()[0]}")
conn.close()
