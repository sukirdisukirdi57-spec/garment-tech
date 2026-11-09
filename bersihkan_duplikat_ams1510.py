#!/usr/bin/env python3
"""Hapus duplikat relasi AMS-210EN-1510 (simpan 1 per part)."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 15

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-bersihkan-duplikat-ams1510-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Ambil parts duplikat
cur.execute("""SELECT part_id FROM component_parts cp
               JOIN components c ON c.id=cp.component_id
               WHERE c.machine_id=?
               GROUP BY part_id HAVING COUNT(*)>1""", (MID,))
dup_parts = [r[0] for r in cur.fetchall()]
print(f"[DUPLIKAT] {len(dup_parts)} parts")

# Untuk tiap part duplikat, simpan relasi dengan component_id terkecil, hapus sisanya
deleted = 0
for pid in dup_parts:
    cur.execute("""SELECT cp.id, cp.component_id FROM component_parts cp
                   JOIN components c ON c.id=cp.component_id
                   WHERE c.machine_id=? AND cp.part_id=?
                   ORDER BY cp.component_id""", (MID, pid))
    rows = cur.fetchall()
    # Simpan yang pertama, hapus sisanya
    for row_id, comp_id in rows[1:]:
        cur.execute("DELETE FROM component_parts WHERE id=?", (row_id,))
        deleted += 1

conn.commit()
print(f"[HAPUS] {deleted} relasi duplikat")

cur.execute("""SELECT 
  (SELECT COUNT(*) FROM component_parts cp JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?) AS total_rel,
  (SELECT COUNT(DISTINCT part_id) FROM component_parts cp JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?) AS parts_unik""", (MID, MID))
row = cur.fetchone()
print(f"[HASIL] total relasi: {row[0]}, parts unik: {row[1]}")
conn.close()
