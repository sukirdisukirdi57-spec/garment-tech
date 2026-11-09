#!/usr/bin/env python3
"""Rebuild Z-8550A & Z-8560A dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_z8550a_hasil_parse.csv")
DB  = Path("database/garment.db")

MACHINES = [
    (98, "Z-8550A"),
    (99, "Z-8560A"),
]

SECTIONS = {
    "A":  ("A. Machine body", "Badan mesin", 1),
    "B":  ("B. Needle bar & thread take-up", "Needle bar & take-up", 3),
    "C":  ("C. Zigzag mechanism", "Zigzag mechanism", 7),
    "D":  ("D. Presser foot mechanism", "Presser foot", 9),
    "E":  ("E. Feed mechanism", "Feed mechanism", 11),
    "F":  ("F. Knee lifter mechanism", "Knee lifter", 17),
    "G":  ("G. Quick reverse mechanism", "Quick reverse", 19),
    "H":  ("H. Rotary hook mechanism", "Rotary hook", 21),
    "J":  ("J. Lubrication", "Lubrication", 23),
    "K":  ("K. Threading mechanism", "Threading", 27),
    "L":  ("L. Bobbin winder mechanism", "Bobbin winder", 29),
    "M1": ("M1. Thread trimmer mechanism (1)", "Thread trimmer (1)", 31),
    "M2": ("M2. Thread trimmer mechanism (2)", "Thread trimmer (2)", 33),
    "N":  ("N. Tension release mechanism", "Tension release", 35),
    "P":  ("P. Thread wiper mechanism", "Thread wiper", 37),
    "Q1": ("Q1. Control box & motor", "Control box & motor", 39),
    "Q2": ("Q2. Control box mechanism", "Control box (2)", 41),
    "Q3": ("Q3. Control box mechanism", "Control box (3)", 43),
    "R":  ("R. Knee switch mechanism", "Knee switch", 45),
    "S":  ("S. Quick reverse switch", "Quick reverse switch", 47),
    "T":  ("T. Presser foot lifting solenoid", "Presser foot lifting solenoid", 49),
    "Z":  ("Z. Accessories", "Accessories", 51),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

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
        sec = r["section_ref"]
        sec_num = SECTION_ORDER.get(sec, 0)
        cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                       quantity, catalog_ref, diagram_page, section_ref, section_name)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (MID, r["part_number"], r["part_name"], qty,
                     int(r["catalog_ref"]), int(r["diagram_page"]),
                     sec_num, SECTIONS[sec][0]))
    
    for sec, (name, loc, page) in SECTIONS.items():
        sec_num = SECTION_ORDER[sec]
        cur.execute("""SELECT part_number FROM parts
                       WHERE machine_id=? AND section_ref=?
                       ORDER BY catalog_ref LIMIT 1""", (MID, sec_num))
        r = cur.fetchone()
        main_pn = r[0] if r else None
        cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                       location, catalog_ref, diagram_page)
                       VALUES(?,?,?,?,?,?)""",
                    (MID, name, main_pn, loc, str(sec_num), page))
    
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
