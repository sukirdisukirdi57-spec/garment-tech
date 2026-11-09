#!/usr/bin/env python3
"""Isi component_parts: relasi komponen <-> parts berdasarkan section_ref."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB  = Path("database/garment.db")
MID = 17

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-component-parts-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Ambil semua komponen (section_ref = catalog_ref)
cur.execute("SELECT id, catalog_ref FROM components WHERE machine_id=?", (MID,))
components = {int(r[1]): r[0] for r in cur.fetchall()}
print(f"[KOMPONEN] {len(components)} terdeteksi")

total_inserted = 0
for ref, comp_id in sorted(components.items()):
    cur.execute("""SELECT id, part_number FROM parts
                   WHERE machine_id=? AND section_ref=?""", (MID, ref))
    parts = cur.fetchall()

    for pid, pn in parts:
        # relation_type: matched_catalog_part jika part_number sama dengan komponen,
        # else sub-part
        cur.execute("SELECT part_number FROM components WHERE id=?", (comp_id,))
        comp_pn = cur.fetchone()[0]
        rel = "matched_catalog_part" if pn == comp_pn else "sub-part"

        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,?)""", (comp_id, pid, rel))
            total_inserted += 1
        except sqlite3.IntegrityError:
            pass  # duplikat, skip

    print(f"  section {ref}: {len(parts)} parts")

conn.commit()

cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id
               WHERE c.machine_id=?""", (MID,))
print(f"\n[HASIL] total relasi component_parts: {cur.fetchone()[0]}")
print(f"[INSERT] baris baru: {total_inserted}")

conn.close()
