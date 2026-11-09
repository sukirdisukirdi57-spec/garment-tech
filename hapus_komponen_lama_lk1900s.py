#!/usr/bin/env python3
"""Hapus 25 komponen lama LK-1900S yang tidak terpakai."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 37

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-hapus-komponen-lk1900s-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
before = cur.fetchone()[0]

# Pastikan tidak ada relasi
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id
               WHERE c.machine_id=?""", (MID,))
rel = cur.fetchone()[0]
if rel > 0:
    raise SystemExit(f"BATAL: ada {rel} relasi, tidak aman dihapus")

cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
deleted = cur.rowcount
conn.commit()

cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
after = cur.fetchone()[0]
print(f"[HASIL] dihapus={deleted}, sebelum={before}, sesudah={after}")
conn.close()
