#!/usr/bin/env python3
"""Relasi LH-3528A (id=18) via catalog_ref + diagram_page."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 18

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-relasi-lh3528a-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Hapus relasi lama (jika ada)
cur.execute("DELETE FROM component_parts WHERE component_id IN (SELECT id FROM components WHERE machine_id=?)", (MID,))
print(f"[HAPUS] relasi lama: {cur.rowcount}")

# Ambil komponen
cur.execute("SELECT id, catalog_ref, diagram_page, component_name FROM components WHERE machine_id=?", (MID,))
comps = cur.fetchall()
print(f"[KOMPONEN] {len(comps)}")

total = 0
for comp_id, comp_ref, comp_page, comp_name in comps:
    try:
        ref_int = int(comp_ref) if comp_ref else None
    except (ValueError, TypeError):
        ref_int = None
    
    if ref_int is None:
        continue
    
    # Cari parts dengan catalog_ref SAMA dan diagram_page SAMA
    cur.execute("""SELECT id, part_number FROM parts
                   WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=? AND diagram_page=?""",
                (MID, ref_int, comp_page))
    parts = cur.fetchall()
    
    for pid, pn in parts:
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,'matched_catalog_part')""", (comp_id, pid))
            total += 1
        except sqlite3.IntegrityError:
            pass
    
    if parts:
        print(f"  {comp_name[:40]:<40} ref={ref_int} page={comp_page} -> {len(parts)} parts")

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"\n[HASIL] total relasi: {cur.fetchone()[0]}")
conn.close()
