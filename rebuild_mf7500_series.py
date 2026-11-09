#!/usr/bin/env python3
"""Rebuild MF-7500-C11, MF-7500-E11, MF-7500-U11 dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_mf7500_hasil_parse.csv")
DB  = Path("database/garment.db")

MACHINES = [
    (28, "MF-7500-C11"),
    (29, "MF-7500-E11"),
    (9,  "MF-7500-U11"),
]

SECTIONS = {
    1:  ("1. MISCELLANEOUS COVER", "Cover", 1),
    2:  ("2. MAIN SHAFT", "Main shaft", 3),
    3:  ("3. THREAD TENSION", "Thread tension", 5),
    4:  ("4. LOOPER THREAD TRIMMER", "Looper thread trimmer", 7),
    5:  ("5. PNEUMATIC DRIVE & PRESSER FEED LIFTER", "Pneumatic & presser feed lifter", 9),
    6:  ("6. TOP COVER THREAD TRIMMER", "Top cover thread trimmer", 11),
    7:  ("7. AK SOLENOID", "AK solenoid", 12),
    8:  ("8. ACCESSORIES PARTS", "Accessories", 13),
}

with CSV.open(encoding="utf-8") as f:
    all_rows = list(csv.DictReader(f))

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for MID, model in MACHINES:
    print(f"\n=== {model} (id={MID}) ===")
    bak = DB.with_name(f"{DB.name}.backup-rebuild-{model.lower()}-{ts}")
    shutil.copy2(DB, bak)
    print(f"[BACKUP] {bak.name}")
    
    cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
    row = cur.fetchone()
    if not row or row[0] != model:
        print(f"[BATAL] machine_id={MID} bukan {model}")
        continue
    
    cur.execute("""DELETE FROM component_parts WHERE component_id IN
                   (SELECT id FROM components WHERE machine_id=?)""", (MID,))
    cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
    cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
    
    for r in all_rows:
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
        for pid, pn in cur.fetchall():
            rel = "matched_catalog_part" if pn == comp_pn else "sub-part"
            try:
                cur.execute("""INSERT INTO component_parts(component_id, part_id, relation_type)
                               VALUES(?,?,?)""", (comp_id, pid, rel))
                total += 1
            except sqlite3.IntegrityError:
                pass
    
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
    p = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
    c = cur.fetchone()[0]
    cur.execute("""SELECT COUNT(*) FROM component_parts cp
                   JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
    r = cur.fetchone()[0]
    print(f"[HASIL] parts={p}, komponen={c}, relasi={r}")

conn.close()
