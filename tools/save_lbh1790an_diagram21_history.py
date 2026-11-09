import sqlite3
from pathlib import Path
from datetime import datetime
import shutil

DB = Path("database/garment.db")
BACKUP_DIR = Path("database")

revision = """
CATALOG REVISION HISTORY
Source: 21. LIST FOR INFORMATION OF CHANGE
Catalog page: 39
PDF page: 44
Revision No.: 1706-04

OBSOLETED PARTS (D):
Page 03 REF 10: 400-06307
Page 03 REF 18: CQ-2520000-00
Page 03 REF 35: 400-08423
Page 03 REF 36: 401-65704
Page 03 REF 37: 401-65701
Page 03 REF 38: 401-65703
Page 03 REF 39: 400-04206
Page 03 REF 40: SM-6041202-TP
Page 03 REF 43: 229-18304
Page 03 REF 44: 401-42880
Page 03 REF 45: 401-41727
Page 03 REF 46: 401-41730

ADDED PARTS (A):
Page 04 REF 10: 401-44351
Page 04 REF 14: SM-80404A2-TP

Note: Revision history only. Do not globally deactivate
obsolete part numbers or delete existing part records.
""".strip()

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    row = con.execute("""
        SELECT id, notes
        FROM documents
        WHERE id = 119 AND machine_id = 6
    """).fetchone()

    if not row:
        raise RuntimeError("Dokumen Parts List ID 119 tidak ditemukan.")

    old_notes = row["notes"] or ""

    if "21. LIST FOR INFORMATION OF CHANGE" in old_notes:
        print("Dibatalkan: riwayat Diagram 21 sudah tercatat.")
        print(old_notes)
        raise SystemExit(0)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"garment-before-lbh1790an-diagram21-{timestamp}.db"

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()

    print("Backup dibuat:", backup)

    new_notes = old_notes.rstrip() + "\n\n" + revision

    con.execute("BEGIN IMMEDIATE")
    con.execute("""
        UPDATE documents
        SET notes = ?
        WHERE id = 119 AND machine_id = 6
    """, (new_notes,))
    con.commit()

    check = con.execute("""
        SELECT id, title, notes
        FROM documents
        WHERE id = 119
    """).fetchone()

    print("\n=== HASIL UPDATE ===")
    print(dict(check))
    print("\nJumlah baris riwayat:", len(revision.splitlines()))

finally:
    con.close()
