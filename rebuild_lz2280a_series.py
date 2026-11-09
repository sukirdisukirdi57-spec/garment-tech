#!/usr/bin/env python3
"""Rebuild LZ-2280A, LZ-2284A, LZ-2287A dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_lz2280a_hasil_parse.csv")
DB  = Path("database/garment.db")

MACHINES = [
    (10, "LZ-2280A"),
    (33, "LZ-2284A"),
    (34, "LZ-2287A"),
]

SECTIONS = {
    1:  ("1. FRAME & MISC COVER (1)", "Frame & cover (1)", 1),
    2:  ("2. FRAME & MISC COVER (2)", "Frame & cover (2)", 3),
    3:  ("3. MAIN SHAFT & NEEDLE BAR", "Main shaft & needle bar", 5),
    4:  ("4. NEEDLE VIBRATOR (1)", "Needle vibrator (1)", 7),
    5:  ("5. NEEDLE VIBRATOR (2)", "Needle vibrator (2)", 8),
    6:  ("6. PRESSER BAR & FEED REGULATOR", "Presser bar & feed regulator", 9),
    7:  ("7. FEED MECHANISM", "Feed mechanism", 11),
    8:  ("8. FEED MECHANISM & CONDENSE", "Feed mechanism & condense", 13),
    9:  ("9. HOOK DRIVING SHAFT & HOOK", "Hook driving shaft & hook", 14),
    10: ("10. LUBRICATION", "Lubrication", 15),
    11: ("11. THREAD TRIMMER MECHANISM", "Thread trimmer", 17),
    12: ("12. UPPER THREAD FEEDER", "Upper thread feeder", 19),
    13: ("13. AUTOMATIC REVERSE FEED", "Automatic reverse feed", 20),
    14: ("14. WIPER MECHANISM", "Wiper", 21),
    15: ("15. COVER COMPONENTS", "Cover", 22),
    16: ("16. OIL RESERVOIR & KNEE LIFTER", "Oil reservoir & knee lifter", 23),
    17: ("17. THREAD STAND", "Thread stand", 24),
    18: ("18. EXCLUSIVE PARTS LZ-2284A/2287A", "Exclusive parts", 25),
    19: ("19. SPECIAL ORDER PARTS (1)", "Special order (1)", 26),
    20: ("20. SPECIAL ORDER PARTS (2)", "Special order (2)", 27),
}

with CSV.open(encoding="utf-8") as f:
    all_rows = list(csv.DictReader(f))

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for MID, model in MACHINES:
    print(f"\n=== {model} (id={MID}) ===")
    
    # Backup per mesin
    bak = DB.with_name(f"{DB.name}.backup-rebuild-{model.lower()}-{ts}")
    shutil.copy2(DB, bak)
    print(f"[BACKUP] {bak.name}")
    
    cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
    row = cur.fetchone()
    if not row or row[0] != model:
        print(f"[BATAL] machine_id={MID} bukan {model}")
        continue
    
    # Hapus data lama
    cur.execute("""DELETE FROM component_parts WHERE component_id IN
                   (SELECT id FROM components WHERE machine_id=?)""", (MID,))
    cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
    cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
    
    # Filter: untuk LZ-2280A skip section 18 (khusus 2284A/2287A)
    rows = all_rows
    if model == "LZ-2280A":
        rows = [r for r in all_rows if int(r["section_ref"]) != 18]
    
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
    
    # Komponen
    used_sections = set(int(r["section_ref"]) for r in rows)
    for ref in sorted(used_sections):
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
    
    # Relasi
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
