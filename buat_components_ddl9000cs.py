#!/usr/bin/env python3
"""Buat 15 komponen untuk DDL-9000C-S berdasarkan section partslist."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB  = Path("database/garment.db")
MID = 17

# section_ref, component_name, location, diagram_page
SECTIONS = [
    (1,  "1. MACHINE FRAME & MISCELLANEOUS COVER COMPONENTS", "Rangka mesin & cover", 1),
    (2,  "2. BOBBIN WINDER COMPONENTS", "Mekanisme bobbin winder", 3),
    (3,  "3. MAIN SHAFT & NEEDLE BAR COMPONENTS", "Poros utama & batang jarum", 5),
    (4,  "4. HAND LIFTER & TENSION RELEASE COMPONENTS", "Hand lifter & tension release", 7),
    (5,  "5. FEED ADJUST MECHANISM COMPONENTS", "Mekanisme feed adjust", 9),
    (6,  "6. VERTICAL FEED COMPONENTS", "Vertical feed", 11),
    (7,  "7. HOOK DRIVING COMPONENTS", "Hook driving", 13),
    (8,  "8. THREAD TRIMMER COMPONENTS", "Thread trimmer", 15),
    (9,  "9. OIL LUBRICATION COMPONENTS", "Pelumasan", 17),
    (10, "10. AUTOMATIC REVERSE FEED COMPONENTS", "Reverse feed otomatis", 19),
    (11, "11. OPERATION PANEL COMPONENTS", "Panel operasi", 20),
    (12, "12. THREAD STAND COMPONENTS", "Thread stand", 21),
    (13, "13. UNDER COVER COMPONENTS", "Under cover", 22),
    (14, "14. ACCESSORIE PART COMPONENTS", "Aksesoris", 23),
    (16, "16. TABLE & STAND COMPONENTS", "Meja & stand", 25),
]

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-components-ddl9000cs-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Cek apakah sudah ada komponen
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
if cur.fetchone()[0] > 0:
    raise SystemExit(f"BATAL: mesin {MID} sudah punya komponen")

inserted = 0
for ref, name, location, page in SECTIONS:
    # Part utama section = part dengan catalog_ref terkecil di section itu
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY catalog_ref LIMIT 1""", (MID, ref))
    row = cur.fetchone()
    main_pn = row[0] if row else None

    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, location, str(ref), page))
    inserted += 1

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[HASIL] {inserted} komponen dibuat, total di DB: {cur.fetchone()[0]}")

conn.close()
