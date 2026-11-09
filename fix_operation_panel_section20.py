import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
SECTION = "AMS-210EN catalog staging; section 20"

# REF, NOTE, PART NO, DESCRIPTION, QTY RAW
data = [
(1,  "",      "400-86485",      "IP-420F PANEL ASSY",                 "1"),
(2,  "",      "400-78163",      "FRONT_CASE",                         "(1)"),
(3,  "",      "400-80799",      "REAR_CASE_ASSY",                     "(1)"),
(4,  "",      "400-80800",      "LCD_ASSY",                           "(1)"),
(5,  "",      "400-86541",      "LCD TOUCH PANEL ASSY",               "(1)"),
(6,  "",      "400-83668",      "LCD_BRACKET",                        "(1)"),
(7,  "",      "400-83666",      "LCD_STAY",                           "(1)"),
(8,  "",      "SL-4030681-SC",  "SCREW M3 L=6",                       "(2)"),
(9,  "",      "400-78168",      "INSULATION_SHEET",                   "(1)"),
(10, "",      "400-83960",      "PANEL PCB ASSY",                     "(1)"),
(11, "",      "SL-4030681-SC",  "SCREW M3 L=6",                       "(3)"),
(12, "",      "HX-0035400-0B",  "PCB SUPPORT L=8MM",                  "(2)"),
(13, "",      "SL-4030881-SC",  "SCREW M3X8",                         "(4)"),
(14, "",      "CM-6001001-01",  "WEEE MARK LABEL S",                  "(1)"),
(15, "",      "HW-0021802-00",  "FLAT CABLE",                         "(1)"),
(16, "",      "400-81602",      "POWER SWITCH ASM",                   "1"),
(17, "",      "HA-0058200-00",  "SWITCH",                             "(1)"),
(18, "",      "400-81603",      "SWITCH INSTALLATION BOARD",          "(1)"),
(19, "",      "SL-4041091-SE",  "SCREW M4 L=10",                      "(2)"),
(20, "#01",   "CM-3001004-01",  "LABEL 3 (LARGE)",                    "1"),
(21, "#01",   "BME-01100000",   "VOLTAGE INDICATION SEAL",            "1"),
(22, "#02",   "CM-3004007-01",  "VOLTAGE CAUTION LABEL",              "1"),
(23, "#02",   "BME-03200000",   "VOLTAGE INDICATION SEAL",            "1"),
(24, "#03",   "CM-3001000-03",  "VOLTAGE WARNING LABEL(25)",          "1"),
(25, "#03",   "CM-3004006-01",  "VOLTAGE CAUTION LABEL",              "1"),
(26, "",      "400-85316",      "OPTION A ASSY",                      "1"),
(27, "",      "M3004-511-00A",  "VOLTAGE INDICATION CARD A",          "(1)"),
(28, "",      "HF-0013031-5S",  "FUSE 3.15A 250V REF. NO.112",        "(1)"),
(29, "",      "HF-0030002-00",  "FUSE 2A (220/240V)",                 "(1)"),
(30, "",      "HF-0013050-P0",  "FUSE 5A",                            "(1)"),
(31, "",      "MA-0115320-00",  "STAPLE",                             "(3)"),
(32, "",      "SK-3512001-SE",  "WOOD SCREW D=5.1 L=20",              "(2)"),
(33, "",      "MTS-HJ100003",   "BOLT",                               "(2)"),
(34, "",      "SM-6084002-TN",  "SCREW M8 L=40",                      "(1)"),
(35, "",      "WP-0852086-SC",  "WASHER M8",                          "(2)"),
(36, "",      "WP-0841601-SC",  "WASHER 8.4X17.4X1.6",                "(1)"),
(37, "",      "WS-0820002-KR",  "SPRING WASHER M8",                   "(3)"),
(38, "",      "NM-6080002-SC",  "NUT M8",                             "(2)"),
(39, "",      "HX-0015000-0D",  "CABLE CLIP",                         "(2)"),
(40, "",      "SL-4040881-SC",  "SCREW M4 L=8",                       "(2)"),
(41, "",      "HX-0006500-0A",  "CABLE CLIP",                         "(2)"),
(42, "#01",   "400-86468",      "POWER CABLE 1P PLUG ASSY",           "1"),
(43, "#01",   "M9034-580-0A0",  "GROUND CORD ASM.",                   "1"),
(44, "#02",   "400-86469",      "POWER CABLE 3P ASSY",                "1"),
(45, "#03",   "400-86470",      "POWER CABLE 1P ASSY",                "1"),
(46, "",      "400-65566",      "PANEL CABLE D ASM",                  "1"),
(47, "",      "400-35024",      "OPERATION_BOX_FIXED_PLATE(B)ASM",    "1"),
(48, "",      "SK-3413201-SE",  "WOOD SCREW D=4.1 L=32",              "2"),
(49, "#02",   "CM-3001004-01",  "LABEL 3 (LARGE)",                    "1"),
(50, "＊ #04", "403-11568",     "IP-510B PANEL ASSY",                 "1"),
(51, "＊ #04", "402-95563",     "PANEL CABLE ASSY",                   "1"),
]

# QTY numerik: panjang dalam meter (mis. 0.1/2.5) tetap boleh desimal.
def parse_qty(raw):
    value = raw.strip().strip("()")
    try:
        number = float(value)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return None

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"garment-before-fix-operation-panel-section20-{stamp}.db"

# Backup sebelum perubahan apa pun.
shutil.copy2(DB, backup)
print("BACKUP:", backup)

con = sqlite3.connect(DB)
try:
    con.execute("BEGIN IMMEDIATE")

    existing = con.execute("""
        SELECT COUNT(*)
        FROM parts
        WHERE machine_id = 44 AND notes = ?
    """, (SECTION,)).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Section 20 sudah memiliki {existing} baris; dibatalkan agar tidak duplikat."
        )

    # Cegah REF yang sama dan nomor komponen yang tidak sesuai data sumber.
    refs = [row[0] for row in data]
    if refs != list(range(1, 52)):
        raise RuntimeError("REF tidak lengkap atau tidak berurutan 1–51.")

    for ref, note, part_no, name, qty_raw in data:
        con.execute("""
            INSERT INTO parts (
                machine_id, part_number, part_name, quantity,
                catalog_ref, note, notes, quantity_raw
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            44, part_no, name, parse_qty(qty_raw), ref,
            note if note else "COMMON", SECTION, qty_raw
        ))

    con.commit()
except Exception:
    con.rollback()
    raise
finally:
    con.close()

# Audit setelah commit.
con = sqlite3.connect(DB)
rows = con.execute("""
    SELECT catalog_ref, part_number, part_name, quantity,
           quantity_raw, note
    FROM parts
    WHERE machine_id = 44 AND notes = ?
    ORDER BY catalog_ref
""", (SECTION,)).fetchall()

refs = [r[0] for r in rows]
print("\n=== AUDIT SECTION 20 ===")
print("Jumlah baris:", len(rows))
print("REF lengkap 1–51:", refs == list(range(1, 52)))
print("REF duplikat:", len(refs) - len(set(refs)))
print("REF 39:", [dict(zip(
    ["catalog_ref", "part_number", "part_name", "quantity",
     "quantity_raw", "note"], r
)) for r in rows if r[0] == 39])
print("REF 50–51:")
for r in rows:
    if r[0] in (50, 51):
        print(r)

con.close()
