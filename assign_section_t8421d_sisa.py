#!/usr/bin/env python3
"""Assign section_ref untuk 73 parts T-8421D yang belum punya section."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 84

# Section tambahan untuk parts varian (Q & R dari T-8422D)
EXTRA_SECTIONS = {
    25: ("Q. Tension release mechanism (varian)", "Tension release", 39),
    26: ("R. Thread wiper mechanism (varian)", "Thread wiper", 41),
}

# Keyword untuk deteksi section
KEYWORDS = {
    25: ["TENSION RELEASE", "SOLENOID"],
    26: ["THREAD WIPER", "WIPER"],
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-assign-sisa-t8421d-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Ambil parts yang belum punya section
cur.execute("SELECT id, part_number, part_name FROM parts WHERE machine_id=? AND section_ref IS NULL", (MID,))
rows = cur.fetchall()

assigned = 0
unassigned = 0
for pid, pn, name in rows:
    name_upper = (name or "").upper()
    matched = None
    for ref, kws in KEYWORDS.items():
        if any(kw in name_upper for kw in kws):
            matched = ref
            break
    if matched:
        sec_name, loc, page = EXTRA_SECTIONS[matched]
        cur.execute("""UPDATE parts SET section_ref=?, section_name=?, diagram_page=?
                       WHERE id=?""", (matched, sec_name, page, pid))
        assigned += 1
    else:
        unassigned += 1

conn.commit()
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id=? AND section_ref IS NULL", (MID,))
print(f"[HASIL] assigned={assigned}, unassigned={unassigned}, sisa NULL: {cur.fetchone()[0]}")
conn.close()
