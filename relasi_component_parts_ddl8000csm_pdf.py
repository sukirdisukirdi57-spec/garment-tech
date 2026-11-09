#!/usr/bin/env python3
"""Isi component_parts DDL-8000CSM (versi PDF, 17 section)."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 225

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-component-parts-ddl8000csm-pdf-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

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
    print(f"  section {ref:>2}: {len(parts)} parts")

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id
               WHERE c.machine_id=?""", (MID,))
print(f"\n[HASIL] total relasi: {cur.fetchone()[0]}")
conn.close()
