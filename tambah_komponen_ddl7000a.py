#!/usr/bin/env python3
"""Tambah komponen halaman 20 DDL-7000A + relasi."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 4

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-tambah-komponen-ddl7000a-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Cek apakah sudah ada
cur.execute("SELECT id FROM components WHERE machine_id=? AND component_name='Oil Reservoir & Knee Lifter'", (MID,))
if cur.fetchone():
    print("[SKIP] sudah ada")
else:
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=4 AND diagram_page=20
                   ORDER BY CAST(catalog_ref AS INTEGER) LIMIT 1""")
    r = cur.fetchone()
    main_pn = r[0] if r else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, "Oil Reservoir & Knee Lifter", main_pn,
                 "Oil reservoir & knee lifter", "0", 20))
    comp_id = cur.lastrowid
    
    cur.execute("SELECT id FROM parts WHERE machine_id=? AND diagram_page=20", (MID,))
    parts = cur.fetchall()
    for (pid,) in parts:
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,'sub-part')""", (comp_id, pid))
        except sqlite3.IntegrityError:
            pass
    print(f"[OK] komponen + {len(parts)} relasi")

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[TOTAL] relasi: {cur.fetchone()[0]}")
conn.close()
