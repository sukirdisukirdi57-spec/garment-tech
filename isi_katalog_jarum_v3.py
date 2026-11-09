#!/usr/bin/env python3
"""Isi sisa sistem jarum: keluarga + sister + single."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-isi-jarum-v3-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

def insert_sizes(system, brand, sizes, method='base'):
    cur.execute("SELECT COUNT(*) FROM needles WHERE needle_system=?", (system,))
    if cur.fetchone()[0] > 0:
        print(f"  {system:15} SKIP (sudah {cur.fetchone()[0] if False else 'ada varian'})")
        return 0
    added = 0
    for size in sizes:
        try:
            nm_val = float(size.replace("NM ", ""))
            cur.execute("""INSERT INTO needles
                (brand, needle_system, size_nm, size_nm_value, verification_status)
                VALUES(?,?,?,?, 'Belum diverifikasi')""",
                (brand, system, size, nm_val))
            added += 1
        except sqlite3.IntegrityError:
            pass
    print(f"  {system:15} ✅ {added} ukuran ({method})")
    return added

# ===== A. Keluarga base baru (6-7 size standar) =====
FAMILIES = {
    'TV×1':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110']),
    'TV×5':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110']),
    'TV×7':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110']),
    'TV×64': ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110']),
    'TQ×1':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'TQ×7':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'TQ×9':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'LW×2T': ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'LW×3T': ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'LW×5T': ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'LW×6T': ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DO×5':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DO×558':('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'EB×1':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'EB×755':('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    '149×5': ('Groz-Beckert', ['NM 70','NM 80','NM 90','NM 100','NM 110']),
    '149×7': ('Groz-Beckert', ['NM 70','NM 80','NM 90','NM 100','NM 110']),
    'MY 1014 H': ('Groz-Beckert', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'MY1014B': ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
}

# ===== B. Single sistem (3-6 size) =====
SINGLE = {
    'DD×1':   ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DH×1':   ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DI×3':   ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DM×13':  ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DN×1':   ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DP×1':   ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DP×1958':('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DP×438KK':('ORGAN', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'DV×63':  ('Groz-Beckert', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'UY 36211': ('Groz-Beckert', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    '135×17': ('SCHMETZ', ['NM 70','NM 80','NM 90','NM 100']),
    '579':    ('Groz-Beckert', ['NM 70','NM 80','NM 90']),
    '62×57 MR': ('Groz-Beckert', ['NM 70','NM 80','NM 90']),
    'B27':    ('Groz-Beckert', ['NM 70','NM 80','NM 90']),
    'MT190':  ('TNC', ['NM 70','NM 80','NM 90']),
    'FL×118KK': ('ORGAN', ['NM 70','NM 80','NM 90']),
    'UN×154': ('TNC', ['NM 70','NM 80','NM 90','NM 100']),
    'UY×121 GBS': ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
    'UY×154 GAS': ('TNC', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100']),
}

# ===== C. Sister dari base yang ada =====
SISTERS = {
    'UY×128': ['UY 128', 'UY 128 GAS'],
}

total = 0

print("=== A. KELUARGA BASE BARU ===")
for sys, (brand, sizes) in FAMILIES.items():
    total += insert_sizes(sys, brand, sizes, method='family')

print("\n=== B. SINGLE SISTEM ===")
for sys, (brand, sizes) in SINGLE.items():
    total += insert_sizes(sys, brand, sizes, method='single')

print("\n=== C. SISTER dari base yang ada ===")
for base, sisters in SISTERS.items():
    cur.execute("""SELECT brand, size_nm, size_nm_value, point_code,
                   point_description, material_application
                   FROM needles WHERE needle_system=?""", (base,))
    base_rows = cur.fetchall()
    for sister in sisters:
        cur.execute("SELECT COUNT(*) FROM needles WHERE needle_system=?", (sister,))
        if cur.fetchone()[0] > 0:
            print(f"  {sister:15} SKIP")
            continue
        added = 0
        for row in base_rows:
            brand, size_nm, size_val, point, point_desc, material = row
            try:
                cur.execute("""INSERT INTO needles
                    (brand, needle_system, size_nm, size_nm_value, point_code,
                     point_description, material_application, verification_status)
                    VALUES(?,?,?,?,?,?,?, 'Belum diverifikasi')""",
                    (brand, sister, size_nm, size_val, point, point_desc, material))
                added += 1
            except sqlite3.IntegrityError:
                pass
        total += added
        print(f"  {sister:15} ✅ {added} dari {base}")

conn.commit()

# Verifikasi
cur.execute("SELECT COUNT(*) FROM needles")
print(f"\n[TOTAL] needles: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM needle_systems ns
               WHERE ns.system_code NOT IN (SELECT DISTINCT needle_system FROM needles)""")
print(f"[SISA] sistem kosong: {cur.fetchone()[0]}")
if cur.fetchone() is None:
    cur.execute("""SELECT ns.system_code FROM needle_systems ns
                   WHERE ns.system_code NOT IN (SELECT DISTINCT needle_system FROM needles)""")
    for row in cur.fetchall():
        print(f"  {row[0]}")
conn.close()
print(f"\n>>> BARU: {total} varian")
