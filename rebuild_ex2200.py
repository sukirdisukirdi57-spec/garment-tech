#!/usr/bin/env python3
"""Rebuild EX2200 (id=212) dari PDF Pegasus."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_ex2200_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 212
EXPECTED_MODEL = "EX2200"

SECTIONS = {
    "BED":     ("MACHINE BED FRAME", "Machine bed frame", 2),
    "COVER1":  ("COVER (1)", "Cover (1)", 4),
    "COVER2":  ("COVER (2)", "Cover (2)", 6),
    "CRANK":   ("CRANKSHAFT DRIVE MECHANISM", "Crankshaft drive", 8),
    "TENSION": ("THREAD TENSION MECHANISM", "Thread tension", 10),
    "GUIDE":   ("THREAD GUIDE & THREAD TAKEUP", "Thread guide & take-up", 12),
    "NEEDLE1": ("NEEDLE DRIVE MECHANISM (1)", "Needle drive (1)", 14),
    "NEEDLE2": ("NEEDLE DRIVE MECHANISM (2)", "Needle drive (2)", 16),
    "NEEDLE3": ("NEEDLE DRIVE MECHANISM (3)", "Needle drive (3)", 18),
    "LOOPER1": ("DOUBLE CHAINSTITCH LOOPER DRIVE (1)", "Looper drive (1)", 20),
    "LOOPER2": ("DOUBLE CHAINSTITCH LOOPER DRIVE (2)", "Looper drive (2)", 22),
    "LOOPER3": ("DOUBLE CHAINSTITCH LOOPER DRIVE (3)", "Looper drive (3)", 24),
    "FEED1":   ("FEED MECHANISM (1)", "Feed mechanism (1)", 26),
    "FEED2":   ("FEED MECHANISM (2)", "Feed mechanism (2)", 28),
    "KNIFE":   ("KNIFE DRIVE MECHANISM", "Knife drive", 30),
    "PRESSER": ("PRESSER FOOT MECHANISM", "Presser foot", 32),
    "LUBE1":   ("LUBRICATION MECHANISM (1)", "Lubrication (1)", 34),
    "LUBE2":   ("LUBRICATION MECHANISM (2)", "Lubrication (2)", 36),
    "HR":      ("H.R. DEVICE", "H.R. device", 38),
    "TSTAND":  ("THREAD STAND", "Thread stand", 40),
    "SEMI":    ("PARTS FOR SEMI-SUBMERGED INSTALLATION", "Semi-submerged installation", 42),
    "SPEC":    ("SPECIFIC PARTS", "Specific parts", 44),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-ex2200-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
row = cur.fetchone()
if not row or row[0] != EXPECTED_MODEL:
    raise SystemExit(f"BATAL: machine_id={MID} bukan {EXPECTED_MODEL} (dapat: {row})")

cur.execute("""DELETE FROM component_parts WHERE component_id IN
               (SELECT id FROM components WHERE machine_id=?)""", (MID,))
cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
print("[HAPUS] data lama")

with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
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
print(f"[PARTS] {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[KOMPONEN] {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[RELASI] {cur.fetchone()[0]}")
conn.close()
