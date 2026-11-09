#!/usr/bin/env python3
"""Rebuild LH-3568A, LH-3578A, LH-3588A dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_lh3500a_hasil_parse.csv")
DB  = Path("database/garment.db")

# Filter section per model
MODELS = {
    19: ("LH-3568A", {1,2,4,7,8,10,11,12,13,14,15,16,18,19,20,21,22}),
    20: ("LH-3578A", {1,2,3,5,8,9,10,11,12,13,14,15,17,18,19,20,21,22}),
    21: ("LH-3588A", {1,2,4,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22}),
}

SECTIONS = {
    1:  ("1. FRAME & MISC COVER", "Frame & cover", 1),
    2:  ("2. MAIN SHAFT & THREAD TAKE-UP", "Main shaft & thread take-up", 3),
    3:  ("3. NEEDLE BAR (1)", "Needle bar (1)", 5),
    4:  ("4. NEEDLE BAR (2)", "Needle bar (2)", 7),
    5:  ("5. TENSION POST (1)", "Tension post (1)", 9),
    6:  ("6. TENSION POST (2)", "Tension post (2)", 11),
    7:  ("7. TENSION POST (3)", "Tension post (3)", 13),
    8:  ("8. HOOK & HOOK DRIVING (1)", "Hook & hook driving (1)", 15),
    9:  ("9. HOOK & HOOK DRIVING (2)", "Hook & hook driving (2)", 17),
    10: ("10. HOOK & HOOK DRIVING (3)", "Hook & hook driving (3)", 19),
    11: ("11. FEED MECHANISM", "Feed mechanism", 21),
    12: ("12. PRESSER BAR & TENSION RELEASE", "Presser bar & tension release", 23),
    13: ("13. THREAD TRIMMER", "Thread trimmer", 25),
    14: ("14. AUTOMATIC REVERSE FEED", "Automatic reverse feed", 27),
    15: ("15. WIPER MECHANISM", "Wiper mechanism", 29),
    16: ("16. LUBRICATION (LH-3528A/3568A)", "Lubrication (3528A/3568A)", 31),
    17: ("17. LUBRICATION (LH-3578A/3588A)", "Lubrication (3578A/3588A)", 33),
    18: ("18. BELT COVER & BOBBIN WINDER", "Belt cover & bobbin winder", 35),
    19: ("19. BOTTOM COVER", "Bottom cover", 37),
    20: ("20. AK DEVICE", "AK device", 38),
    21: ("21. THREAD STAND", "Thread stand", 39),
    22: ("22. ACCESSORIE PARTS", "Accessories", 41),
}

with CSV.open(encoding="utf-8") as f:
    all_rows = list(csv.DictReader(f))

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for MID, (model, allowed_sections) in MODELS.items():
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
    
    rows = [r for r in all_rows if int(r["section_ref"]) in allowed_sections]
    
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
