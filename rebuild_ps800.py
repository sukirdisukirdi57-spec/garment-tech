#!/usr/bin/env python3
"""Rebuild PS-800 (id=11) dengan 1004 parts dari parse PDF."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_ps800_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 11
EXPECTED_MODEL = "PS-800"

SECTIONS = {
    1:  ("1. MACHINE FRAME & MISC COVER (1)", "Rangka & cover (1)", 1),
    2:  ("2. MACHINE FRAME & MISC COVER (2)", "Rangka & cover (2)", 3),
    3:  ("3. DISPLAY UNIT", "Display unit", 5),
    4:  ("4. UPPER SHAFT & PICK LINE", "Poros atas & pick line", 7),
    5:  ("5. NEEDLE BAR & LOWER SHAFT", "Needle bar & lower shaft", 9),
    6:  ("6. ROTARY SHUTTLE & THREAD CUTTING", "Rotary shuttle & thread cutting", 11),
    7:  ("7. OIL SUPPLY & NEEDLE PLATE", "Oil supply & needle plate", 13),
    8:  ("8. WIRE CUT ELECTROMAGNETIC", "Wire cut electromagnetic", 15),
    9:  ("9. Y BASE UNIT", "Y base unit", 17),
    10: ("10. Y SCREW ROD MOTOR UNIT", "Y screw rod motor", 19),
    11: ("11. Y CONNECTION SEAT", "Y connection seat", 21),
    12: ("12. X BASE UNIT", "X base unit", 23),
    13: ("13. X MOTOR", "X motor", 25),
    14: ("14. X PRESSURE PLATE", "X pressure plate", 27),
    15: ("15. X SHELL PARTS", "X shell parts", 29),
    16: ("16. PACK UNIT", "Pack unit", 31),
    17: ("17. FRAME CONNECTION ALUMINUM", "Frame connection aluminum", 33),
    18: ("18. PLATEN CONNECTION ALUMINUM", "Platen connection aluminum", 35),
    19: ("19. PLATEN PARTS", "Platen parts", 37),
    20: ("20. ELECTRICAL", "Electrical", 39),
    21: ("21. WIPER CYLINDER", "Wiper cylinder", 41),
    22: ("22. NEEDLE COOLER", "Needle cooler", 43),
    23: ("23. ELECTRONIC PRESSER FOOT", "Electronic presser foot", 45),
    24: ("24. POWER SUPPLY WIRING", "Power supply wiring", 47),
    25: ("25. ACCESSORY BOX", "Accessory box", 49),
    26: ("26. PRESSER FOOT", "Presser foot", 51),
    27: ("27. NEEDLE PLATE", "Needle plate", 53),
    28: ("28. THIRD THREAD TENSION REGULATOR", "Third thread tension regulator", 55),
    29: ("29. LASER TUBE", "Laser tube", 57),
    30: ("30. LASER AIR SUCTION", "Laser air suction", 59),
    31: ("31. LASER ELECTRONIC CONTROL", "Laser electronic control", 61),
    32: ("32. ROTARY CUTTER MEMBER", "Rotary cutter member", 63),
    33: ("33. ROTARY KNIFE", "Rotary knife", 65),
    34: ("34. BARCODE READER", "Barcode reader", 67),
    35: ("35. ACTIVE TENSION", "Active tension", 69),
    36: ("36. THICK MATERIAL KIT", "Thick material kit", 71),
    37: ("37. OPTIONAL PARTS", "Optional parts", 73),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-ps800-{ts}")
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
