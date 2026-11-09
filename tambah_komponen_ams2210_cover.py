#!/usr/bin/env python3
"""Tambah komponen Cover & Aksesoris AMS-210EN-2210 untuk 44 parts tanpa section."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 44

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-tambah-cover-ams2210-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Cek apakah sudah ada
cur.execute("SELECT id FROM components WHERE machine_id=? AND component_name='Cover & Aksesoris'", (MID,))
existing = cur.fetchone()
if existing:
    comp_id = existing[0]
    print(f"[SKIP] sudah ada (id={comp_id})")
else:
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, "Cover & Aksesoris", None, "Cover & aksesoris", "99", 6))
    comp_id = cur.lastrowid
    print(f"[OK] komponen dibuat (id={comp_id})")

# Relasikan 44 parts tanpa section
cur.execute("""SELECT id FROM parts WHERE machine_id=? AND id NOT IN (
               SELECT cp.part_id FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?)""", (MID, MID))
parts = cur.fetchall()
total = 0
for (pid,) in parts:
    try:
        cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                       VALUES(?,?,'sub-part')""", (comp_id, pid))
        total += 1
    except sqlite3.IntegrityError:
        pass
print(f"[RELASI] {total} parts")

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[TOTAL] relasi: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM parts WHERE machine_id=? AND id NOT IN (
               SELECT cp.part_id FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?)""", (MID, MID))
print(f"[SISA] parts tanpa relasi: {cur.fetchone()[0]}")
conn.close()
