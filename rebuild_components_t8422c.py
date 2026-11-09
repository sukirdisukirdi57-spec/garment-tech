#!/usr/bin/env python3
"""Buat komponen section-based T-8422C + relasi."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 90

SECTIONS = {
    1:  ("A. Machine body", "Badan mesin", 1),
    2:  ("B. Upper shaft mechanism", "Poros atas", 3),
    3:  ("C. Needle bar rocking mechanism", "Needle bar rocking", 5),
    4:  ("D. Presser foot mechanism", "Presser foot", 7),
    5:  ("E. Feed mechanism", "Mekanisme feed", 9),
    6:  ("F. Quick reverse mechanism", "Quick reverse", 11),
    7:  ("G. Feed shaft mechanism", "Feed shaft", 13),
    8:  ("H. Gauge parts", "Gauge parts", 15),
    9:  ("J2. Rotary hook mechanism (T-8422C)", "Rotary hook 8422C", 19),
    10: ("J3. Rotary hook mechanism", "Rotary hook umum", 23),
    11: ("K. Lower shaft mechanism", "Lower shaft", 25),
    12: ("L. Lubrication", "Pelumasan", 27),
    13: ("M. Threading mechanism", "Threading", 31),
    14: ("N. Bobbin winder mechanism", "Bobbin winder", 33),
    15: ("P. Thread trimmer mechanism", "Thread trimmer", 35),
    16: ("Q. Tension release mechanism (T-8422C)", "Tension release 8422C", 39),
    17: ("R. Thread wiper mechanism (T-8422C)", "Thread wiper 8422C", 41),
    18: ("S1. Control box and motor mechanism", "Control box & motor", 43),
    19: ("S2. Control box", "Control box (2)", 45),
    20: ("S3. Control box", "Control box (3)", 47),
    21: ("T. Quick reverse switch mechanism", "Quick reverse switch", 49),
    22: ("U. Power supply equipment", "Power supply", 51),
    23: ("Z1. Accessories", "Aksesoris (1)", 53),
    24: ("Z2. Accessories", "Aksesoris (2)", 55),
    25: ("Wa1. Warning labels", "Label peringatan (1)", 57),
    26: ("Wa2. Warning labels", "Label peringatan (2)", 58),
    27: ("Sp1. Different parts list", "Part khusus (1)", 59),
    28: ("Sp2. Different parts list", "Part khusus (2)", 60),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-components-t8422c-{ts}")
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

# Relasi langsung
cur.execute("SELECT id, catalog_ref, part_number FROM components WHERE machine_id=?", (MID,))
components = {int(r[1]): (r[0], r[2]) for r in cur.fetchall()}

total = 0
for ref, (comp_id, comp_pn) in sorted(components.items()):
    cur.execute("SELECT id, part_number FROM parts WHERE machine_id=? AND section_ref=?", (MID, ref))
    parts = cur.fetchall()
    for pid, pn in parts:
        rel = "matched_catalog_part" if pn == comp_pn else "sub-part"
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,?)""", (comp_id, pid, rel))
            total += 1
        except sqlite3.IntegrityError:
            pass

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[HASIL] komponen: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[HASIL] relasi: {cur.fetchone()[0]}")
conn.close()
