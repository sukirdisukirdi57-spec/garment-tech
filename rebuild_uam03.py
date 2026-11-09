#!/usr/bin/env python3
"""Rebuild MAICA UAM-03 (id=64) dari CSV."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("data/maica/UAM03-parts-generated.csv")
DB  = Path("database/garment.db")
MID = 64

# Map page CSV -> (section_name, diagram_pdf_page)
PAGE_TO_SECTION = {
    4:  ("ASSIEME TELAO MACCHINA", 3),
    5:  ("ASSIEME TELAO MACCHINA (cont)", 3),
    7:  ("ASSIEME IMPILATORE", 6),
    8:  ("ASSIEME SCARICATORE", 9),
    10: ("ASSIEME FERMA TESSUTO", 9),
    12: ("ASSIEME ASSE X-Y TAGLIO", 11),
    14: ("ASSIEME CROCHET", 13),
    16: ("ASSIEME ASSE X-Y CUCITO", 15),
    18: ("ASSIEME TESTA A CUCIRE UAM03", 17),
    20: ("ASSIEME TRAVE ASSE X-Y TESTA CUCIRE", 19),
    22: ("ASSIEME PARTI ELETTRICHE", 21),
    24: ("ASSIEME LASER", 23),
    26: ("ASSIEME TAGLIERINA CON BRONZINA", 25),
    28: ("ASSIEME CARTER MACCHINA", 27),
    30: ("ASSIEME QUADRO ELETTRICO", 29),
    32: ("ASSIEME DIME RICAMBIO CUCITO POLSO", 31),
    33: ("ASSIEME DIME RICAMBIO TAGLIO POLSO", 32),
    34: ("ASSIEME DIME RICAMBIO CUCITURA COLLO", 33),
    35: ("ASSIEME DIME RICAMBIO TAGLIO COLLO", 34),
}

# Section order (untuk component ref)
SECTION_ORDER = {
    4: 1, 5: 1,  # gabung TELAO = section 1
    7: 2,
    8: 3,
    10: 4,
    12: 5,
    14: 6,
    16: 7,
    18: 8,
    20: 9,
    22: 10,
    24: 11,
    26: 12,
    28: 13,
    30: 14,
    32: 15,
    33: 16,
    34: 17,
    35: 18,
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-uam03-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
row = cur.fetchone()
if not row or row[0] != "UAM-03":
    raise SystemExit(f"BATAL: machine_id={MID} bukan UAM-03 (dapat: {row})")

cur.execute("""DELETE FROM component_parts WHERE component_id IN
               (SELECT id FROM components WHERE machine_id=?)""", (MID,))
cur.execute("DELETE FROM parts WHERE machine_id=?", (MID,))
cur.execute("DELETE FROM components WHERE machine_id=?", (MID,))
print("[HAPUS] data lama")

with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

inserted = 0
for r in rows:
    try:
        page = int(r["page"])
    except:
        continue
    if page not in PAGE_TO_SECTION:
        continue
    sec_name, diagram_page = PAGE_TO_SECTION[page]
    sec_num = SECTION_ORDER[page]
    try:
        qty = int(r["quantity"]) if r["quantity"] else None
    except:
        qty = None
    try:
        catalog_ref = int(r["item"]) if r["item"] else None
    except:
        catalog_ref = None
    
    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page, section_ref, section_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (MID, r["part_no"], r["description"], qty,
                 catalog_ref, diagram_page, sec_num, sec_name))
    inserted += 1

print(f"[PARTS] {inserted} inserted")

# Buat komponen per section
cur.execute("SELECT DISTINCT section_ref, section_name FROM parts WHERE machine_id=? ORDER BY section_ref", (MID,))
sections = cur.fetchall()

for sec_num, sec_name in sections:
    # Ambil diagram page dari mapping
    diagram_page = None
    for page, (sn, dp) in PAGE_TO_SECTION.items():
        if SECTION_ORDER[page] == sec_num:
            diagram_page = dp
            break
    
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY catalog_ref LIMIT 1""", (MID, sec_num))
    r = cur.fetchone()
    main_pn = r[0] if r else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, sec_name, main_pn, sec_name, str(sec_num), diagram_page))

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
print(f"[TOTAL] parts: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[TOTAL] komponen: {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[TOTAL] relasi: {cur.fetchone()[0]}")
conn.close()
