#!/usr/bin/env python3
"""Rebuild MEB-3200C (id=40) dari PDF."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_meb3200c_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 40
EXPECTED_MODEL = "MEB-3200C"

SECTIONS = {
    1:  ("1. FRAME & MISC COVER (1)", "Frame & cover (1)", 1),
    2:  ("2. FRAME & MISC COVER (2)", "Frame & cover (2)", 3),
    3:  ("3. BOTTOM COVER", "Bottom cover", 5),
    4:  ("4. FEED", "Feed", 7),
    5:  ("5. CLOTH OPEN", "Cloth open", 9),
    6:  ("6. LOWER THREAD CUTTING (1)", "Lower thread cutting (1)", 11),
    7:  ("7. LOWER THREAD CUTTING (2)", "Lower thread cutting (2)", 13),
    8:  ("8. UPPER THREAD CUTTING", "Upper thread cutting", 15),
    9:  ("9. PRESSER (1)", "Presser (1)", 17),
    10: ("10. PRESSER (2)", "Presser (2)", 19),
    11: ("11. REVOLUTION", "Revolution", 21),
    12: ("12. LOOPER DRIVING", "Looper driving", 23),
    13: ("13. LOWER SHAFT", "Lower shaft", 25),
    14: ("14. UPPER SHAFT", "Upper shaft", 27),
    15: ("15. NEEDLE BAR DRIVING", "Needle bar driving", 29),
    16: ("16. NEEDLE BAR ROCKING", "Needle bar rocking", 31),
    17: ("17. NEEDLE BAR", "Needle bar", 33),
    18: ("18. THREAD TAKE-UP LEVER & GUIDE LOWER", "Thread take-up & guide lower", 35),
    19: ("19. LOWER THREAD HAUL", "Lower thread haul", 37),
    20: ("20. THREAD GUIDE UPPER", "Thread guide upper", 39),
    21: ("21. GIMP HAUL", "Gimp haul", 41),
    22: ("22. CLOTH CUTTING (1)", "Cloth cutting (1)", 43),
    23: ("23. CLOTH CUTTING (2)", "Cloth cutting (2)", 45),
    24: ("24. MULTICUTTING DEVICE", "Multicutting device", 47),
    25: ("25. AIR", "Air", 49),
    26: ("26. LUBRICATION MECHANISM", "Lubrication", 51),
    27: ("27. TABLE", "Table", 53),
    28: ("28. TRANSMISSION", "Transmission", 55),
    30: ("30. ACCESSORY PARTS", "Accessories", 59),
    31: ("31. OPTION (1)", "Option (1)", 61),
    32: ("32. OPTION (2)", "Option (2)", 63),
    33: ("33. OPTION (3)", "Option (3)", 65),
    34: ("34. OPTION (4)", "Option (4)", 67),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-meb3200c-{ts}")
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
