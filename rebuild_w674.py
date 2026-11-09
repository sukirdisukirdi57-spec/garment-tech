#!/usr/bin/env python3
"""Rebuild W674 (id=206) dari PDF Pegasus."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_w674_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 206
EXPECTED_MODEL = "W674"

SECTIONS = {
    "BED":       ("MACHINE BED FRAME", "Machine bed frame", 2),
    "COVER1":    ("COVER (1)", "Cover (1)", 4),
    "COVER2":    ("COVER (2)", "Cover (2)", 6),
    "COVER3":    ("COVER (3) [W674-40]", "Cover (3) [W674-40]", 8),
    "COVER4":    ("COVER (4) [W674-40]", "Cover (4) [W674-40]", 10),
    "COVER5":    ("COVER (5) [W674-42]", "Cover (5) [W674-42]", 12),
    "COVER6":    ("COVER (6) [W674-45]", "Cover (6) [W674-45]", 14),
    "COVER7":    ("COVER (7) [W674-45]", "Cover (7) [W674-45]", 16),
    "LOWSHAFT":  ("LOWER SHAFT MECHANISM", "Lower shaft", 18),
    "UPSHAFT":   ("UPPER SHAFT MECHANISM", "Upper shaft", 20),
    "NEEDLEBAR": ("NEEDLE BAR MECHANISM", "Needle bar", 22),
    "NEEDLERECV":("NEEDLE RECEIVER MECHANISM", "Needle receiver", 24),
    "LOOPER":    ("LOOPER MECHANISM", "Looper", 26),
    "FEED1":     ("FEED MECHANISM (1)", "Feed (1)", 28),
    "FEED2":     ("FEED MECHANISM (2)", "Feed (2)", 30),
    "PRESSER":   ("PRESSER FOOT MECHANISM", "Presser foot", 32),
    "TENSION1":  ("THREAD TENSION MECHANISM (1)", "Thread tension (1)", 34),
    "TENSION2":  ("THREAD TENSION MECHANISM (2)", "Thread tension (2)", 36),
    "NDLTHREAD": ("NEEDLE THREAD MECHANISM", "Needle thread", 38),
    "BOBBIN":    ("BOBBIN WINDER MECHANISM", "Bobbin winder", 40),
    "LUBE1":     ("LUBRICATION MECHANISM (1)", "Lubrication (1)", 42),
    "LUBE2":     ("LUBRICATION MECHANISM (2)", "Lubrication (2)", 44),
    "FT":        ("FT MECHANISM", "FT mechanism", 46),
    "RP1":       ("RP DEVICE (1)", "RP device (1)", 48),
    "RP2":       ("RP DEVICE (2)", "RP device (2)", 50),
    "CLOTH1":    ("CLOTH TENSION ROLLER (1)", "Cloth tension roller (1)", 52),
    "CLOTH2":    ("CLOTH TENSION ROLLER (2)", "Cloth tension roller (2)", 54),
    "CLOTH3":    ("CLOTH TENSION ROLLER (3)", "Cloth tension roller (3)", 56),
    "HG1":       ("HG DEVICE (1) [W674-40]", "HG device (1)", 58),
    "HG2":       ("HG DEVICE (2) [W674-40]", "HG device (2)", 60),
    "HG3":       ("HG DEVICE (3) [W674-45]", "HG device (3)", 62),
    "HG4":       ("HG DEVICE (4) [W674-45]", "HG device (4)", 64),
    "INSTALL":   ("INSTALLATION ACCESSORIES", "Installation accessories", 66),
    "TSTAND":    ("THREAD STAND", "Thread stand", 68),
}

SECTION_ORDER = {k: i+1 for i, k in enumerate(SECTIONS.keys())}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-w674-{ts}")
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
