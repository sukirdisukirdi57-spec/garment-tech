#!/usr/bin/env python3
"""Rebuild LK-1900C & LK-1903C dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_lk1900c_hasil_parse.csv")
DB  = Path("database/garment.db")

MODELS = {
    8: ("LK-1900C", {1,2,3,4,5,6,7,8,10,11,12,13,14,16,17,18,19,30,31,32,33,34,35,36,37,38}),
    42: ("LK-1903C", {1,2,3,4,5,6,7,8,10,11,12,13,14,16,20,21,22,23,24,25,30,31,32,33,34}),
}

SECTIONS = {
    1:  ("1. FRAME & MISC COVER (1)", "Frame & cover (1)", 1),
    2:  ("2. FRAME & MISC COVER (2)", "Frame & cover (2)", 3),
    3:  ("3. MAIN SHAFT & NEEDLE BAR", "Main shaft & needle bar", 5),
    4:  ("4. PRESSER LIFTER & WIPER", "Presser lifter & wiper", 7),
    5:  ("5. SHUTTLE DRIVER SHAFT", "Shuttle driver shaft", 9),
    6:  ("6. THREAD TENSION", "Thread tension", 11),
    7:  ("7. THREAD TRIMMER MECHANISM", "Thread trimmer", 13),
    8:  ("8. FEED MECHANISM", "Feed mechanism", 15),
    10: ("10. THREAD STAND", "Thread stand", 19),
    11: ("11. TABLE STAND (JT-K47)", "Table stand", 21),
    12: ("12. CONTROL BOX", "Control box", 23),
    13: ("13. OPERATION PANEL", "Operation panel", 25),
    14: ("14. MARKING LIGHT", "Marking light", 27),
    16: ("16. ACCESSORIE PARTS", "Accessories", 31),
    17: ("17. EXCLUSIVE LK-1901CS (1)", "Exclusive LK-1901CS (1)", 33),
    18: ("18. EXCLUSIVE LK-1901CS (2)", "Exclusive LK-1901CS (2)", 35),
    19: ("19. EXCLUSIVE LK-1902CS/CH", "Exclusive LK-1902CS/CH", 37),
    20: ("20. EXCLUSIVE LK-1903CS (1)", "Exclusive LK-1903CS (1)", 39),
    21: ("21. EXCLUSIVE LK-1903CS (2)", "Exclusive LK-1903CS (2)", 41),
    22: ("22. EXCLUSIVE LK-1903C-B (1)", "Exclusive LK-1903C-B (1)", 43),
    23: ("23. EXCLUSIVE LK-1903C-B (2)", "Exclusive LK-1903C-B (2)", 45),
    24: ("24. EXCLUSIVE LK-1903C-B (3)", "Exclusive LK-1903C-B (3)", 47),
    25: ("25. EXCLUSIVE LK-1903C-B (4)", "Exclusive LK-1903C-B (4)", 49),
    30: ("30. ACCESSORIE SUBCLASSES", "Accessories subclasses", 59),
    31: ("31. OPTION (1)", "Option (1)", 61),
    32: ("32. OPTION (2)", "Option (2)", 63),
    33: ("33. OPTION (3)", "Option (3)", 65),
    34: ("34. OPTION (4)", "Option (4)", 67),
    35: ("35. OPTION (5)", "Option (5)", 69),
    36: ("36. OPTION (6)", "Option (6)", 71),
    37: ("37. OPTION (7)", "Option (7)", 73),
    38: ("38. OPTION (8)", "Option (8)", 75),
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
