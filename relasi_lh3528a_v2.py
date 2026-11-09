#!/usr/bin/env python3
"""Relasi LH-3528A v2: matched + sub-part via rentang catalog_ref per halaman."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 18

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-relasi-lh3528a-v2-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DELETE FROM component_parts WHERE component_id IN (SELECT id FROM components WHERE machine_id=?)", (MID,))
print(f"[HAPUS] relasi lama: {cur.rowcount}")

# Group komponen per diagram_page, urut catalog_ref
cur.execute("""SELECT id, catalog_ref, diagram_page, component_name
               FROM components WHERE machine_id=?
               ORDER BY diagram_page, CAST(catalog_ref AS INTEGER)""", (MID,))
comps = cur.fetchall()

from collections import defaultdict
by_page = defaultdict(list)
for cid, cref, cpage, cname in comps:
    try:
        by_page[cpage].append((int(cref), cid, cname))
    except:
        pass

total = 0
for page, comp_list in sorted(by_page.items()):
    # Ambil semua parts di halaman ini
    cur.execute("""SELECT id, CAST(catalog_ref AS INTEGER) AS ref
                   FROM parts WHERE machine_id=? AND diagram_page=?
                   ORDER BY CAST(catalog_ref AS INTEGER)""", (MID, page))
    parts = cur.fetchall()
    
    for pid, part_ref in parts:
        # Cari komponen dengan ref terdekat <= part_ref
        matched_comp = None
        for comp_ref, cid, cname in comp_list:
            if comp_ref <= part_ref:
                matched_comp = (comp_ref, cid, cname)
            else:
                break
        if not matched_comp:
            matched_comp = comp_list[0] + (None,)
            matched_comp = (comp_list[0][0], comp_list[0][1], comp_list[0][2])
        
        comp_ref, cid, cname = matched_comp
        rel = "matched_catalog_part" if comp_ref == part_ref else "sub-part"
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,?)""", (cid, pid, rel))
            total += 1
        except sqlite3.IntegrityError:
            pass

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[HASIL] total relasi: {cur.fetchone()[0]}")
conn.close()
