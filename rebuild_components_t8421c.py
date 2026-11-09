#!/usr/bin/env python3
"""Buat komponen section-based T-8421C + relasi."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 89

SECTIONS = {
    1:  ("A. Machine body", "Badan mesin", 1),
    2:  ("B. Upper shaft mechanism", "Poros atas", 3),
    3:  ("C. Needle bar rocking mechanism", "Needle bar rocking", 5),
    4:  ("D. Presser foot mechanism", "Presser foot", 7),
    5:  ("E. Feed mechanism", "Mekanisme feed", 9),
    6:  ("F. Quick reverse mechanism", "Quick reverse", 11),
    7:  ("G. Feed shaft mechanism", "Feed shaft", 13),
    8:  ("H. Gauge parts", "Gauge parts", 15),
    9:  ("J1. Rotary hook mechanism (T-8421C)", "Rotary hook 8421C", 17),
    10: ("J3. Rotary hook mechanism", "Rotary hook umum", 23),
    11: ("K. Lower shaft mechanism", "Lower shaft", 25),
    12: ("L. Lubrication", "Pelumasan", 27),
    13: ("M. Threading mechanism", "Threading", 31),
    14: ("N. Bobbin winder mechanism", "Bobbin winder", 33),
    15: ("P. Thread trimmer mechanism", "Thread trimmer", 35),
    16: ("S1. Control box and motor mechanism", "Control box & motor", 43),
    17: ("S2. Control box", "Control box (2)", 45),
    18: ("S3. Control box", "Control box (3)", 47),
    19: ("T. Quick reverse switch mechanism", "Quick reverse switch", 49),
    20: ("U. Power supply equipment", "Power supply", 51),
    21: ("Z1. Accessories", "Aksesoris (1)", 53),
    22: ("Z2. Accessories", "Aksesoris (2)", 55),
    23: ("Wa1. Warning labels", "Label peringatan (1)", 57),
    24: ("Wa2. Warning labels", "Label peringatan (2)", 58),
    25: ("Sp1. Different parts list", "Part khusus (1)", 59),
    26: ("Sp2. Different parts list", "Part khusus (2)", 60),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-components-t8421c-{ts}")
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
