import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
SECTION = "AMS-210EN catalog staging; section 24"

# REF, NOTE, PART NO, DESCRIPTION, QTY RAW
data = [
    (1,  "☆",       "B1806-210-D00", "BOBBIN",                         "1"),
    (2,  "#02",     "EA-9500B01-00", "CABLE BAND",                     "1"),
    (3,  "#09",     "400-48664",     "HEAD_COVER",                     "1"),
    (4,  "☆ #04",   "MDP-500B1402",  "NEEDLE DPX5#14-2",               "1"),
    (5,  "☆ #05",   "MDP-170B1802",  "NEEDLE DPZ17#18-2",              "1"),
    (6,  "☆ #06",   "MC-2005010-02", "NEEDLE 134 #100-2",              "1"),
    (7,  "☆ #07",   "MC-3720011-02", "NEEDLE SY3355 #110-2",           "1"),
    (8,  "COMMON",  "229-33204",     "SCREW DRIVER SMALL",             "1"),
    (9,  "COMMON",  "B9113-012-000", "WRENCH (9X10)",                  "1"),
    (10, "COMMON",  "B9140-372-000", "HEXAGONAL WRENCH SMALL",         "1"),
    (11, "COMMON",  "400-32763",     "HEXAGONAL_DRIVER(1.5)",          "1"),
    (12, "#08",     "131-60304",     "S SHAPED HOOK",                  "2"),
    (13, "#08",     "260-37903",     "CHAIN",                          "1"),
    (14, "#02",     "HX-0015000-0D", "CABLE CLIP",                     "1"),
    (15, "#03",     "291-86403",     "EC DECLARATION",                 "1"),
    (16, "COMMON",  "B9121-220-0A0", "OILER (CONTAINING NO.2 OIL)",    "1"),
    (17, "#02",     "229-32800",     "ACCESSORIE BAG",                 "1"),
    (18, "#02",     "PX-5000140-00", "PLUG",                           "2"),
    (19, "COMMON",  "229-33105",     "SCREW DRIVER MIDDLE",            "1"),
    (20, "#01",     "262-34005",     "VINYL COVER",                    "1"),
    (21, "COMMON",  "B1131-528-000", "FELT",                           "1"),
    (22, "COMMON",  "101-02200",     "THREAD GUIDE F",                 "1"),
    (23, "COMMON",  "SM-6040860-TP", "SCREW M4 L=8",                   "1"),
    (24, "COMMON",  "B9101-490-000", "DRIVER",                         "1"),
    (25, "COMMON",  "229-32800",     "ACCESSORIE BAG",                 "1"),
    (26, "#03",     "CM-6001002-01", "WEEE INFORMATION SHEET",         "1"),
]

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

if [r[0] for r in data] != list(range(1, 27)):
    raise SystemExit("REF tidak lengkap 1–26. Dibatalkan.")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
backup = BACKUP_DIR / (
    "garment-before-fix-accessorie-parts-section24-"
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
            f"Section 24 sudah berisi {count} baris. Transaksi dibatalkan."
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

print("\n=== AUDIT SECTION 24 ===")
print("Jumlah baris:", len(rows))
print("REF lengkap 1–26:", refs == list(range(1, 27)))
print("REF duplikat:", len(refs) - len(set(refs)))
print("Jumlah kuantitas 2:", sum(1 for r in rows if r[3] == 2))

for row in rows:
    print(row)

con.close()
