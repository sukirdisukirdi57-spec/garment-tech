#!/usr/bin/env python3
"""Rebuild W542P & W562P dari PDF Pegasus."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_w522_hasil_parse.csv")
DB  = Path("database/garment.db")

MACHINES = [
    (200, "W542P"),
    (199, "W562P"),
]

SECTIONS = {
    "BED":      ("MACHINE BED FRAME", "Machine bed frame", 2),
    "COVER1":   ("COVER (1)", "Cover (1)", 4),
    "COVER2":   ("COVER (2)", "Cover (2)", 6),
    "CRANK":    ("CRANKSHAFT MECHANISM", "Crankshaft", 8),
    "ARMSHAFT": ("ARM SHAFT MECHANISM", "Arm shaft", 10),
    "NEEDLEBAR":("NEEDLE BAR MECHANISM", "Needle bar", 12),
    "NDLGUARD": ("NEEDLE GUARD MECHANISM", "Needle guard", 14),
    "LOOPER":   ("LOOPER MECHANISM", "Looper", 16),
    "FEED1":    ("FEED MECHANISM (1)", "Feed (1)", 18),
    "FEED2":    ("FEED MECHANISM (2)", "Feed (2)", 20),
    "PRESSER":  ("PRESSER FOOT MECHANISM", "Presser foot", 22),
    "SPREADER": ("SPREADER MECHANISM", "Spreader", 24),
    "TENSION":  ("THREAD TENSION MECHANISM", "Thread tension", 26),
    "NDLTHREAD":("NEEDLE & SPREADER THREAD HANDLING", "Needle & spreader thread", 28),
    "LTHREAD":  ("LOOPER THREAD HANDLING", "Looper thread handling", 30),
    "LUBE1":    ("LUBRICATION MECHANISM (1)", "Lubrication (1)", 32),
    "LUBE2":    ("LUBRICATION MECHANISM (2)", "Lubrication (2)", 34),
    "HR":       ("HR DEVICE, BINDER", "HR device & binder", 36),
    "TSTAND":   ("THREAD STAND", "Thread stand", 38),
    "SEMI":     ("SEMI-SUBMERGED INSTALLATION PARTS", "Semi-submerged installation", 40),
    "SPEC":     ("SPECIFIC PARTS", "Specific parts", 42),
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
        print(f"[BATAL] machine_id={MID} bukan {model} (dapat: {row})")
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
