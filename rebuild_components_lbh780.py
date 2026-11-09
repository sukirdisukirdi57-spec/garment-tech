#!/usr/bin/env python3
"""Rebuild komponen section-based LBH-780."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 39

SECTIONS = {
    1:  ("1. LBH-772NV-1,LBH-782NV (1)", "LBH-772NV/782NV (1)", 1),
    2:  ("2. LBH-772NV-1,LBH-782NV (2)", "LBH-772NV/782NV (2)", 3),
    3:  ("3. LBH-772NV-1,LBH-782NV (3)", "LBH-772NV/782NV (3)", 5),
    4:  ("4. LBH-773NV-1,LBH-783NV", "LBH-773NV/783NV", 7),
    5:  ("5. LBH-774NV-1,LBH-784NV", "LBH-774NV/784NV", 8),
    6:  ("6. LBH-772NB-1,LBH-782NB", "LBH-772NB/782NB", 9),
    7:  ("7. LBH-773NB-1,LBH-783NB", "LBH-773NB/783NB", 11),
    8:  ("8. LBH-774NB-1,LBH-784NB", "LBH-774NB/784NB", 12),
    9:  ("9. THREAD STAND COMPONENTS", "Thread stand", 13),
    10: ("10. SEMI-CIRCULAR BARTACKING", "Semi-circular bartacking", 15),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-components-lbh780-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
print(f"[HAPUS] komponen lama: {cur.rowcount}")

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
