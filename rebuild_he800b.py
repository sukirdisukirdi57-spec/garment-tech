#!/usr/bin/env python3
"""Rebuild HE-800B (id=102) dari PDF Brother."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_he800b_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 103
EXPECTED_MODEL = "HE-800B"

SECTIONS = {
    "A":  ("A. Machine body", "Badan mesin", 1),
    "B":  ("B. Needle bar & thread take-up", "Needle bar & take-up", 3),
    "C":  ("C. Upper shaft mechanism", "Upper shaft", 5),
    "D":  ("D. Zigzag mechanism", "Zigzag mechanism", 7),
    "E":  ("E. Emergency stop mechanism", "Emergency stop", 9),
    "F":  ("F. Presser foot mechanism", "Presser foot", 11),
    "G":  ("G. Feed mechanism", "Feed mechanism", 13),
    "H":  ("H. Cutter mechanism", "Cutter mechanism", 15),
    "J":  ("J. Thread breakage detector", "Thread breakage detector", 17),
    "K":  ("K. Rotary hook mechanism", "Rotary hook", 19),
    "L":  ("L. Lower shaft mechanism", "Lower shaft", 21),
    "M":  ("M. Lubrication", "Lubrication", 23),
    "N":  ("N. Threading mechanism", "Threading", 27),
    "P":  ("P. Bobbin winder mechanism", "Bobbin winder", 31),
    "Q":  ("Q. Upper thread trimmer", "Upper thread trimmer", 33),
    "R":  ("R. Lower thread trimmer", "Lower thread trimmer", 35),
    "S1": ("S1. Control box", "Control box (1)", 39),
    "S2": ("S2. Control box", "Control box (2)", 41),
    "T":  ("T. Power supply equipment", "Power supply", 43),
    "U":  ("U. Operation panel", "Operation panel", 45),
    "V":  ("V. Motor mechanism", "Motor mechanism", 47),
    "W":  ("W. Attachment set", "Attachment set", 49),
    "Z":  ("Z. Accessories", "Accessories", 51),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-he800b-{ts}")
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
