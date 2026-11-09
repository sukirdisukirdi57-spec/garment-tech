#!/usr/bin/env python3
"""Relasi AMS-210EN-1306 via diagram_page terdekat."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB = Path("database/garment.db")
MID = 43

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-relasi-ams1306-v3-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DELETE FROM component_parts WHERE component_id IN (SELECT id FROM components WHERE machine_id=?)", (MID,))
print(f"[HAPUS] relasi lama: {cur.rowcount}")

# Parts page yang tersedia
cur.execute("SELECT DISTINCT diagram_page FROM parts WHERE machine_id=? AND diagram_page IS NOT NULL ORDER BY diagram_page", (MID,))
part_pages = [r[0] for r in cur.fetchall()]
print(f"[PAGES PARTS] {part_pages}")

cur.execute("""SELECT id, catalog_ref, diagram_page, component_name
               FROM components WHERE machine_id=? ORDER BY diagram_page""", (MID,))
comps = cur.fetchall()

by_page = defaultdict(list)
for cid, cref, cpage, cname in comps:
    if cpage:
        # Cari part page terdekat
        nearest = min(part_pages, key=lambda p: abs(p - cpage))
        by_page[nearest].append((int(cref) if cref else 999, cid, cname, cpage))

total = 0
for page, comp_list in sorted(by_page.items()):
    comp_list.sort(key=lambda x: x[0])
    cur.execute("""SELECT id, CAST(catalog_ref AS INTEGER) AS ref
                   FROM parts WHERE machine_id=? AND diagram_page=?
                   ORDER BY CAST(catalog_ref AS INTEGER)""", (MID, page))
    parts = cur.fetchall()
    
    for pid, part_ref in parts:
        matched = None
        for comp_ref, cid, cname, cpage in comp_list:
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
cur.execute("""SELECT COUNT(*) FROM parts WHERE machine_id=? AND id NOT IN (
               SELECT cp.part_id FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?)""", (MID, MID))
print(f"[SISA] parts tanpa relasi: {cur.fetchone()[0]}")
conn.close()
