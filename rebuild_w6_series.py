#!/usr/bin/env python3
"""Rebuild W664P (semua section) & W662PC (section utama saja)."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_w6_hasil_parse.csv")
DB  = Path("database/garment.db")

# Section utama (untuk W662PC)
MAIN_SECTIONS = {
    "BED", "COVER1", "COVER2", "CRANK", "ARMSHAFT", "NEEDLEBAR",
    "LOOPER", "FEED1", "FEED2", "FEED3", "PRESSER", "SPREADER",
    "TENSION", "NDLTHREAD", "BOBBIN", "LUBE1", "LUBE2", "HR",
    "INSTALL", "TSTAND",
}

# W664P: semua section (41), W662PC: hanya section utama (20)
MACHINES = [
    (201, "W664P", None),            # None = semua
    (197, "W662PC", MAIN_SECTIONS),  # filter section utama
]

SECTIONS = {
    "BED":      ("MACHINE BED FRAME", "Machine bed frame", 2),
    "COVER1":   ("COVER (1)", "Cover (1)", 4),
    "COVER2":   ("COVER (2)", "Cover (2)", 6),
    "CRANK":    ("CRANKSHAFT DRIVE MECHANISM", "Crankshaft drive", 8),
    "ARMSHAFT": ("ARM SHAFT MECHANISM", "Arm shaft", 10),
    "NEEDLEBAR":("NEEDLE BAR/GUARD MECHANISM", "Needle bar & guard", 12),
    "LOOPER":   ("LOOPER DRIVE MECHANISM", "Looper drive", 14),
    "FEED1":    ("FEED MECHANISM (1)", "Feed (1)", 16),
    "FEED2":    ("FEED MECHANISM (2)", "Feed (2)", 18),
    "FEED3":    ("FEED MECHANISM (3)", "Feed (3)", 20),
    "PRESSER":  ("PRESSER FOOT MECHANISM", "Presser foot", 22),
    "SPREADER": ("SPREADER MECHANISM", "Spreader", 24),
    "TENSION":  ("THREAD TENSION MECHANISM", "Thread tension", 26),
    "NDLTHREAD":("NEEDLE & SPREADER THREAD HANDLING", "Needle & spreader thread", 28),
    "BOBBIN":   ("LOOPER THREAD HANDLING", "Looper thread handling", 30),
    "LUBE1":    ("LUBRICATION MECHANISM (1)", "Lubrication (1)", 32),
    "LUBE2":    ("LUBRICATION MECHANISM (2)", "Lubrication (2)", 34),
    "HR":       ("H.R. DEVICE", "H.R. device", 36),
    "INSTALL":  ("INSTALLATION ACCESSORIES", "Installation accessories", 38),
    "TSTAND":   ("THREAD STAND", "Thread stand", 40),
    "SPEC01":   ("SPECIFIC PARTS W664-01", "Specific parts W664-01", 42),
    "SPEC02":   ("SPECIFIC PARTS W664-02", "Specific parts W664-02", 44),
    "SPEC03":   ("SPECIFIC PARTS W664-03", "Specific parts W664-03", 46),
    "SPEC05":   ("SPECIFIC PARTS W664-05/FT240,240A", "Specific parts W664-05", 48),
    "SPEC08":   ("SPECIFIC PARTS W664-08", "Specific parts W664-08", 50),
    "SPEC30":   ("SPECIFIC PARTS W664-30,32,33,34,35", "Specific parts W664-30 series", 52),
    "SPEC30b":  ("SPECIFIC PARTS W664-30", "Specific parts W664-30", 54),
    "SPEC32":   ("SPECIFIC PARTS W664-32", "Specific parts W664-32", 56),
    "SPEC33":   ("SPECIFIC PARTS W664-33A/B", "Specific parts W664-33", 58),
    "SPEC34":   ("SPECIFIC PARTS W664-34,35", "Specific parts W664-34/35", 60),
    "SPEC71":   ("SPECIFIC PARTS W664-71", "Specific parts W664-71", 62),
    "SPEC81":   ("SPECIFIC PARTS W664-81", "Specific parts W664-81", 64),
    "SPECxxM":  ("SPECIFIC PARTS W664-01M..35N", "Specific parts W664-M variants", 66),
    "FT05":     ("FT DEVICE W664-05,33", "FT device W664-05/33", 68),
    "FT33a":    ("FT DEVICE (1) W664-33", "FT device W664-33 (1)", 70),
    "FT33b":    ("FT DEVICE (2) W664-33", "FT device W664-33 (2)", 72),
    "FT34":     ("FT DEVICE W664-34A,35A,35B", "FT device W664-34/35", 74),
    "CLOTH30":  ("CLOTH TENSION ROLLER (1) W664-30,34A", "Cloth roller W664-30/34A", 76),
    "CLOTH32":  ("CLOTH TENSION ROLLER (2) W664-32", "Cloth roller W664-32", 78),
    "CLOTH33":  ("CLOTH TENSION ROLLER (3) W664-33", "Cloth roller W664-33", 80),
    "RUBBER":   ("RUBBER DEVICE W664-33", "Rubber device W664-33", 82),
    "RP1":      ("RP DEVICE (1)", "RP device (1)", 84),
    "RP2":      ("RP DEVICE (2)", "RP device (2)", 86),
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
    
    rows = [r for r in all_rows if allowed is None or r["section_ref"] in allowed]
    
    # Bangun section list (urutan) berdasarkan section yang dipakai
    used_sections = []
    for r in rows:
        if r["section_ref"] not in used_sections:
            used_sections.append(r["section_ref"])
    # Urutkan sesuai urutan di SECTIONS
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
