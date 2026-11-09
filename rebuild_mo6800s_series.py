#!/usr/bin/env python3
"""Rebuild 6 mesin MO-6800S series dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_mo6800s_hasil_parse.csv")
DB  = Path("database/garment.db")

BASE_SECTIONS = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,21,22,23,24,25,32,33,34}

MODELS = {
    22: ("MO-6804S", BASE_SECTIONS | {17}),
    23: ("MO-6814S", BASE_SECTIONS | {18}),
    24: ("MO-6816S", BASE_SECTIONS | {19}),
    25: ("MO-6843S", BASE_SECTIONS | {20}),
    26: ("MO-6904S", BASE_SECTIONS),
    27: ("MO-6914S", BASE_SECTIONS),
}

SECTIONS = {
    1:  ("1. MISC COVER (1)", "Misc cover (1)", 1),
    2:  ("2. MISC COVER (2)", "Misc cover (2)", 3),
    3:  ("3. MISC COVER (3)", "Misc cover (3)", 5),
    4:  ("4. CRANKSHAFT", "Crankshaft", 7),
    5:  ("5. NEEDLE DRIVING SHAFT", "Needle driving shaft", 9),
    6:  ("6. THREAD TENSION", "Thread tension", 11),
    7:  ("7. UPPER LOOPER", "Upper looper", 13),
    8:  ("8. LOWER LOOPER", "Lower looper", 15),
    9:  ("9. CHAIN LOOPER (1)", "Chain looper (1)", 17),
    10: ("10. CHAIN LOOPER (2)", "Chain looper (2)", 19),
    11: ("11. FEED MECHANISM (1)", "Feed mechanism (1)", 21),
    12: ("12. FEED MECHANISM (2)", "Feed mechanism (2)", 23),
    13: ("13. KNIFE", "Knife", 25),
    14: ("14. PRESSER FOOT", "Presser foot", 27),
    15: ("15. LUBRICATION MECHANISM", "Lubrication", 29),
    16: ("16. NEEDLE COOLER UNIT", "Needle cooler unit", 31),
    17: ("17. THREAD STAND (MO-6804S)", "Thread stand (6804S)", 33),
    18: ("18. THREAD STAND (MO-6814S)", "Thread stand (6814S)", 35),
    19: ("19. THREAD STAND (MO-6816S)", "Thread stand (6816S)", 37),
    20: ("20. THREAD STAND (MO-6843S)", "Thread stand (6843S)", 39),
    21: ("21. SEMI-SUNKEN TABLE", "Semi-sunken table", 41),
    22: ("22. FULLY-SUNKEN TABLE", "Fully-sunken table", 43),
    23: ("23. ACCESSORIES PARTS", "Accessories", 45),
    24: ("24. PSC UNIT", "PSC unit", 47),
    25: ("25. TAPE INSERTION", "Tape insertion", 49),
    32: ("32. AUTOMATIC HAND LIFTER", "Automatic hand lifter", 63),
    33: ("33. THREAD TRIMMER", "Thread trimmer", 65),
    34: ("34. DUST COLLECTOR", "Dust collector", 67),
}

with CSV.open(encoding="utf-8") as f:
    all_rows = list(csv.DictReader(f))

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for MID, (model, allowed) in MODELS.items():
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
    
    rows = [r for r in all_rows if int(r["section_ref"]) in allowed]
    
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
    
    used = sorted(set(int(r["section_ref"]) for r in rows))
    for ref in used:
        name, loc, page = SECTIONS[ref]
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
