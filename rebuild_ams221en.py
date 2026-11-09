#!/usr/bin/env python3
"""Rebuild AMS-221EN (id=45) dari PDF resmi JIKI."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_ams221en_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 45
EXPECTED_MODEL = "AMS-221EN"

SECTIONS = {
    1:  ("1. FRAME & MISC COVER (1)", "Frame & cover (1)", 1),
    2:  ("2. FRAME & MISC COVER (2)", "Frame & cover (2)", 3),
    3:  ("3. FRAME & MISC COVER (3)", "Frame & cover (3)", 5),
    4:  ("4. FRAME & MISC COVER (4)", "Frame & cover (4)", 7),
    5:  ("5. MAIN SHAFT & NEEDLE BAR", "Main shaft & needle bar", 9),
    6:  ("6. PRESSER MECHANISM (1)", "Presser (1)", 11),
    7:  ("7. PRESSER MECHANISM (2)", "Presser (2)", 13),
    8:  ("8. SHUTTLE DRIVER SHAFT", "Shuttle driver shaft", 15),
    9:  ("9. WIPER MECHANISM", "Wiper", 17),
    10: ("10. TENSION RELEASE & THREAD TENSION", "Tension release & thread tension", 18),
    11: ("11. THREAD TRIMMER MECHANISM", "Thread trimmer", 19),
    12: ("12. THREAD CLAMP", "Thread clamp", 21),
    13: ("13. X-Y COMPONENTS (1)", "X-Y (1)", 23),
    14: ("14. X-Y COMPONENTS (2)", "X-Y (2)", 25),
    15: ("15. CLOTH FEED MECHANISM (1)", "Cloth feed (1)", 27),
    16: ("16. CLOTH FEED MECHANISM (2)", "Cloth feed (2)", 29),
    17: ("17. TABLE COMPONENTS", "Table", 31),
    18: ("18. PNEUMATIC COMPONENTS", "Pneumatic", 33),
    19: ("19. THREAD STAND COMPONENTS", "Thread stand", 34),
    20: ("20. OPERATION PANEL", "Operation panel", 35),
    21: ("21. CONTROL BOX COMPONENTS", "Control box", 37),
    23: ("23. PEDAL COMPONENTS", "Pedal", 41),
    24: ("24. ACCESSORIE PART", "Accessories", 42),
    25: ("25. OPTIONAL PARTS", "Optional parts", 43),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-ams221en-{ts}")
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
