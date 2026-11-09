#!/usr/bin/env python3
"""Isi katalog jarum: base + sister (dengan backup & verifikasi)."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-isi-jarum-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ========== TAHAP 1: Tambah sistem baru ==========
NEW_SYSTEMS = [
    ('DP×5', 'TNC', 'Chainstitch', 'Mesin jahit rantai'),
    ('UY×128', 'Groz-Beckert', 'Chainstitch', 'Mesin jahit rantai'),
]
print("=== TAHAP 1: Tambah sistem baru ===")
for code, mfr, stitch, cat in NEW_SYSTEMS:
    cur.execute("SELECT COUNT(*) FROM needle_systems WHERE system_code=?", (code,))
    if cur.fetchone()[0] > 0:
        print(f"  {code:10} SKIP (sudah ada)")
        continue
    cur.execute("""INSERT INTO needle_systems
        (system_code, manufacturer, stitch_type, machine_category, verification_status)
        VALUES(?,?,?,?, 'Belum diverifikasi')""",
        (code, mfr, stitch, cat))
    print(f"  {code:10} ✅ added (id={cur.lastrowid})")
conn.commit()

# ========== TAHAP 2: Isi base dengan ukuran standar ==========
BASE_SIZES = {
    'DC×1':  ['NM 65','NM 70','NM 75','NM 80','NM 85','NM 90','NM 100','NM 110','NM 120'],
    'DP×17': ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120','NM 130'],
    'DP×5':  ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120'],
    'DP×35': ['NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120'],
    'UY×128':['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120'],
    'DV×1':  ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120'],
    'DB×K5': ['NM 65','NM 70','NM 75','NM 80','NM 90','NM 100','NM 110','NM 120'],
}
BRAND_BASE = {
    'DC×1': 'TNC', 'DP×17': 'Groz-Beckert', 'DP×5': 'TNC',
    'DP×35': 'Groz-Beckert', 'UY×128': 'Groz-Beckert',
    'DV×1': 'TNC', 'DB×K5': 'Groz-Beckert',
}

print("\n=== TAHAP 2: Isi base dengan ukuran standar ===")
total_base = 0
for sys, sizes in BASE_SIZES.items():
    cur.execute("SELECT COUNT(*) FROM needles WHERE needle_system=?", (sys,))
    if cur.fetchone()[0] > 0:
        print(f"  {sys:10} SKIP (sudah ada varian)")
        continue
    brand = BRAND_BASE[sys]
    for size in sizes:
        # Extract numeric value dari "NM XX"
        m = size.replace("NM ", "")
        try: nm_val = float(m)
        except: nm_val = None
        cur.execute("""INSERT INTO needles
            (brand, needle_system, size_nm, size_nm_value, verification_status)
            VALUES(?,?,?,?, 'Belum diverifikasi')""",
            (brand, sys, size, nm_val))
        total_base += 1
    print(f"  {sys:10} ✅ {len(sizes)} ukuran ditambahkan")
conn.commit()
print(f"  Total base: {total_base}")

# ========== TAHAP 3: Duplikasi sister ==========
SISTER_MAP = {
    'DB×1': ['DB×1 KN', 'BQ×1', 'DB×1 HEM ST', 'DB×1 MU', 'DB×A20', 'DB×F2', 'DB×F17', 'DB-N19', 'DB×1KK', 'DB×1++'],
    '134':  ['134 CL', '134 D', '134 DI', '134 LL', '134 LR', '134 PCL', '134 S',
             '134-35 CL', '134-35 R', '134-35 LR', '134-35 S', '134-35 D', '134-35 PCL',
             '134-35', '134-35 MR'],
    'DB×K5': ['DB×K5 PVD', 'DB×K5 CM'],
    'DC×1':  ['DC×1 F', 'DC×1 KN'],
    'DP×17': ['DP×17 CL', 'DP×17 LR', 'DP×17 S', 'DP×17KK', 'DP×17++'],
    'DP×5':  ['DP×5 KK', 'DP×5 KN', 'DP×5 USP', 'DP×5++'],
    'UY×128':['UY×128KK', 'UY×128KK-KN', 'UY×128GASKN', 'UY×128GAS-SK'],
    'DP×35': ['DP×35R++', 'DP×35R-SK'],
}

print("\n=== TAHAP 3: Duplikasi sister ===")
total_sister = 0
for base, sisters in SISTER_MAP.items():
    cur.execute("""SELECT brand, size_nm, size_nm_value, point_code,
                   point_description, material_application
                   FROM needles WHERE needle_system=?""", (base,))
    base_rows = cur.fetchall()
    if not base_rows:
        print(f"  {base:10} SKIP (base kosong)")
        continue
    for sister in sisters:
        cur.execute("SELECT COUNT(*) FROM needles WHERE needle_system=?", (sister,))
        if cur.fetchone()[0] > 0:
            print(f"  {sister:20} SKIP (sudah ada)")
            continue
        added = 0
        for row in base_rows:
            brand, size_nm, size_val, point, point_desc, material = row
            # Brand: kalau base TNC, sister TNC. Kalau ORGAN, sister ORGAN. Kalau base SCHMETZ, sister TNC
            sister_brand = brand if brand in ('TNC', 'ORGAN') else 'TNC'
            try:
                cur.execute("""INSERT INTO needles
                    (brand, needle_system, size_nm, size_nm_value, point_code,
                     point_description, material_application, verification_status)
                    VALUES(?,?,?,?,?,?,?, 'Belum diverifikasi')""",
                    (sister_brand, sister, size_nm, size_val, point, point_desc, material))
                added += 1
            except sqlite3.IntegrityError:
                pass
        total_sister += added
        print(f"  {sister:20} ✅ {added} varian dari {base}")
conn.commit()
print(f"  Total sister: {total_sister}")

# ========== VERIFIKASI ==========
print("\n=== VERIFIKASI ===")
cur.execute("SELECT COUNT(*) FROM needles")
print(f"Total needles: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM needle_systems")
print(f"Total needle_systems: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(DISTINCT needle_system) FROM needles ns
               WHERE EXISTS (SELECT 1 FROM needle_systems s WHERE s.system_code = ns.needle_system)""")
print(f"Sistem dengan varian: {cur.fetchone()[0]}")

conn.close()
print(f"\n>>> TOTAL BARU: {total_base + total_sister} varian")
