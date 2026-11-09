#!/usr/bin/env python3
"""Rebuild BAS-311HN-03S, BAS-311HX, BAS-326HX dari PDF Brother."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_bas311hn_hasil_parse.csv")
DB  = Path("database/garment.db")

# Section utama (semua mesin)
MAIN = {"A", "B", "E", "F", "G", "H", "J", "K", "L1", "L2", "M1", "M2", "N", "T1", "T2", "T3"}
# Section 311HN
S_311HN = MAIN | {"C1", "C3", "C5", "C6", "C7", "C9", "D1", "D2"}
# Section 326H
S_326H = MAIN | {"C2", "C4", "C5", "C8", "D1", "D3"}

MACHINES = [
    (227, "BAS-311HN-03S", S_311HN),
    (113, "BAS-311HX", S_311HN),
    (114, "BAS-326HX", S_326H),
]

SECTIONS = {
    "A":  ("A. Machine body", "Badan mesin", 1),
    "B":  ("B. Upper shaft & needle bar", "Upper shaft & needle bar", 3),
    "C1": ("C1. Feed mechanism (311HN)", "Feed (311HN)", 5),
    "C2": ("C2. Feed mechanism (326H)", "Feed (326H)", 7),
    "C3": ("C3. Feed mechanism (311HN)", "Feed (311HN) #3", 9),
    "C4": ("C4. Feed mechanism (326H)", "Feed (326H) #2", 11),
    "C5": ("C5. Feed mechanism", "Feed mechanism (umum)", 13),
    "C6": ("C6. Feed mechanism (311HN-0S)", "Feed (311HN-0S)", 15),
    "C7": ("C7. Feed mechanism (311HN-0A)", "Feed (311HN-0A)", 17),
    "C8": ("C8. Feed mechanism (326H)", "Feed (326H) #3", 19),
    "C9": ("C9. Feed mechanism (option)", "Feed (option)", 21),
    "D1": ("D1. Work clamp lifter mechanism", "Work clamp lifter", 23),
    "D2": ("D2. Work clamp lifter (311HN-0S)", "Work clamp lifter (311HN-0S)", 25),
    "D3": ("D3. Work clamp lifter (326H-0A)", "Work clamp lifter (326H-0A)", 27),
    "E":  ("E. Lower shaft mechanism", "Lower shaft", 29),
    "F":  ("F. Lubrication", "Lubrication", 31),
    "G":  ("G. Threading mechanism", "Threading", 35),
    "H":  ("H. Bobbin winder mechanism", "Bobbin winder", 37),
    "J":  ("J. Thread trimmer mechanism", "Thread trimmer", 39),
    "K":  ("K. Thread wiper mechanism", "Thread wiper", 43),
    "L1": ("L1. Tension release (digital)", "Tension release (digital)", 45),
    "L2": ("L2. Tension release (solenoid)", "Tension release (solenoid)", 47),
    "M1": ("M1. Control box", "Control box (1)", 49),
    "M2": ("M2. Control box", "Control box (2)", 51),
    "N":  ("N. Pneumatic components", "Pneumatic", 53),
    "T1": ("T1. Attachment set (option)", "Attachment set (1)", 61),
    "T2": ("T2. Attachment set (option)", "Attachment set (2)", 67),
    "T3": ("T3. Attachment set (option)", "Attachment set (3)", 69),
}

with CSV.open(encoding="utf-8") as f:
    all_rows = list(csv.DictReader(f))

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for MID, model, allowed in MACHINES:
    print(f"\n=== {model} (id={MID}) ===")
    bak = DB.with_name(f"{DB.name}.backup-rebuild-{model.lower()}-{ts}")
    shutil.copy2(DB, bak)
    print(f"[BACKUP] {bak.name}")
    
    cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
    row = cur.fetchone()
    if not row or row[0] != model:
        print(f"[BATAL] machine_id={MID} bukan {model} (dapat: {row})")
        continue
    
    cur.execute("""DELETE FROM component_parts WHERE component_id IN
                   (SELECT id FROM components WHERE machine_id=?)""", (MID,))
    cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
    cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
    
    rows = [r for r in all_rows if r["section_ref"] in allowed]
    
    used_sections = []
    for r in rows:
        if r["section_ref"] not in used_sections:
            used_sections.append(r["section_ref"])
    sec_order_list = [k for k in SECTIONS.keys() if k in used_sections]
    sec_order = {k: i+1 for i, k in enumerate(sec_order_list)}
    
    for r in rows:
        qty_clean = r["quantity"].strip("()")
        try:
            qty = int(float(qty_clean)) if qty_clean else None
        except ValueError:
            qty = None
        sec = r["section_ref"]
        sec_num = sec_order.get(sec, 0)
        cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                       quantity, catalog_ref, diagram_page, section_ref, section_name)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (MID, r["part_number"], r["part_name"], qty,
                     int(r["catalog_ref"]), int(r["diagram_page"]),
                     sec_num, SECTIONS[sec][0]))
    
    for sec in sec_order_list:
        name, loc, page = SECTIONS[sec]
        sec_num = sec_order[sec]
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
