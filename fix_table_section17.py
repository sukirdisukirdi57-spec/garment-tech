import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
SECTION = "AMS-210EN catalog staging; section 17"
MACHINE_ID = 44

# REF, PART NO, DESCRIPTION, QTY, QTY RAW, NOTE
parts = [
    (1,  "141-91951",      "T-STAND COMPL.",                 1, "1",    "#01"),
    (2,  "400-38255",      "T-STAND COMPL.(AIR TYPE)",       1, "1",    "#03"),
    (3,  "B8101-210-AAB",  "UPPER STAND COMPL.",             1, "(1)",  "COMMON"),
    (4,  "141-18152",      "UPPER STAND ASM. RIGHT",         1, "(1)",  "COMMON"),
    (5,  "111-58409",      "STAND SIDE SUPPORT",             1, "(1)",  "COMMON"),
    (6,  "111-58607",      "RUBBER CAP",                     4, "(4)",  "COMMON"),
    (7,  "B8105-210-AAA",  "STAND COMPL.",                   1, "(1)",  "COMMON"),
    (8,  "141-18251",      "STAND ASM. RIGHT",               1, "(1)",  "COMMON"),
    (9,  "170-07402",      "NUT",                            2, "(2)",  "COMMON"),
    (10, "111-58516",      "UPPER STAND PLATE",              2, "(2)",  "COMMON"),
    (11, "SL-9082091-SE",  "WASHER HEXAGONAL BOLT",         10, "(10)", "#01"),
    (12, "SL-9082091-SE",  "WASHER HEXAGONAL BOLT",         12, "(12)", "#03"),
    (13, "138-17754",      "Z-STAND PEDAL COMPL.",           1, "(1)",  "#01"),
    (14, "WP-0871602-SE",  "WASHER 8.7X18X1.6",              4, "(4)",  "#01"),
    (15, "WS-0861410-KR",  "SPRING WASHER 8.6X15X1.4",      2, "(2)",  "#01"),
    (16, "NM-6080721-SE",  "NUT M8",                         2, "(2)",  "#01"),
    (17, "111-59001",      "PEDAL SHAFT BRACKET",             2, "(2)",  "#01"),
    (18, "B8153-771-000",  "PEDAL CONNECTING ROD",            1, "(1)",  "#01"),
    (19, "D8113-555-B00",  "PEDAL BUSHING",                  2, "(2)",  "#01"),
    (20, "GPF-06080000",   "PEDAL ADJUSTING PLATE",           1, "(1)",  "#01"),
    (21, "GPF-060600A0",   "PEDAL COMPL.",                   1, "(1)",  "#01"),
    (22, "SM-9061203-SE",  "SCREW M6 L=12",                  2, "(2)",  "#01"),
    (23, "WP-0671016-SE",  "WASHER 6.7X13X1",                2, "(2)",  "#01"),
    (24, "WS-0621210-KR",  "SPRING WASHER 6.2X11.4X1.2",    2, "(2)",  "#01"),
    (25, "SM-9082023-SE",  "SCREW M8 L=20",                 2, "(2)",  "#01"),
    (26, "WP-0871602-SE",  "WASHER 8.7X18X1.6",              2, "(2)",  "#01"),
    (27, "111-59506",      "STRUT AUXILIARY PLATE",           2, "(2)",  "#01"),
    (28, "WS-0861410-KR",  "SPRING WASHER 8.6X15X1.4",      2, "(2)",  "#01"),
    (29, "B8150-210-000",  "CASTER",                         4, "(4)",  "COMMON"),
    (30, "NM-6120003-SE",  "NUT M12",                        4, "(4)",  "COMMON"),
    (31, "SM-9086523-SE",  "HEXAGONAL BOLT",                 2, "(2)",  "#01"),
    (32, "111-58300",      "STAND SIDE SUPPORT",             1, "(1)",  "COMMON"),
    (33, "B1115-210-D00",  "HINGE RUBBER",                   2, "2",    "#02"),
    (34, "SM-6066002-TN",  "BOLT M6 L=60",                   4, "4",    "#02"),
    (35, "400-30949",      "TABLE",                          1, "1",    "COMMON"),
    (36, "111-55157",      "DRAWER ASM.",                    1, "1",    "COMMON"),
    (37, "111-55108",      "DRAWER",                         1, "(1)",  "COMMON"),
    (38, "111-55207",      "DRAWER SUPPORT",                 2, "(2)",  "COMMON"),
    (39, "SK-3311600-SC",  "WOOD SCREW D=3.1 L=16",          6, "(6)",  "COMMON"),
    (40, "D8204-555-D00",  "DRAWER STOPPER",                 1, "(1)",  "COMMON"),
    (41, "NM-6080001-SC",  "NUT M8X1.25",                    1, "1",    "#02"),
    (42, "SM-6086002-TP",  "SCREW",                          1, "1",    "#02"),
    (43, "WP-0851846-SC",  "WASHER 8.5X22.0X1.8",           1, "1",    "#02"),
    (44, "B8202-205-000",  "OIL MANAGEMENT",                 1, "1",    "#02"),
    (45, "B9121-012-000",  "OIL CAN",                        1, "1",    "#02"),
    (46, "SK-3311601-SE",  "WOOD SCREW D=3.1 L=16",          2, "2",    "#02"),
    (47, "WP-0651646-SC",  "WASHER",                         4, "4",    "#02"),
    (48, "NM-6060001-SC",  "NUT M6",                         8, "8",    "#02"),
    (49, "B1111-210-D00",  "BED HINGE",                      2, "2",    "#02"),
    (50, "ST-9053511-SR",  "TAPPING SCREW M5X35",            4, "4",    "COMMON"),
]

assert len(parts) == 50
assert [p[0] for p in parts] == list(range(1, 51))
assert all(p[1] and p[2] and p[4] for p in parts)

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"garment-before-fix-table-section17-{stamp}.db"

# Backup konsisten menggunakan SQLite backup API.
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(backup))
src.backup(dst)
dst.close()
src.close()
print("Backup:", backup)

con = sqlite3.connect(str(DB))
try:
    con.execute("BEGIN IMMEDIATE")

    machine = con.execute(
        "SELECT id FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone()
    if not machine:
        raise RuntimeError(f"Machine ID {MACHINE_ID} tidak ditemukan")

    existing = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id=? AND notes=?
    """, (MACHINE_ID, SECTION)).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Section 17 sudah memiliki {existing} baris. Dibatalkan."
        )

    con.executemany("""
        INSERT INTO parts (
            machine_id, source_document_id, part_number, part_name,
            quantity, catalog_ref, diagram_page, note,
            source_url, notes, quantity_raw
        )
        VALUES (?, NULL, ?, ?, ?, ?, NULL, ?, NULL, ?, ?)
    """, [
        (MACHINE_ID, pn, name, qty, ref, note, SECTION, raw)
        for ref, pn, name, qty, raw, note in parts
    ])

    result = con.execute("""
        SELECT catalog_ref, COUNT(*) AS n
        FROM parts
        WHERE machine_id=? AND notes=?
        GROUP BY catalog_ref
        ORDER BY catalog_ref
    """, (MACHINE_ID, SECTION)).fetchall()

    refs = [r[0] for r in result]
    duplicates = [r[0] for r in result if r[1] != 1]

    if refs != list(range(1, 51)) or duplicates:
        raise RuntimeError("Validasi REF 1–50 gagal; transaksi dibatalkan")

    con.commit()
    print("BERHASIL: Section 17 dimasukkan.")
    print("Jumlah baris:", len(result))
    print("REF lengkap dan unik: 1–50")
    print("Backup:", backup)

except Exception:
    con.rollback()
    raise
finally:
    con.close()
