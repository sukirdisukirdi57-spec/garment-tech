#!/usr/bin/env python3
"""Fix section_ref AMS-210EN-2210 dari notes + relasi."""
import sqlite3, shutil, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB = Path("database/garment.db")
MID = 44

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-fix-ams2210-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. Isi section_ref dari notes
cur.execute("SELECT id, notes FROM parts WHERE machine_id=? AND notes LIKE '%section%'", (MID,))
updated = 0
for pid, notes in cur.fetchall():
    m = re.search(r'section (\d+)', notes)
    if m:
        sec = int(m.group(1))
        cur.execute("UPDATE parts SET section_ref=? WHERE id=?", (sec, pid))
        updated += 1
print(f"[SECTION] {updated} parts")

# 2. Isi diagram_page = 2*sec-1
cur.execute("SELECT DISTINCT section_ref FROM parts WHERE machine_id=? AND section_ref IS NOT NULL ORDER BY section_ref", (MID,))
sections = [r[0] for r in cur.fetchall()]
for sec in sections:
    cur.execute("UPDATE parts SET diagram_page=? WHERE machine_id=? AND section_ref=?", (2*sec-1, MID, sec))
print(f"[PAGE] {len(sections)} section")

conn.commit()

# 3. Hapus relasi lama & rebuild via diagram_page (komponen)
cur.execute("DELETE FROM component_parts WHERE component_id IN (SELECT id FROM components WHERE machine_id=?)", (MID,))
print(f"[HAPUS] relasi lama: {cur.rowcount}")

cur.execute("SELECT DISTINCT diagram_page FROM parts WHERE machine_id=? AND diagram_page IS NOT NULL ORDER BY diagram_page", (MID,))
part_pages = [r[0] for r in cur.fetchall()]

cur.execute("""SELECT id, catalog_ref, diagram_page, component_name
               FROM components WHERE machine_id=? AND diagram_page IS NOT NULL""", (MID,))
comps = cur.fetchall()

by_page = defaultdict(list)
for cid, cref, cpage, cname in comps:
    nearest = min(part_pages, key=lambda p: abs(p - cpage))
    ref_int = int(cref) if cref and str(cref).isdigit() else 999
    by_page[nearest].append((ref_int, cid, cname))

total = 0
for page, comp_list in sorted(by_page.items()):
    comp_list.sort(key=lambda x: x[0])
    cur.execute("""SELECT id, CAST(catalog_ref AS INTEGER) AS ref
                   FROM parts WHERE machine_id=? AND diagram_page=?
                   ORDER BY CAST(catalog_ref AS INTEGER)""", (MID, page))
    for pid, part_ref in cur.fetchall():
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
print(f"[RELASI] {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM parts WHERE machine_id=? AND id NOT IN (
               SELECT cp.part_id FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?)""", (MID, MID))
print(f"[SISA] parts tanpa relasi: {cur.fetchone()[0]}")
conn.close()
