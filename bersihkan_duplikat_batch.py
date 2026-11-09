#!/usr/bin/env python3
"""Bersihkan duplikat relasi AMS-224EN-4530 (46) & LBH-1790AN (6)."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINES = [(46, "AMS-224EN-4530"), (6, "LBH-1790AN")]

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-bersihkan-duplikat-batch-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for MID, model in MACHINES:
    print(f"=== {model} (id={MID}) ===")
    cur.execute("""SELECT part_id FROM component_parts cp
                   JOIN components c ON c.id=cp.component_id
                   WHERE c.machine_id=?
                   GROUP BY part_id HAVING COUNT(*)>1""", (MID,))
    dup_parts = [r[0] for r in cur.fetchall()]
    print(f"[DUPLIKAT] {len(dup_parts)} parts")
    
    deleted = 0
    for pid in dup_parts:
        cur.execute("""SELECT cp.id FROM component_parts cp
                       JOIN components c ON c.id=cp.component_id
                       WHERE c.machine_id=? AND cp.part_id=?
                       ORDER BY cp.component_id""", (MID, pid))
        rows = cur.fetchall()
        for (row_id,) in rows[1:]:
            cur.execute("DELETE FROM component_parts WHERE id=?", (row_id,))
            deleted += 1
    print(f"[HAPUS] {deleted} relasi duplikat")
    
    cur.execute("""SELECT 
      (SELECT COUNT(*) FROM component_parts cp JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?) AS total_rel,
      (SELECT COUNT(*) FROM parts WHERE machine_id=?) AS total_parts""", (MID, MID))
    r = cur.fetchone()
    print(f"[HASIL] relasi: {r[0]}, parts: {r[1]}\n")

conn.commit()
conn.close()
print("[SELESAI]")
