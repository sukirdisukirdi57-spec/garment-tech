#!/usr/bin/env python3
"""Rebuild LZ-2290A (id=36) dari PDF resmi JIKI."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_lz2290a_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 36
EXPECTED_MODEL = "LZ-2290A"

SECTIONS = {
    1:  ("1. FRAME & MISC COVER (1)", "Frame & cover (1)", 1),
    2:  ("2. FRAME & MISC COVER (2)", "Frame & cover (2)", 3),
    3:  ("3. MAIN SHAFT & THREAD TAKE-UP & NEEDLE BAR", "Main shaft & needle bar", 5),
    4:  ("4. NEEDLE VIBRATOR", "Needle vibrator", 7),
    5:  ("5. HAND LIFTER", "Hand lifter", 9),
    6:  ("6. FEED MECHANISM (1)", "Feed mechanism (1)", 11),
    7:  ("7. FEED MECHANISM (2)", "Feed mechanism (2)", 13),
    8:  ("8. FEED MECHANISM (3)", "Feed mechanism (3)", 15),
    9:  ("9. FEED MECHANISM (4)", "Feed mechanism (4)", 17),
    10: ("10. HOOK DRIVING SHAFT (1)", "Hook driving shaft (1)", 19),
    11: ("11. HOOK DRIVING SHAFT (2)", "Hook driving shaft (2)", 21),
    12: ("12. THREAD TRIMMER MECHANISM", "Thread trimmer", 23),
    13: ("13. FEED MECHANISM (SU/DU)", "Feed mechanism (SU/DU)", 25),
    14: ("14. AUTOMATIC REVERSE FEED", "Automatic reverse feed", 26),
    15: ("15. THREAD FEEDER", "Thread feeder", 27),
    16: ("16. MANUAL SWITCH", "Manual switch", 28),
    17: ("17. MANUAL SWITCH (0B)", "Manual switch (0B)", 29),
    18: ("18. THREAD RELEASE SOLENOID", "Thread release solenoid", 31),
    19: ("19. LUBRICATION", "Lubrication", 33),
    20: ("20. WIPER MECHANISM", "Wiper mechanism", 35),
    21: ("21. UNDER COVER", "Under cover", 37),
    22: ("22. THREAD STAND", "Thread stand", 39),
    23: ("23. IP-100 PANEL", "IP-100 panel", 40),
    24: ("24. SC-915/916 TRANSMISSION (1)", "SC-915/916 transmission (1)", 41),
    25: ("25. SC-915/916 TRANSMISSION (2)", "SC-915/916 transmission (2)", 43),
    26: ("26. SC-915/916 ACCESSORIE", "SC-915/916 accessorie", 45),
    27: ("27. ACCESSORIE PARTS", "Accessories", 46),
    28: ("28. COMMON PARTS DS/DU", "Common parts DS/DU", 47),
    29: ("29. CB TYPE (1)", "CB type (1)", 48),
    30: ("30. CB TYPE (2)", "CB type (2)", 49),
    31: ("31. CB TYPE (3)", "CB type (3)", 51),
    32: ("32. SPECIAL ORDER (1)", "Special order (1)", 53),
    33: ("33. SPECIAL ORDER (2)", "Special order (2)", 55),
    34: ("34. SPECIAL ORDER (3)", "Special order (3)", 56),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-lz2290a-{ts}")
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
