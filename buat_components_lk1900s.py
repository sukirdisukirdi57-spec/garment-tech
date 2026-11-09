#!/usr/bin/env python3
"""Buat 20 komponen LK-1900S berdasarkan section."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB  = Path("database/garment.db")
MID = 37

SECTIONS = {
    1:  ("1. FRAME & MISCELLANEOUS COVER COMPONENTS", "Rangka & cover", 1),
    2:  ("2. MAIN SHAFT & NEEDLE BAR COMPONENTS", "Poros utama & batang jarum", 3),
    3:  ("3. PRESSER LIFTER & WIPER COMPONENTS", "Presser lifter & wiper", 5),
    4:  ("4. SHUTTLE DRIVER SHAFT COMPONENTS", "Shuttle driver shaft", 7),
    5:  ("5. THREAD TENSION COMPONENTS", "Tegangan benang", 9),
    6:  ("6. THREAD TRIMMER MECHANISM COMPONENTS", "Thread trimmer", 11),
    7:  ("7. FEED MECHANISM COMPONENTS", "Mekanisme feed", 13),
    8:  ("8. SENSOR COMPONENTS", "Sensor", 15),
    9:  ("9. THREAD STAND COMPONENTS", "Thread stand", 17),
    10: ("10. TABLE STAND COMPONENTS (JT-K46)", "Meja & stand", 19),
    11: ("11. CONTROL BOX COMPONENTS", "Control box", 21),
    12: ("12. OPERATION PANEL COMPONENTS", "Panel operasi", 23),
    14: ("14. ACCESSORIE PARTS COMPONENTS", "Aksesoris", 27),
    15: ("15. EXCLUSIVE PARTS FOR LK-1903SS-301,LK-1903SS-302(1)", "Part khusus LK-1903SS (1)", 29),
    16: ("16. EXCLUSIVE PARTS FOR LK-1903SS-301,LK-1903SS-302(2)", "Part khusus LK-1903SS (2)", 31),
    17: ("17. ACCESSORIE PARTS FOR LK-1900S SUBCLASSES", "Aksesoris subclass", 33),
    18: ("18. OPTION COMPONENTS (1)", "Opsi komponen (1)", 35),
    19: ("19. OPTION COMPONENTS (2) (FOR LK-1903S)", "Opsi komponen (2)", 37),
    20: ("20. OPTION COMPONENTS (3) (FOR LK-1903S SHANK BUTTON)", "Opsi komponen (3)", 39),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-components-lk1900s-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
if cur.fetchone()[0] > 0:
    raise SystemExit("BATAL: komponen sudah ada")

for ref, (name, location, page) in SECTIONS.items():
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY catalog_ref LIMIT 1""", (MID, ref))
    row = cur.fetchone()
    main_pn = row[0] if row else None

    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, location, str(ref), page))

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[HASIL] {cur.fetchone()[0]} komponen dibuat")
conn.close()
