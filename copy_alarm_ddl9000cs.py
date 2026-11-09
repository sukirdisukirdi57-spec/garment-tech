#!/usr/bin/env python3
"""Copy kode E* dari troubleshooting -> machine_alarms untuk DDL-9000C-S (id=17)."""
import sqlite3, shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID = 17
MANUAL_TITLE = "JUKI DDL-9000C-S Instruction Manual"
MANUAL_CHAPTER = "4-6. List of errors"
MANUAL_PAGE = 52

# Backup
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-alarms-ddl9000cs-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Ambil dari troubleshooting
cur.execute("""SELECT code, problem, possible_cause, solution
               FROM troubleshooting
               WHERE machine_id=? AND code LIKE 'E%' AND code IS NOT NULL
               ORDER BY code""", (MID,))
rows = cur.fetchall()
print(f"[SUMBER] {len(rows)} kode alarm dari troubleshooting")

# Insert (UNIQUE machine_id+alarm_code akan tolak duplikat)
inserted = 0
skipped = 0
for code, problem, cause, solution in rows:
    try:
        cur.execute("""INSERT INTO machine_alarms(machine_id, alarm_code, alarm_name,
                       possible_cause, solution, manual_title, manual_chapter, manual_page)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (MID, code, problem, cause, solution,
                     MANUAL_TITLE, MANUAL_CHAPTER, MANUAL_PAGE))
        inserted += 1
    except sqlite3.IntegrityError:
        skipped += 1

conn.commit()

cur.execute("SELECT COUNT(*) FROM machine_alarms WHERE machine_id=?", (MID,))
total = cur.fetchone()[0]
print(f"[HASIL] inserted={inserted}, skipped(duplikat)={skipped}, total di DB={total}")

conn.close()
