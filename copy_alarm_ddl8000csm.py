#!/usr/bin/env python3
"""Copy kode dari troubleshooting -> machine_alarms untuk DDL-8000CSM (id=225)."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 225
MANUAL_TITLE = "JUKI DDL-8000C Series Instruction Manual"

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-alarms-ddl8000csm-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""SELECT code, problem, possible_cause, solution
               FROM troubleshooting
               WHERE machine_id=? AND code IS NOT NULL
               ORDER BY code""", (MID,))
rows = cur.fetchall()
print(f"[SUMBER] {len(rows)} kode dari troubleshooting")

inserted = 0
skipped = 0
for code, problem, cause, solution in rows:
    try:
        cur.execute("""INSERT INTO machine_alarms(machine_id, alarm_code, alarm_name,
                       possible_cause, solution, manual_title, source_note)
                       VALUES(?,?,?,?,?,?,?)""",
                    (MID, code, problem, cause, solution, MANUAL_TITLE,
                     "Dari troubleshooting DDL-8000CSM; kecocokan varian belum diverifikasi"))
        inserted += 1
    except sqlite3.IntegrityError:
        skipped += 1

conn.commit()
cur.execute("SELECT COUNT(*) FROM machine_alarms WHERE machine_id=?", (MID,))
print(f"[HASIL] inserted={inserted}, skipped={skipped}, total={cur.fetchone()[0]}")
conn.close()
