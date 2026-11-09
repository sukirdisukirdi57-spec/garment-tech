#!/usr/bin/env python3
"""Rebuild WT664P (id=196) dari PDF Pegasus."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_wt664p_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 196
EXPECTED_MODEL = "WT664P"

SECTIONS = {
    "BED":      ("MACHINE BED FRAME & COVER", "Machine bed frame & cover", 2),
    "MAIN":     ("ARM SHAFT & NEEDLE BAR & LOOPER DRIVE & FEED", "Arm shaft & needle bar & looper drive & feed", 4),
    "TOPFEED1": ("TOP FEED MECHANISM (1)", "Top feed (1)", 6),
    "TOPFEED2": ("TOP FEED MECHANISM (2)", "Top feed (2)", 8),
    "TOPFEED3": ("TOP FEED MECHANISM (3)", "Top feed (3)", 10),
    "PRESSER":  ("PRESSER FOOT MECHANISM", "Presser foot", 12),
    "SPREADER": ("SPREADER & NEEDLE/SPREADER THREAD", "Spreader & thread handling", 14),
    "LUBE":     ("LUBRICATION MECHANISM", "Lubrication", 16),
    "SPEC1":    ("SPECIFIC PARTS (1) WT664-01G,01N", "Specific parts WT664-01", 18),
    "SPEC2":    ("SPECIFIC PARTS (2) WT664-01N,08N,35M,35N", "Specific parts WT664-01N/08N/35", 20),
    "SPEC3":    ("SPECIFIC PARTS (3) WT664-03F", "Specific parts WT664-03F", 22),
    "SPEC4":    ("SPECIFIC PARTS (4) WT664-08A,B,D,H,N", "Specific parts WT664-08", 24),
    "SPEC5":    ("SPECIFIC PARTS (5) WT664-35A,B,G,M,N", "Specific parts WT664-35A/B/G/M/N", 26),
    "SPEC6":    ("SPECIFIC PARTS (6) WT664-35B,G,N", "Specific parts WT664-35B/G/N", 28),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-wt664p-{ts}")
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
