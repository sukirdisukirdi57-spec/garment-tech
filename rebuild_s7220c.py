#!/usr/bin/env python3
"""Rebuild S-7220C (id=73) dari PDF Brother."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_s7220c_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 73
EXPECTED_MODEL = "S-7220C"

SECTIONS = {
    "A":  ("A. Machine body", "Badan mesin", 1),
    "B1": ("B1. Needle bar & thread take-up (1)", "Needle bar & take-up (1)", 3),
    "B2": ("B2. Needle bar & thread take-up (2)", "Needle bar & take-up (2)", 7),
    "C":  ("C. Needle feed mechanism", "Needle feed", 9),
    "D":  ("D. Presser foot mechanism", "Presser foot", 13),
    "E":  ("E. Feed mechanism", "Feed mechanism", 15),
    "F":  ("F. Knee lifter mechanism", "Knee lifter", 19),
    "G":  ("G. Quick reverse mechanism", "Quick reverse", 21),
    "H":  ("H. Rotary hook mechanism", "Rotary hook", 23),
    "J":  ("J. Lubrication", "Lubrication", 25),
    "K":  ("K. Threading mechanism", "Threading", 29),
    "L":  ("L. Bobbin winder mechanism", "Bobbin winder", 31),
    "M":  ("M. Thread trimmer mechanism", "Thread trimmer", 33),
    "N":  ("N. Tension release mechanism", "Tension release", 37),
    "P":  ("P. Thread wiper mechanism", "Thread wiper", 39),
    "Q1": ("Q1. Operation panel & motor", "Operation panel & motor", 41),
    "Q2": ("Q2. Control box", "Control box", 43),
    "R":  ("R. Quick reverse switch", "Quick reverse switch", 45),
    "S":  ("S. Power supply equipment", "Power supply", 47),
    "Z":  ("Z. Accessories", "Accessories", 49),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-s7220c-{ts}")
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
