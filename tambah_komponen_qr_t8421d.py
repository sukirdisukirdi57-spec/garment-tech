#!/usr/bin/env python3
"""Tambah komponen Q & R untuk T-8421D + relasi parts-nya."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 84

EXTRA = {
    25: ("Q. Tension release mechanism (varian)", "Tension release", 39),
    26: ("R. Thread wiper mechanism (varian)", "Thread wiper", 41),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-tambah-qr-t8421d-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Cek apakah sudah ada
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=? AND CAST(catalog_ref AS INTEGER) IN (25,26)", (MID,))
if cur.fetchone()[0] > 0:
    print("[SKIP] komponen Q/R sudah ada")
else:
    for ref, (name, loc, page) in EXTRA.items():
        cur.execute("""INSERT INTO components(machine_id, component_name, location, catalog_ref, diagram_page)
                       VALUES(?,?,?,?,?)""", (MID, name, loc, str(ref), page))
    print(f"[OK] 2 komponen Q/R dibuat")

conn.commit()

# Relasi
cur.execute("SELECT id, catalog_ref FROM components WHERE machine_id=? AND CAST(catalog_ref AS INTEGER) IN (25,26)", (MID,))
comps = {int(r[1]): r[0] for r in cur.fetchall()}

total = 0
for ref, comp_id in comps.items():
    cur.execute("SELECT id FROM parts WHERE machine_id=? AND section_ref=?", (MID, ref))
    parts = cur.fetchall()
    for (pid,) in parts:
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,'sub-part')""", (comp_id, pid))
            total += 1
        except sqlite3.IntegrityError:
            pass
    print(f"  section {ref}: {len(parts)} parts")

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"\n[HASIL] total relasi T-8421D: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[BARU] relasi ditambah: {total}")
conn.close()
