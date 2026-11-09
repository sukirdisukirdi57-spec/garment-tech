#!/usr/bin/env python3
"""Tambah komponen untuk 12 section AMS-210EN-2210 yang belum terwakili."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 44

SECTIONS = {
    1:  ("Section 1 Components", 1),
    2:  ("Section 2 Components", 3),
    8:  ("Section 8 Components", 15),
    9:  ("Section 9 Components", 17),
    16: ("Section 16 Components", 31),
    17: ("Section 17 Components", 33),
    18: ("Section 18 Components", 35),
    20: ("Section 20 Components", 39),
    24: ("Section 24 Components", 47),
    25: ("Section 25 Components", 49),
    26: ("Section 26 Components", 51),
    27: ("Section 27 Components", 53),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-tambah-komponen-ams2210-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

total = 0
for sec, (name, page) in SECTIONS.items():
    cur.execute("SELECT id FROM components WHERE machine_id=? AND component_name=?", (MID, name))
    if cur.fetchone():
        print(f"[SKIP] {name}")
        continue
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY CAST(catalog_ref AS INTEGER) LIMIT 1""", (MID, sec))
    r = cur.fetchone()
    main_pn = r[0] if r else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, name, str(sec), page))
    comp_id = cur.lastrowid
    
    cur.execute("SELECT id FROM parts WHERE machine_id=? AND section_ref=?", (MID, sec))
    parts = cur.fetchall()
    for (pid,) in parts:
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,'sub-part')""", (comp_id, pid))
            total += 1
        except sqlite3.IntegrityError:
            pass
    print(f"[OK] {name} -> {len(parts)} parts")

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"\n[HASIL] relasi baru: {total}")
print(f"[TOTAL] relasi: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM parts WHERE machine_id=? AND id NOT IN (
               SELECT cp.part_id FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?)""", (MID, MID))
print(f"[SISA] parts tanpa relasi: {cur.fetchone()[0]}")
conn.close()
