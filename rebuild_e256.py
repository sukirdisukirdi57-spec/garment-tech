#!/usr/bin/env python3
"""Rebuild E256 (id=213) dari PDF Pegasus."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_e256_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 213
EXPECTED_MODEL = "E256"

SECTIONS = {
    "BED":      ("MACHINE BED FRAME", "Machine bed frame", 2),
    "COVER1":   ("COVER (1)", "Cover (1)", 4),
    "COVER2":   ("COVER (2)", "Cover (2)", 6),
    "CRANK":    ("CRANKSHAFT DRIVE MECHANISM", "Crankshaft drive", 8),
    "NEEDLE":   ("NEEDLE DRIVE MECHANISM", "Needle drive", 10),
    "UPLOOPER": ("UPPER LOOPER DRIVE MECHANISM", "Upper looper drive", 12),
    "LOWLOOPER":("LOWER LOOPER DRIVE MECHANISM", "Lower looper drive", 14),
    "FEED1":    ("FEED MECHANISM (1)", "Feed mechanism (1)", 16),
    "FEED2":    ("FEED MECHANISM (2)", "Feed mechanism (2)", 18),
    "KNIFE":    ("KNIFE DRIVE MECHANISM", "Knife drive", 20),
    "PRESSER":  ("PRESSER FOOT MECHANISM", "Presser foot", 22),
    "LUBE":     ("LUBRICATING MECHANISM", "Lubricating mechanism", 24),
    "HR":       ("H.R. DEVICE", "H.R. device", 26),
    "TSTAND":   ("THREAD STAND", "Thread stand", 28),
    "INSTALL1": ("INSTALLATION ACCESSORIES (1)", "Installation accessories (1)", 30),
    "INSTALL2": ("INSTALLATION ACCESSORIES (2)", "Installation accessories (2)", 32),
    "SPEC1":    ("SPECIFIC PARTS (1)", "Specific parts (1)", 34),
    "SPEC2":    ("SPECIFIC PARTS (2)", "Specific parts (2)", 36),
    "SPEC3":    ("SPECIFIC PARTS (3)", "Specific parts (3)", 38),
    "SPEC4":    ("SPECIFIC PARTS (4)", "Specific parts (4)", 40),
    "SPEC5":    ("SPECIFIC PARTS (5)", "Specific parts (5)", 42),
    "SPEC6":    ("SPECIFIC PARTS (6)", "Specific parts (6)", 44),
    "SPEC7":    ("SPECIFIC PARTS (7)", "Specific parts (7)", 46),
    "SPEC8":    ("SPECIFIC PARTS (8)", "Specific parts (8)", 48),
    "SPEC9":    ("SPECIFIC PARTS (9)", "Specific parts (9)", 50),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-e256-{ts}")
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
