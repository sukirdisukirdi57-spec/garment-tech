#!/usr/bin/env python3
"""Rebuild MAICA UAM-02 (id=63) dari CSV v8."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("data/maica/UAM02-parts-v8.csv")
DB  = Path("database/garment.db")
MID = 63

# Page -> (section_name, diagram_page)
# Nama section berbasis konten (karena PDF rusak, tidak ada nama asli)
PAGE_TO_SECTION = {
    4:  ("Page 4 — Telaio & Aspirazione (LAMIERA ASPIRAZIONE)", 4),
    5:  ("Page 5 — Telaio (lanjutan: RAC.90° GIR 1-8 D.8)", 5),
    6:  ("Page 6 — Elettronica (SOLENOIDE DIFFERENZIALE)", 6),
    8:  ("Page 8 — Supporto Dima Etichetta", 8),
    10: ("Page 10 — Protezione (LAMIERA PROTEZIONE)", 10),
    12: ("Page 12 — Crochet (ALBERO CROCHET)", 12),
    14: ("Page 14 — Asse X-Y (PIATTO BLOCCA CINGHIA AT5)", 14),
    16: ("Page 16 — Elettronica / Lampada LED", 16),
    18: ("Page 18 — Molla Aspirafilo", 18),
    20: ("Page 20 — Carter Posteriore", 20),
    22: ("Page 22 — Pedale / Elettrico", 22),
    24: ("Page 24 — Quadro Elettrico", 24),
    25: ("Page 25 — Pulsantiera (PIASTRA TASTI)", 25),
    27: ("Page 27 — Dima Posizionamento Etichetta", 27),
    28: ("Page 28 — Dima Cucitura 4 Lati", 28),
}

SECTION_ORDER = {page: i+1 for i, page in enumerate(sorted(PAGE_TO_SECTION.keys()))}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-rebuild-uam02-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT model FROM machines WHERE id=?", (MID,))
row = cur.fetchone()
if not row or row[0] != "UAM-02":
    raise SystemExit(f"BATAL: machine_id={MID} bukan UAM-02 (dapat: {row})")

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
for page in sorted(PAGE_TO_SECTION.keys()):
    sec_name, diagram_page = PAGE_TO_SECTION[page]
    sec_num = SECTION_ORDER[page]
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
