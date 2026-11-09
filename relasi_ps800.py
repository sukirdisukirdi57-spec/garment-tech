#!/usr/bin/env python3
"""Relasi PS-800 (id=11) via catalog_ref + diagram_page + sub-part."""
import sqlite3, shutil, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB = Path("database/garment.db")
MID = 11

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-relasi-ps800-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Hapus relasi lama
cur.execute("DELETE FROM component_parts WHERE component_id IN (SELECT id FROM components WHERE machine_id=?)", (MID,))
print(f"[HAPUS] relasi lama: {cur.rowcount}")

# Group komponen per diagram_page, urut catalog_ref (ekstrak angka dari "Ref. N")
cur.execute("""SELECT id, catalog_ref, diagram_page, component_name
               FROM components WHERE machine_id=?
               ORDER BY diagram_page""", (MID,))
comps = cur.fetchall()

by_page = defaultdict(list)
for cid, cref, cpage, cname in comps:
    m = re.search(r'(\d+)', str(cref))
    if m:
        by_page[cpage].append((int(m.group(1)), cid, cname))

total = 0
for page, comp_list in sorted(by_page.items()):
    comp_list.sort(key=lambda x: x[0])
    cur.execute("""SELECT id, CAST(catalog_ref AS INTEGER) AS ref
                   FROM parts WHERE machine_id=? AND diagram_page=?
                   ORDER BY CAST(catalog_ref AS INTEGER)""", (MID, page))
    parts = cur.fetchall()
    
    for pid, part_ref in parts:
        matched = None
        for comp_ref, cid, cname in comp_list:
            if comp_ref <= part_ref:
                matched = (comp_ref, cid)
            else:
                break
        if not matched:
            matched = (comp_list[0][0], comp_list[0][1])
        
        comp_ref, cid = matched
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
