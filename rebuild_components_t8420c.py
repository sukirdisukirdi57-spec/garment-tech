#!/usr/bin/env python3
"""Buat 18 komponen section-based T-8420C."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 94

SECTIONS = {
    1:  ("A. Machine body", "Badan mesin", 1),
    2:  ("B. Upper shaft mechanism", "Poros atas", 3),
    3:  ("C. Needle bar rocking mechanism", "Needle bar rocking", 5),
    4:  ("D. Presser foot mechanism", "Presser foot", 7),
    5:  ("E. Feed mechanism", "Mekanisme feed", 9),
    6:  ("F. Feed shaft mechanism", "Feed shaft", 11),
    7:  ("G. Gauge parts", "Gauge parts", 13),
    8:  ("H1. Rotary hook mechanism", "Rotary hook (1)", 15),
    9:  ("H2. Rotary hook mechanism", "Rotary hook (2)", 17),
    10: ("J. Lower shaft mechanism", "Lower shaft", 19),
    11: ("K. Lubrication", "Pelumasan", 21),
    12: ("L. Threading mechanism", "Threading", 25),
    13: ("M. Bobbin winder mechanism", "Bobbin winder", 27),
    14: ("N. Power supply equipment", "Power supply", 29),
    15: ("Z1. Accessories", "Aksesoris (1)", 31),
    16: ("Z2. Accessories", "Aksesoris (2)", 33),
    17: ("Wa. Warning labels", "Label peringatan", 35),
    18: ("Sp. Different parts list", "Part khusus", 37),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-components-t8420c-{ts}")
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
