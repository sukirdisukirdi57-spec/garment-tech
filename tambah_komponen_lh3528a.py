#!/usr/bin/env python3
"""Tambah komponen untuk halaman 1, 9, 37, 38, 39 LH-3528A + relasi."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 18

NEW_COMPONENTS = [
    ("Aksesoris & Cover", 1, 1),
    ("Thread Tension Assembly 2", 2, 9),
    ("Knee Lifter & Bottom Cover", 3, 37),
    ("AK Device (1)", 4, 38),
    ("AK Device (2)", 5, 39),
]

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-tambah-komponen-lh3528a-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

total_new = 0
for name, ref, page in NEW_COMPONENTS:
    # Cek apakah sudah ada
    cur.execute("SELECT id FROM components WHERE machine_id=? AND component_name=?", (MID, name))
    existing = cur.fetchone()
    if existing:
        print(f"[SKIP] {name} sudah ada")
        continue
    # Part utama = part dengan catalog_ref terkecil di halaman
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND diagram_page=?
                   ORDER BY CAST(catalog_ref AS INTEGER) LIMIT 1""", (MID, page))
    r = cur.fetchone()
    main_pn = r[0] if r else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, name, str(ref), page))
    comp_id = cur.lastrowid
    
    # Relasikan semua parts di halaman ini
    cur.execute("SELECT id FROM parts WHERE machine_id=? AND diagram_page=?", (MID, page))
    parts = cur.fetchall()
    for (pid,) in parts:
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,'sub-part')""", (comp_id, pid))
            total_new += 1
        except sqlite3.IntegrityError:
            pass
    print(f"[OK] {name} (page {page}) -> {len(parts)} parts")

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"\n[HASIL] relasi baru: {total_new}")
print(f"[TOTAL] relasi LH-3528A: {cur.fetchone()[0]}")
conn.close()
