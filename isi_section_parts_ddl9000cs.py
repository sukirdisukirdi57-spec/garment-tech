#!/usr/bin/env python3
"""Isi section_ref & section_name di parts DDL-9000C-S berdasarkan line range di txt."""
import re, sqlite3, shutil
from pathlib import Path
from datetime import datetime

SRC = Path("downloads/JUKI_DDL9000CS_partslist.txt")
DB  = Path("database/garment.db")
MID = 17

# Section boundary dari hasil grep sebelumnya (baris awal tiap section di body)
SECTIONS = [
    (117,  "1. MACHINE FRAME & MISCELLANEOUS COVER COMPONENTS", 1, 1),
    (277,  "2. BOBBIN WINDER COMPONENTS", 2, 3),
    (366,  "3. MAIN SHAFT & NEEDLE BAR COMPONENTS", 3, 5),
    (490,  "4. HAND LIFTER & TENSION RELEASE COMPONENTS", 4, 7),
    (620,  "5. FEED ADJUST MECHANISM COMPONENTS", 5, 9),
    (764,  "6. VERTICAL FEED COMPONENTS", 6, 11),
    (893,  "7. HOOK DRIVING COMPONENTS", 7, 13),
    (989,  "8. THREAD TRIMMER COMPONENTS", 8, 15),
    (1170, "9. OIL LUBRICATION COMPONENTS", 9, 17),
    (1312, "10. AUTOMATIC REVERSE FEED COMPONENTS", 10, 19),
    (1369, "11. OPERATION PANEL COMPONENTS", 11, 20),
    (1429, "12. THREAD STAND COMPONENTS", 12, 21),
    (1495, "13. UNDER COVER COMPONENTS", 13, 22),
    (1571, "14. ACCESSORIE PART COMPONENTS", 14, 23),
    (1713, "16. TABLE & STAND COMPONENTS", 16, 25),
]

def line_to_section(ln):
    for start, name, ref, page in SECTIONS:
        if ln >= start:
            current = (name, ref, page)
        else:
            break
    return current if 'current' in dir() else None

# Pattern sama seperti parser sebelumnya
PN_PATTERN = re.compile(r"^(?:[A-Z]{2}-\d{6,7}(?:-[A-Z0-9]{2,3})?|\d{3}-\d{5})$")
LINE_PATTERN = re.compile(
    r"^\s*(\d+)\s+(?:#\d+\s+)?([A-Z0-9][A-Z0-9\-]+)\s+(.+?)\s+(\d+(?:\.\d+)?)\s*$"
)

# Parse ulang CSV dengan line & section
updates = []
cur_section = None
with SRC.open(encoding="utf-8", errors="ignore") as f:
    for ln, line in enumerate(f, 1):
        if ln >= 1898: break
        for start, name, ref, page in SECTIONS:
            if ln == start:
                cur_section = (ref, name)
        m = LINE_PATTERN.match(line)
        if not m or not cur_section:
            continue
        ref_, pn, name, qty = m.groups()
        if not PN_PATTERN.match(pn) or not name.strip():
            continue
        updates.append({
            "part_number": pn,
            "catalog_ref": int(ref_),
            "section_ref": cur_section[0],
            "section_name": cur_section[1],
        })

print(f"[PARSE] {len(updates)} baris valid dengan section")

# Backup
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-section-parts-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Update satu per satu (pakai part_number + catalog_ref)
updated = 0
unmatched = 0
for u in updates:
    cur.execute("""UPDATE parts SET section_ref=?, section_name=?
                   WHERE machine_id=? AND part_number=? AND catalog_ref=?
                     AND section_ref IS NULL""",
                (u["section_ref"], u["section_name"], MID,
                 u["part_number"], u["catalog_ref"]))
    if cur.rowcount > 0:
        updated += cur.rowcount
    else:
        unmatched += 1

conn.commit()

# Statistik
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=? AND section_ref IS NOT NULL", (MID,))
total_assigned = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=?", (MID,))
total = cur.fetchone()[0]

print(f"[UPDATE] baris ter-update: {updated}")
print(f"[UNMATCHED] sisa: {unmatched}")
print(f"[HASIL] parts dengan section: {total_assigned}/{total}")

conn.close()
