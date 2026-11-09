#!/usr/bin/env python3
"""Rebuild 17 komponen section-based DDL-8000CSM."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 225

SECTIONS = {
    1:  ("1. MACHINE FRAME & MISCELLANEOUS COVER COMPONENTS", "Rangka & cover", 1),
    2:  ("2. UPPER SHAFT AND PICK LINE COMPONENTS", "Poros atas & pick line", 3),
    3:  ("3. NEEDLE BAR & THREAD TENSION COMPONENTS", "Batang jarum & tegangan benang", 5),
    4:  ("4. HAND LIFTER COMPONENTS", "Hand lifter", 7),
    5:  ("5. UPRIGHT SHAFT & HOOK DRIVING SHAFT COMPONENTS", "Upright shaft & hook driving", 9),
    6:  ("6. FEED MECHANISM COMPONENTS", "Mekanisme feed", 11),
    7:  ("7. FEED ADJUST MECHANISM COMPONENTS", "Feed adjust", 13),
    8:  ("8. THREAD TRIMMER COMPONENTS", "Thread trimmer", 15),
    9:  ("9. AUTOMATIC REVERSE FEED & NB COMPONENTS", "Reverse feed & NB", 17),
    10: ("10. OIL LUBRICATION COMPONENTS", "Pelumasan", 19),
    11: ("11. OIL SHIELD COMPONENTS", "Oil shield", 21),
    12: ("12. THREAD STAND COMPONENTS", "Thread stand", 23),
    13: ("13. ACCESSORIE PART COMPONENTS", "Aksesoris", 25),
    14: ("14. FOR DDL-8000C-SC,SH", "Part khusus SC/SH", 27),
    15: ("15. OPTION CLOTH PRESS SENSOR DEVICE", "Opsi sensor kain", 29),
    16: ("16. OPTION ONE TOUCH PRESSER DEVICE", "Opsi one-touch presser", 31),
    17: ("17. OPTION LONG PITCH DEVICE", "Opsi long pitch", 33),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-components-ddl8000csm-pdf-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
print(f"[HAPUS] komponen lama: {cur.rowcount}")

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
print(f"[HASIL] komponen: {cur.fetchone()[0]}")
conn.close()
