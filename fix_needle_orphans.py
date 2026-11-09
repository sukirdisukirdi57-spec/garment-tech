#!/usr/bin/env python3
"""Fix orphan needle_systems: normalisasi format + tambah base."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-fix-needle-orphans-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. Tambah 2 sistem base ke needle_systems (yang sudah ada WKH/ST varian)
print("=== Tambah sistem base ===")
for code, mfr in [('DB×287', 'TNC'), ('DB×9', 'TNC')]:
    cur.execute("SELECT COUNT(*) FROM needle_systems WHERE system_code=?", (code,))
    if cur.fetchone()[0] > 0:
        print(f"  {code} SKIP")
        continue
    cur.execute("""INSERT INTO needle_systems
        (system_code, manufacturer, verification_status)
        VALUES(?,?, 'Belum diverifikasi')""", (code, mfr))
    print(f"  {code} ✅ added (id={cur.lastrowid})")
conn.commit()

# 2. Normalisasi format di needles
NORMALIZE = {
    'DB X 1':   'DB×1',
    'DB X 1KN': 'DB×1 KN',
    'DB X K5':  'DB×K5',
}

print("\n=== Normalisasi format di needles ===")
for old, new in NORMALIZE.items():
    cur.execute("SELECT id, brand, size_nm, point_code FROM needles WHERE needle_system=?", (old,))
    rows = cur.fetchall()
    if not rows:
        print(f"  {old:12} → {new:12} SKIP (tidak ada)")
        continue
    
    migrated = 0
    deleted = 0
    for r_id, brand, size_nm, point in rows:
        # Cek duplikat di target
        cur.execute("""SELECT id FROM needles
            WHERE needle_system=? AND brand=? AND size_nm=?
              AND COALESCE(point_code,'') = COALESCE(?, '')""",
            (new, brand, size_nm, point))
        if cur.fetchone():
            cur.execute("DELETE FROM needles WHERE id=?", (r_id,))
            deleted += 1
        else:
            cur.execute("UPDATE needles SET needle_system=? WHERE id=?", (new, r_id))
            migrated += 1
    print(f"  {old:12} → {new:12} migrated={migrated}, deleted_dup={deleted}")

conn.commit()

# 3. Verifikasi
cur.execute("""SELECT COUNT(*) FROM needle_systems ns
               WHERE ns.system_code NOT IN (SELECT DISTINCT needle_system FROM needles)""")
print(f"\n[SISA] sistem kosong: {cur.fetchone()[0]}")
if cur.fetchone() is None:
    cur.execute("""SELECT ns.system_code FROM needle_systems ns
                   WHERE ns.system_code NOT IN (SELECT DISTINCT needle_system FROM needles)""")
    print("  Sistem tanpa varian:")
    for row in cur.fetchall():
        print(f"    {row[0]}")

cur.execute("SELECT COUNT(*) FROM needles")
print(f"[TOTAL] needles: {cur.fetchone()[0]}")
conn.close()
