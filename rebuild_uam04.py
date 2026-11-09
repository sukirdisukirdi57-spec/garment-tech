#!/usr/bin/env python3
"""Rebuild MAICA UAM-04 (id=65) dari CSV v3."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("data/maica/UAM04-parts-v3.csv")
DB  = Path("database/garment.db")
MID = 65
EXPECTED_MODEL = "UAM-04"

# Map halaman -> (sub-assembly name, location, diagram_page)
PAGE_TO_SECTION = {
    4:  ("ASSIEME TELAJO E ASPIRAZIONE", "Frame & aspirasi", 4),
    5:  ("ASSIEME IMPLATORE (1)", "Implatore (1)", 5),
    7:  ("ASSIEME IMPLATORE (2)", "Implatore (2)", 7),
    9:  ("ASSIEME SCARICATORE", "Scaricatore", 9),
    11: ("ASSIEME BLOCCA FESSINO", "Blocca fessino", 11),
    13: ("ASSIEME PIEGA FESSINO", "Piega fessino", 13),
    15: ("ASSIEME CROCHET UAM04-02-01", "Crochet", 15),
    18: ("ASSIEME TRAVERSA ASSE X E PINZA", "Traversa asse X & pinza", 18),
    20: ("ASSIEME TESTA A CUCIRE", "Testa a cucire", 20),
    22: ("ASSIEME CARTER", "Carter", 22),
    23: ("ASSIEME PARTI ELETTRICHE / ELETTRONICHE", "Parti elettriche", 23),
    24: ("ASSIEME DIMA PIEGA FESSINO", "Dima piega fessino", 24),
    25: ("ASSIEME BLOCCA FESSINO (blade)", "Blocca fessino (blade)", 25),
    26: ("ASSIEME PARTI PER DIME PINZA", "Parti per dime pinza", 26),
    28: ("ASSIEME QUADRO ELETTRICO", "Quadro elettrico", 28),
    30: ("ASSIEME PULSANTIERA UAM04", "Pulsantiera", 30),
    31: ("ASSIEME MORSETTIERA", "Morsettiera", 31),
    35: ("ASSIEME RICAMBIO DIME BLOCCA FESSINO", "Ricambio dime blocca", 35),
    37: ("ASSIEME RICAMBIO DIMA PIEGA FESSINO", "Ricambio dima piega", 37),
    38: ("ASSIEME DIME FESSINO", "Dime fessino", 38),
}

# Urutkan page sesuai urutan sub-assembly
PAGE_ORDER = sorted(PAGE_TO_SECTION.keys())

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-uam04-{ts}")
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

# Section order = index page dalam PAGE_ORDER
sec_order = {page: i+1 for i, page in enumerate(PAGE_ORDER)}

for r in rows:
    page = int(r["page"])
    if page not in PAGE_TO_SECTION: 
        continue
    qty_str = r["quantity"].strip()
    try:
        qty = int(float(qty_str)) if qty_str else None
    except ValueError:
        qty = None
    sec_num = sec_order.get(page, 0)
    sec_name = PAGE_TO_SECTION[page][0]
    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page, section_ref, section_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (MID, r["part_no"], r["description"], qty,
                 int(r["item"]) if r["item"] else None,
                 page, sec_num, sec_name))

# Buat komponen per section
for page in PAGE_ORDER:
    name, loc, dpage = PAGE_TO_SECTION[page]
    sec_num = sec_order[page]
    cur.execute("""SELECT part_number FROM parts
                   WHERE machine_id=? AND section_ref=?
                   ORDER BY catalog_ref LIMIT 1""", (MID, sec_num))
    r = cur.fetchone()
    main_pn = r[0] if r else None
    cur.execute("""INSERT INTO components(machine_id, component_name, part_number,
                   location, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, name, main_pn, loc, str(sec_num), dpage))

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
print(f"[PARTS] {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM components WHERE machine_id=?", (MID,))
print(f"[KOMPONEN] {cur.fetchone()[0]}")
cur.execute("""SELECT COUNT(*) FROM component_parts cp
               JOIN components c ON c.id=cp.component_id WHERE c.machine_id=?""", (MID,))
print(f"[RELASI] {cur.fetchone()[0]}")
conn.close()
