#!/usr/bin/env python3
"""Rebuild MO-6700S (id=5) dengan 1048 parts."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_mo6700s_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 5
EXPECTED_MODEL = "MO-6700S"

SECTIONS = {
    1:  ("1. MISCELLANEOUS COVER (1)", "Cover (1)", 1),
    2:  ("2. MISCELLANEOUS COVER (2)", "Cover (2)", 3),
    3:  ("3. CRANKSHAFT", "Crankshaft", 5),
    4:  ("4. NEEDLE DRIVING SHAFT", "Needle driving shaft", 7),
    5:  ("5. FEED MECHANISM (1)", "Feed mechanism (1)", 9),
    6:  ("6. FEED MECHANISM (2)", "Feed mechanism (2)", 11),
    7:  ("7. UPPER & LOWER LOOPER", "Upper & lower looper", 13),
    8:  ("8. CHAIN LOOPER", "Chain looper", 15),
    9:  ("9. PRESSER FOOT (1)", "Presser foot (1)", 16),
    10: ("10. PRESSER FOOT (2)", "Presser foot (2)", 17),
    11: ("11. THREAD TENSION", "Thread tension", 19),
    12: ("12. LOWER KNIFE", "Lower knife", 21),
    13: ("13. UPPER KNIFE", "Upper knife", 23),
    14: ("14. NEEDLE COOLING MECHANISM", "Needle cooling", 24),
    15: ("15. LUBRICATION MECHANISM", "Lubrication", 25),
    16: ("16. SEMI-SUNKEN TABLE", "Semi-sunken table", 27),
    17: ("17. FULLY-SUNKEN TABLE", "Fully-sunken table", 28),
    18: ("18. STAND (Z/T)", "Stand", 29),
    19: ("19. THREAD STAND (MO-6704S/6714S)", "Thread stand (6704S/6714S)", 31),
    20: ("20. THREAD STAND SP (6704S/6714S)", "Thread stand SP (6704S/6714S)", 33),
    21: ("21. THREAD STAND (MO-6716S)", "Thread stand (6716S)", 35),
    22: ("22. THREAD STAND SP (MO-6716S)", "Thread stand SP (6716S)", 37),
    23: ("23. SPECIAL ORDER PARTS", "Special order parts", 39),
    24: ("24. ACCESSORIES PARTS", "Accessories", 41),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-mo6700s-{ts}")
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
    sec = int(r["section_ref"])
    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page, section_ref, section_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (MID, r["part_number"], r["part_name"], qty,
                 int(r["catalog_ref"]), int(r["diagram_page"]),
                 sec, SECTIONS[sec][0]))

for ref, (name, loc, page) in SECTIONS.items():
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY catalog_ref LIMIT 1""", (MID, ref))
    r = cur.fetchone()
    main_pn = r[0] if r else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, loc, str(ref), page))

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
