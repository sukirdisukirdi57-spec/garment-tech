#!/usr/bin/env python3
"""Batch copy kode dari troubleshooting -> machine_alarms."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")

# Mesin yang perlu copy (MID, model, manual_title)
MACHINES = [
    (11, "PS-800", "JUKI PS-800 Instruction Manual"),
    (40, "MEB-3200C", "JUKI MEB-3200C Instruction Manual"),
    (227, "BAS-311HN-03S", "Brother BAS-311HN Instruction Manual"),
    (6, "LBH-1790AN", "JUKI LBH-1790AN Instruction Manual"),
    (38, "LBH-1790S", "JUKI LBH-1790S Instruction Manual"),
]

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-copy-alarm-batch-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

grand_total = 0
for MID, model, manual_title in MACHINES:
    print(f"=== {model} (id={MID}) ===")
    cur.execute("""SELECT code, problem, possible_cause, solution
                   FROM troubleshooting
                   WHERE machine_id=? AND code IS NOT NULL AND code != ''
                   ORDER BY code""", (MID,))
    rows = cur.fetchall()
    
    inserted = 0
    skipped = 0
    for code, problem, cause, solution in rows:
        try:
            cur.execute("""INSERT INTO machine_alarms(machine_id, alarm_code, alarm_name,
                           possible_cause, solution, manual_title, source_note)
                           VALUES(?,?,?,?,?,?,?)""",
                        (MID, code, problem, cause, solution, manual_title,
                         "Dari troubleshooting; kecocokan varian belum diverifikasi"))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM machine_alarms WHERE machine_id=?", (MID,))
    total = cur.fetchone()[0]
    print(f"  sumber: {len(rows)}, inserted: {inserted}, skipped: {skipped}, total alarm: {total}\n")
    grand_total += inserted

conn.close()
print(f"[SELESAI] total inserted: {grand_total}")
