#!/usr/bin/env python3
"""Buat 24 komponen section-based T-8422D."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 85

SECTIONS = {
    1:  ("A. Machine body", "Badan mesin", 1),
    2:  ("B. Upper shaft mechanism", "Poros atas", 3),
    3:  ("C. Needle bar rocking mechanism", "Needle bar rocking", 5),
    4:  ("D. Presser foot mechanism", "Presser foot", 7),
    5:  ("E. Feed mechanism", "Mekanisme feed", 9),
    6:  ("F. Quick reverse mechanism", "Quick reverse", 11),
    7:  ("G. Feed shaft mechanism", "Feed shaft", 13),
    8:  ("H. Gauge parts", "Gauge parts", 15),
    9:  ("J2. Rotary hook mechanism (T-8422D)", "Rotary hook 8422D", 19),
    10: ("J3. Rotary hook mechanism", "Rotary hook umum", 23),
    11: ("K. Lower shaft mechanism", "Lower shaft", 25),
    12: ("L. Lubrication", "Pelumasan", 27),
    13: ("M. Threading mechanism", "Threading", 31),
    14: ("N. Bobbin winder mechanism", "Bobbin winder", 33),
    15: ("P. Thread trimmer mechanism", "Thread trimmer", 35),
    16: ("Q. Tension release mechanism (T-8422D)", "Tension release 8422D", 39),
    17: ("R. Thread wiper mechanism (T-8422D)", "Thread wiper 8422D", 41),
    18: ("S1. Control box", "Control box (1)", 43),
    19: ("S2. Control box", "Control box (2)", 45),
    20: ("T. Quick reverse switch mechanism", "Quick reverse switch", 47),
    21: ("U. Operation panel", "Panel operasi", 49),
    22: ("V. Power supply equipment and motor mechanism", "Power supply & motor", 51),
    23: ("Z1. Accessories", "Aksesoris (1)", 53),
    24: ("Z2. Accessories", "Aksesoris (2)", 55),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-components-t8422d-{ts}")
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
