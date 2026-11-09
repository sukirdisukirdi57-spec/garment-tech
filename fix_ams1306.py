#!/usr/bin/env python3
"""Isi section_ref AMS-210EN-1306 dari notes + relasi."""
import sqlite3, shutil, re
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 43

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-fix-ams1306-{ts}")
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
        cur.execute("UPDATE parts SET section_ref=? WHERE id=?", (int(m.group(1)), pid))
        updated += 1
print(f"[SECTION] {updated} parts terisi section_ref")

# 2. Isi diagram_page berdasarkan section (section N -> page 2N-1)
cur.execute("SELECT DISTINCT section_ref FROM parts WHERE machine_id=? AND section_ref IS NOT NULL ORDER BY section_ref", (MID,))
sections = [r[0] for r in cur.fetchall()]
for sec in sections:
    page = 2*sec - 1
    cur.execute("UPDATE parts SET diagram_page=? WHERE machine_id=? AND section_ref=?", (page, MID, sec))
print(f"[PAGE] {len(sections)} section: {sections}")

conn.commit()

# 3. Hapus relasi lama & rebuild
cur.execute("DELETE FROM component_parts WHERE component_id IN (SELECT id FROM components WHERE machine_id=?)", (MID,))
print(f"[HAPUS] relasi lama: {cur.rowcount}")

# Ambil komponen, isi diagram_page berdasarkan urutan
cur.execute("SELECT id, component_name FROM components WHERE machine_id=? ORDER BY id", (MID,))
comps = cur.fetchall()
print(f"[KOMPONEN] {len(comps)}")

# Relasikan: komponen ke-N -> section ke-N (jika jumlah cocok)
if len(comps) == len(sections):
    for (comp_id, cname), sec in zip(comps, sections):
        page = 2*sec - 1
        cur.execute("UPDATE components SET diagram_page=? WHERE id=?", (page, comp_id))
        cur.execute("SELECT id FROM parts WHERE machine_id=? AND section_ref=?", (MID, sec))
        for (pid,) in cur.fetchall():
            try:
                cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                               VALUES(?,?,'sub-part')""", (comp_id, pid))
            except sqlite3.IntegrityError:
                pass
    print(f"[RELASI] mapping 1:1 berhasil")
else:
    print(f"[WARN] jumlah komponen ({len(comps)}) != section ({len(sections)})")

conn.commit()
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[HASIL] total relasi: {cur.fetchone()[0]}")
conn.close()
