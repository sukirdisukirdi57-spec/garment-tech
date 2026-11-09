import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
MACHINE_ID = 44
SECTION = "AMS-210EN catalog staging; section 19"

# REF, PART NO, DESCRIPTION, quantity, quantity_raw
parts = [
    (1,  "229-30358",      "THREAD STAND ASM.",              1, "1"),
    (2,  "229-31109",      "SPOOL RETAINER",                 2, "(2)"),
    (3,  "229-31000",      "SPOOL PIN",                      2, "(2)"),
    (4,  "229-30903",      "SPOOL REST CUSHION",             2, "(2)"),
    (5,  "229-30804",      "SPOOL REST",                     2, "(2)"),
    (6,  "SM-6061610-SC",  "SCREW M6 L=16",                  2, "(2)"),
    (7,  "229-30705",      "THREAD GUIDE ARM JOINT",         2, "(2)"),
    (8,  "229-31406",      "SPOOL REST ROD RUBBER CAP",      1, "(1)"),
    (9,  "229-30507",      "SPOOL REST ARM",                 1, "(1)"),
    (10, "229-30408",      "SPOOL REST ROD UPPER",           1, "(1)"),
    (11, "229-31307",      "SPOOL REST ROD JOINT",           1, "(1)"),
    (12, "SM-4051405-SE",  "SCREW M5 L=14",                  2, "(2)"),
    (13, "NM-6050001-SE",  "NUT M5",                        2, "(2)"),
    (14, "229-30309",      "SPOOL REST ROD LOWER",           1, "(1)"),
    (15, "229-30556",      "THREAD STANDING ARM ASM.",       1, "(1)"),
    (16, "WS-0510002-KN",  "SPRING WASHER",                  2, "(2)"),
    (17, "NM-6050001-SE",  "NUT M5",                        2, "(2)"),
    (18, "NM-6160511-SE",  "NUT M16X1.5",                   2, "(2)"),
    (19, "WP-1612616-SE",  "WASHER 16X30X2.6",              2, "(2)"),
    (20, "WS-1643202-KR",  "SPRING WASHER",                  1, "(1)"),
]

assert len(parts) == 20
assert [p[0] for p in parts] == list(range(1, 21))

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
backup = BACKUP_DIR / (
    "garment-before-fix-thread-stand-section19-"
    + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)

src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(backup))
src.backup(dst)
dst.close()
src.close()
print("Backup:", backup)

con = sqlite3.connect(str(DB))
try:
    con.execute("BEGIN IMMEDIATE")

    if not con.execute(
        "SELECT 1 FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone():
        raise RuntimeError(f"Machine ID {MACHINE_ID} tidak ditemukan")

    existing = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id=? AND notes=?
    """, (MACHINE_ID, SECTION)).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Section 19 sudah berisi {existing} baris; INSERT dibatalkan."
        )

    con.executemany("""
        INSERT INTO parts (
            machine_id, source_document_id, part_number, part_name,
            quantity, catalog_ref, diagram_page, note,
            source_url, notes, quantity_raw
        )
        VALUES (?, NULL, ?, ?, ?, ?, NULL, 'COMMON', NULL, ?, ?)
    """, [
        (MACHINE_ID, pn, name, qty, ref, SECTION, raw)
        for ref, pn, name, qty, raw in parts
    ])

    rows = con.execute("""
        SELECT catalog_ref, COUNT(*)
        FROM parts
        WHERE machine_id=? AND notes=?
        GROUP BY catalog_ref
        ORDER BY catalog_ref
    """, (MACHINE_ID, SECTION)).fetchall()

    refs = [r[0] for r in rows]
    if refs != list(range(1, 21)) or any(n != 1 for _, n in rows):
        raise RuntimeError("Validasi REF gagal; transaksi dibatalkan.")

    con.commit()
    print("BERHASIL: Section 19 dimasukkan.")
    print("Jumlah baris:", len(rows))
    print("REF lengkap dan unik: 1–20")
    print("Backup:", backup)

except Exception:
    con.rollback()
    raise
finally:
    con.close()
