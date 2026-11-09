#!/usr/bin/env python3
"""Isi katalog jarum v2: base baru + sister."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-isi-jarum-v2-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ========== BASE BARU (belum ada varian) ==========
NEW_BASES = {
    'DC×27':   ('Groz-Beckert', ['NM 65','NM 70','NM 75','NM 80','NM 85','NM 90','NM 100','NM 110','NM 120']),
    'UO×113':  ('ORGAN',        ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120']),
    'UY 113':  ('Groz-Beckert', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120']),
    'UY 118':  ('Groz-Beckert', ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120']),
    'DB×9':    ('TNC',          ['NM 65','NM 70','NM 75','NM 80','NM 85','NM 90','NM 100','NM 110','NM 120','NM 130']),
    'DB×287':  ('TNC',          ['NM 65','NM 70','NM 75','NM 80','NM 85','NM 90','NM 100','NM 110','NM 120','NM 130']),
    'SH×3':    ('TNC',          ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120','NM 130']),
    'PF×134KK':('ORGAN',        ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120','NM 130']),
    '130/705 H':('SCHMETZ',     ['NM 60','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120']),
}

print("=== BASE BARU ===")
total_base = 0
for sys, (brand, sizes) in NEW_BASES.items():
    cur.execute("SELECT COUNT(*) FROM needles WHERE needle_system=?", (sys,))
    if cur.fetchone()[0] > 0:
        print(f"  {sys:12} SKIP (sudah ada varian)")
        continue
    for size in sizes:
        nm_val = float(size.replace("NM ", ""))
        try:
            cur.execute("""INSERT INTO needles
                (brand, needle_system, size_nm, size_nm_value, verification_status)
                VALUES(?,?,?,?, 'Belum diverifikasi')""",
                (brand, sys, size, nm_val))
            total_base += 1
        except sqlite3.IntegrityError:
            pass
    print(f"  {sys:12} ✅ {len(sizes)} ukuran")
conn.commit()
print(f"  Total base: {total_base}\n")

# ========== SISTER BARU ==========
SISTERS = {
    'DC×27':    ['DC×27++'],
    'UO×113':   ['UO×113 GS', 'UO×163 GAS'],
    'UY 113':   ['UY 113 GS SES', 'UY×113'],
    'UY 118':   ['UY 118 GKS'],
    'DB×9':     ['DB×9 ST'],
    'DB×287':   ['DB×287 WKH'],
    'SH×3':     ['SH×3 TOP'],
    'PF×134KK': ['PF×134KKD', 'PF×134KKLR', 'PF×134KKPCL'],
    '130/705 H':['130/705 H-J', '130/705 H-M', '130/705 H-S', '130/705 H-SUK', '130/705 H-LR'],
    'DV×1':     ['DV×1 (L)', 'DV×1 (R)'],
    'UY×128':   ['UY×128 GAS', 'UY×128GAS++'],
}

print("=== SISTER ===")
total_sister = 0
for base, sisters in SISTERS.items():
    cur.execute("""SELECT brand, size_nm, size_nm_value, point_code,
                   point_description, material_application
                   FROM needles WHERE needle_system=?""", (base,))
    base_rows = cur.fetchall()
    if not base_rows:
        print(f"  {base:12} SKIP (base kosong)")
        continue
    for sister in sisters:
        cur.execute("SELECT COUNT(*) FROM needles WHERE needle_system=?", (sister,))
        if cur.fetchone()[0] > 0:
            print(f"  {sister:20} SKIP")
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
        total_sister += added
        print(f"  {sister:20} ✅ {added} dari {base}")
conn.commit()

# Verifikasi
cur.execute("SELECT COUNT(*) FROM needles")
print(f"\n[TOTAL] needles: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(DISTINCT n.needle_system) FROM needles n
               WHERE n.needle_system IN (SELECT system_code FROM needle_systems)""")
print(f"[TOTAL] sistem punya varian: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM needle_systems ns
               WHERE ns.system_code NOT IN (SELECT DISTINCT needle_system FROM needles)""")
print(f"[SISA] sistem tanpa varian: {cur.fetchone()[0]}")
conn.close()
print(f"\n>>> BARU: base={total_base}, sister={total_sister}")
