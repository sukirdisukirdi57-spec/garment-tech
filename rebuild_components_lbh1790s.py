#!/usr/bin/env python3
"""Hapus komponen lama LBH-1790S, buat 17 komponen section-based."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 38

SECTIONS = {
    1:  ("1. FRAME & MISCELLANEOUS COVER COMPONENTS (1)", "Rangka & cover (1)", 1),
    2:  ("2. FRAME & MISCELLANEOUS COVER COMPONENTS (2)", "Rangka & cover (2)", 3),
    3:  ("3. MAIN SHAFT COMPONENTS", "Poros utama", 5),
    4:  ("4. HOOK DRIVING SHAFT COMPONENTS", "Hook driving shaft", 7),
    5:  ("5. PRESSER & FEED COMPONENTS", "Presser & feed", 9),
    6:  ("6. NEEDLE BAR ROCKING COMPONENTS", "Needle bar rocking", 11),
    7:  ("7. NEEDLE THREAD TRIMMER COMPONENTS", "Needle thread trimmer", 13),
    8:  ("8. BOBBIN THREAD TRIMMER COMPONENTS", "Bobbin thread trimmer", 15),
    9:  ("9. CLOTH CUTTING KNIFE COMPONENTS", "Cloth cutting knife", 17),
    10: ("10. TABLE COMPONENTS", "Meja", 19),
    11: ("11. OPERATION BOX COMPONENTS", "Operation box", 21),
    12: ("12. CONTROL BOX COMPONENTS", "Control box", 23),
    14: ("14. ACCESSORIE PARTS COMPONENTS", "Aksesoris", 27),
    15: ("15. THREAD STAND COMPONENTS", "Thread stand", 29),
    16: ("16. SPECIAL SPECIFICATIONS COMPONENTS (1)", "Spesifikasi khusus (1)", 31),
    17: ("17. SPECIAL SPECIFICATIONS COMPONENTS (2)", "Spesifikasi khusus (2)", 33),
    18: ("18. EXCHANGING PARTS", "Part pengganti", 35),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-components-lbh1790s-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Hapus komponen lama
cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
print(f"[HAPUS] komponen lama: {cur.rowcount}")

# Buat baru
for ref, (name, location, page) in SECTIONS.items():
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY catalog_ref LIMIT 1""", (MID, ref))
    row = cur.fetchone()
    main_pn = row[0] if row else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, location, str(ref), page))

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[HASIL] komponen baru: {cur.fetchone()[0]}")
conn.close()
