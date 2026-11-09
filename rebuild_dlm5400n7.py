#!/usr/bin/env python3
"""Rebuild parts + komponen + relasi DLM-5400N-7 (id=223)."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_dlm5400n7_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 223
EXPECTED_MODEL = "DLM-5400N-7"

SECTIONS = {
    1:  ("1. MACHINE FRAME & MISCELLANEOUS COVER COMPONENTS", "Rangka & cover", 1),
    2:  ("2. MAIN SHAFT & THREAD TAKE-UP LEVER COMPONENTS", "Poros utama & take-up", 3),
    3:  ("3. NEEDLE BAR, UPRIGHT SHAFT & HOOK DRIVING SHAFT COMPONENTS", "Needle bar & hook", 5),
    4:  ("4. HAND LIFTER COMPONENTS", "Hand lifter", 7),
    5:  ("5. FEED MECHANISM COMPONENTS", "Mekanisme feed", 9),
    6:  ("6. THREAD TRIMMER MECHANISM COMPONENTS", "Thread trimmer", 11),
    7:  ("7. KNIFE COMPONENTS", "Knife", 13),
    8:  ("8. AUTOMATIC REVERSE FEED COMPONENTS", "Reverse feed", 15),
    9:  ("9. WIPER COMPONENTS", "Wiper", 16),
    10: ("10. OIL LUBRICATION COMPONENTS", "Pelumasan", 17),
    11: ("11. OIL RESERVOIR COMPONENTS", "Oil reservoir", 19),
    12: ("12. BELT COVER & BOBBIN WINDER COMPONENTS", "Belt cover & bobbin winder", 21),
    13: ("13. THREAD STAND COMPONENTS", "Thread stand", 22),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-dlm5400n7-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
row = cur.fetchone()
if not row or row[0] != EXPECTED_MODEL:
    raise SystemExit(f"BATAL: machine_id={MID} bukan {EXPECTED_MODEL}")

cur.execute("""DELETE FROM component_parts WHERE component_id IN
               (SELECT id FROM components WHERE machine_id=?)""", (MID,))
cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
print("[HAPUS] parts & komponen lama")

with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    qty_clean = r["quantity"].strip("()")
    try:
        qty = int(float(qty_clean)) if qty_clean else None
    except ValueError:
        qty = None
    sec = int(r["section_ref"])
    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page, section_ref, section_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (MID, r["part_number"], r["part_name"], qty,
                 int(r["catalog_ref"]), int(r["diagram_page"]),
                 sec, SECTIONS[sec][0]))

conn.commit()
print(f"[PARTS] {len(rows)} inserted")

for ref, (name, loc, page) in SECTIONS.items():
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY catalog_ref LIMIT 1""", (MID, ref))
    r = cur.fetchone()
    main_pn = r[0] if r else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, loc, str(ref), page))

conn.commit()

cur.execute("SELECT id, catalog_ref, part_number FROM components WHERE machine_id=?", (MID,))
comps = {int(r[1]): (r[0], r[2]) for r in cur.fetchall()}
total = 0
for ref, (comp_id, comp_pn) in sorted(comps.items()):
    cur.execute("SELECT id, part_number FROM parts WHERE machine_id=? AND section_ref=?", (MID, ref))
    parts = cur.fetchall()
    for pid, pn in parts:
        rel = "matched_catalog_part" if pn == comp_pn else "sub-part"
        try:
            cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                           VALUES(?,?,?)""", (comp_id, pid, rel))
            total += 1
        except sqlite3.IntegrityError:
            pass

conn.commit()
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[KOMPONEN] {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[RELASI] {cur.fetchone()[0]}")
conn.close()
