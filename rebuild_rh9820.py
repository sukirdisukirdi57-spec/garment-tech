#!/usr/bin/env python3
"""Rebuild RH-9820 (id=105) dari PDF Brother."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_rh9820_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 105
EXPECTED_MODEL = "RH-9820"

SECTIONS = {
    "A":  ("A. Machine body", "Badan mesin", 1),
    "B":  ("B. Needle bar & thread take-up", "Needle bar & take-up", 5),
    "C":  ("C. Upper shaft mechanism", "Upper shaft", 7),
    "D":  ("D. Zigzag mechanism", "Zigzag mechanism", 9),
    "E":  ("E. Needle bar rocking mechanism", "Needle bar rocking", 11),
    "F1": ("F1. Work clamp mechanism (1)", "Work clamp (1)", 13),
    "F2": ("F2. Work clamp mechanism (2)", "Work clamp (2)", 17),
    "F3": ("F3. Work clamp mechanism (3)", "Work clamp (3)", 19),
    "G":  ("G. Feed mechanism", "Feed mechanism", 21),
    "H":  ("H. Cutter mechanism", "Cutter mechanism", 25),
    "J":  ("J. Lower shaft mechanism", "Lower shaft", 27),
    "K":  ("K. Looper mechanism", "Looper mechanism", 29),
    "L":  ("L. Double chain stitch looper", "Double chain stitch looper", 31),
    "M":  ("M. Spreader mechanism", "Spreader mechanism", 35),
    "N":  ("N. Lubrication", "Lubrication", 37),
    "P1": ("P1. Threading mechanism (1)", "Threading (1)", 41),
    "P2": ("P2. Threading mechanism (2)", "Threading (2)", 45),
    "P3": ("P3. Threading mechanism (3)", "Threading (3)", 47),
    "Q1": ("Q1. Thread trimmer mechanism (1)", "Thread trimmer (1)", 49),
    "Q2": ("Q2. Thread trimmer mechanism (2)", "Thread trimmer (2)", 51),
    "R":  ("R. Upper thread trimmer", "Upper thread trimmer", 53),
    "S1": ("S1. Control box mechanism", "Control box", 55),
    "T":  ("T. Power switch mechanism", "Power switch", 59),
    "U1": ("U1. Air pressure mechanism (1)", "Air pressure (1)", 61),
    "U2": ("U2. Air pressure mechanism (2)", "Air pressure (2)", 63),
    "V":  ("V. Power supply equipment", "Power supply", 65),
    "W":  ("W. Operation panel mechanism", "Operation panel", 67),
    "X":  ("X. Motor mechanism", "Motor mechanism", 69),
    "Y":  ("Y. Foot switch pedal", "Foot switch pedal", 71),
    "AA1": ("AA1. Attachment set (1)", "Attachment set (1)", 73),
    "AA2": ("AA2. Attachment set (2)", "Attachment set (2)", 79),
    "AA3": ("AA3. Attachment set (3)", "Attachment set (3)", 81),
    "AA4": ("AA4. Attachment set (4)", "Attachment set (4)", 83),
    "AA5": ("AA5. Attachment set (5)", "Attachment set (5)", 89),
    "AA6": ("AA6. Attachment set (6)", "Attachment set (6)", 93),
    "AB": ("AB. Upper thread breakage detector", "Upper thread breakage detector", 95),
    "AC": ("AC. Air pressure detector", "Air pressure detector", 95),
    "AD": ("AD. Upper thread nipper device", "Upper thread nipper", 97),
    "AE": ("AE. Cut length changeover device", "Cut length changeover", 101),
    "AF": ("AF. Fly indexer", "Fly indexer", 105),
    "Z":  ("Z. Accessories", "Accessories", 109),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-rh9820-{ts}")
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
    sec_num = SECTION_ORDER.get(sec, 0)
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
