import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
SECTION = "AMS-210EN catalog staging; section 23"

# REF, NOTE, PART NO, DESCRIPTION, QTY RAW
data = [
    (1, "#01", "400-33831", "PK78 PEDAL SWITCH ASM.", "1"),
    (2, "#02", "GPK-470010AB", "3-PEDAL ASM.", "1"),
    (3, "#02", "400-33875", "PK47 RELAY CABLE ASM.", "1"),
]

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

if [r[0] for r in data] != [1, 2, 3]:
    raise SystemExit("REF tidak valid. Dibatalkan.")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
backup = BACKUP_DIR / (
    "garment-before-fix-pedal-section23-"
    + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)
shutil.copy2(DB, backup)
print("BACKUP:", backup)

con = sqlite3.connect(DB)
try:
    con.execute("BEGIN IMMEDIATE")

    count = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id = 44 AND notes = ?
    """, (SECTION,)).fetchone()[0]

    if count:
        raise RuntimeError(
            f"Section 23 sudah berisi {count} baris. Transaksi dibatalkan."
        )

    for ref, note, part_no, name, qty_raw in data:
        con.execute("""
            INSERT INTO parts (
                machine_id, part_number, part_name, quantity,
                catalog_ref, note, notes, quantity_raw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            44, part_no, name, int(qty_raw),
            ref, note, SECTION, qty_raw
        ))

    con.commit()
except Exception:
    con.rollback()
    raise
finally:
    con.close()

con = sqlite3.connect(DB)
rows = con.execute("""
    SELECT catalog_ref, part_number, part_name,
           quantity, quantity_raw, note
    FROM parts
    WHERE machine_id = 44 AND notes = ?
    ORDER BY catalog_ref
""", (SECTION,)).fetchall()

refs = [r[0] for r in rows]

print("\n=== AUDIT SECTION 23 ===")
print("Jumlah baris:", len(rows))
print("REF lengkap 1–3:", refs == [1, 2, 3])
print("REF duplikat:", len(refs) - len(set(refs)))

for row in rows:
    print(row)

con.close()
