#!/usr/bin/env python3
"""Rebuild FS703P (id=194) dari PDF Pegasus."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_fs703p_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 194
EXPECTED_MODEL = "FS703P"

SECTIONS = {
    "BED":       ("MACHINE BED FRAME", "Machine bed frame", 2),
    "COVER":     ("COVER", "Cover", 4),
    "CRANK":     ("CRANKSHAFT MECHANISM", "Crankshaft", 6),
    "NEEDLEDRV": ("NEEDLE DRIVE & SPREADER THREAD HANDLING", "Needle drive & spreader thread", 8),
    "SPREADER":  ("SPREADER & KNIFE DRIVE MECHANISM", "Spreader & knife drive", 10),
    "LOOPER":    ("LOOPER DRIVE MECHANISM", "Looper drive", 12),
    "LTHREAD":   ("LOOPER THREAD HANDLING", "Looper thread handling", 14),
    "FEED1":     ("FEED MECHANISM (1)", "Feed (1)", 16),
    "FEED2":     ("FEED MECHANISM (2)", "Feed (2)", 18),
    "PRESSER1":  ("PRESSER FOOT MECHANISM (1)", "Presser foot (1)", 20),
    "PRESSER2":  ("PRESSER FOOT MECHANISM (2)", "Presser foot (2)", 22),
    "PRESSER3":  ("PRESSER FOOT MECHANISM (3)", "Presser foot (3)", 24),
    "TENSION":   ("THREAD TENSION MECHANISM", "Thread tension", 26),
    "LUBE":      ("LUBRICATION MECHANISM", "Lubrication", 28),
    "PEDESTAL1": ("PEDESTAL (PD1,PD2) (1)", "Pedestal (1)", 30),
    "PEDESTAL2": ("PEDESTAL (PD1,PD2) (2)", "Pedestal (2)", 32),
    "TABLE":     ("TABLE TOP INSTALLATION (PD3)", "Table top installation", 34),
    "TSTAND":    ("THREAD STAND", "Thread stand", 36),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-fs703p-{ts}")
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
