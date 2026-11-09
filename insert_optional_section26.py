import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation

DB = Path("database/garment.db")
SECTION = "AMS-210EN catalog staging; section 26"
MACHINE_ID = 44

# REF, PART NUMBER, DESCRIPTION, QTY RAW, NOTE
rows = [
(1, "B1601-210-D0B-A", "INTERMEDIATE PRESSER B", "1", "COMMON"),
(2, "B1601-210-D0C-A", "INTERMEDIATE PRESSER C", "1", "COMMON"),
(3, "B1601-210-D0E", "INNER PRESSER E", "1", "COMMON"),
(4, "B1601-210-D0F-A", "INTERMEDIATE PRESSER F", "1", "COMMON"),
(5, "141-03253", "INNER HOOK PRESSER ASM. A", "1", "COMMON"),
(6, "141-03659", "SHUTTLE RACE RING ASM. C", "1", "COMMON"),
(7, "B1817-210-DAD", "SHUTTLE RACE RING ASM. D", "1", "COMMON"),
(8, "400-35606", "FEEDING FRAME BLANK", "1", "COMMON"),
(9, "400-35607", "FEEDING FRAME BLANK", "1", "COMMON"),
(10, "400-35608", "FEEDING FRAME BLANK", "1", "COMMON"),
(11, "400-35609", "FEEDING FRAME BLANK R", "1", "COMMON"),
(12, "400-35610", "FEEDING FRAME BLANK L", "1", "COMMON"),
(13, "B2556-210-D0A", "LOWER PLATE BLANK", "1", "#03"),
(14, "B2556-210-D0B", "LOWER PLATE BLANK", "1", "#03"),
(15, "B2594-210-DA0", "CASSETTE PRESSER ASM.", "1", "COMMON"),
(16, "B2594-210-D00", "CASSETTE PRESSER BASE PLATE", "(1)", "COMMON"),
(17, "B2598-210-D00", "CASSETTE PRESSER LOWER PLATE", "(1)", "COMMON"),
(18, "B2599-210-D00", "CASSETTE PRESSER UPPER PLATE", "(1)", "COMMON"),
(19, "B2589-210-D00", "CASSETTE PRESSER SPACER", "(1)", "COMMON"),
(20, "B2572-229-000", "FILAMENT TAPE", "(1)", "COMMON"),
(21, "B2646-215-000", "TAPE", "(1)", "COMMON"),
(22, "B2587-210-000", "MATERIAL PLATE A", "(1)", "COMMON"),
(23, "B2593-210-DA0", "CASSETTE HOLDER FIX PLATE ASM.", "1", "COMMON"),
(24, "B2593-210-D00", "CASSETTE HOLDER FIXING PLATE", "(1)", "COMMON"),
(25, "B2560-372-000", "BUTTON CLAMP STOP PIN", "(2)", "COMMON"),
(26, "400-89692", "ONE-TOUCH CLAMP ASM.", "1", "#01"),
(27, "400-89693", "PRESSER PLATE ASM.", "(1)", "COMMON"),
(28, "400-89694", "PRESSER PLATE", "(1)", "COMMON"),
(29, "B2587-210-D00", "SLIDER HOLDING", "(1)", "COMMON"),
(30, "B5038-206-000", "SET SC", "(1)", "COMMON"),
(31, "B5039-206-000", "SET PLATE", "(1)", "COMMON"),
(32, "161-08300", "NUT B", "(1)", "COMMON"),
(33, "SS-7110840-SP", "SCREW 11/64-40 L=7.8", "(2)", "COMMON"),
(34, "WP-0480856-SP", "WASHER 4.8X8.4X0.8", "(2)", "COMMON"),
(35, "WZ-0430200-KH", "WAVED WASHER", "(1)", "COMMON"),
(36, "B2595-210-DA0", "SLIDER ASM.", "(1)", "COMMON"),
(37, "B2595-210-D00", "SLIDER", "(1)", "COMMON"),
(38, "B1816-280-000", "GUIDE PIN", "(4)", "COMMON"),
(39, "B2597-210-D00", "CLAMP PLATE", "(1)", "COMMON"),
(40, "B5115-210-000", "FEEDING FRAME CLAMP LEVER", "(2)", "COMMON"),
(41, "400-89695", "ONE-TOUCH CLAMP ASM.", "1", "#02"),
(42, "400-89696", "PRESSER PLATE RIGHT ASM.", "(1)", "COMMON"),
(43, "400-89697", "PRESSER PLATE RIGHT", "(1)", "COMMON"),
(44, "B2588-210-D00", "SLIDER HOLDING", "(1)", "COMMON"),
(45, "B5038-206-000", "SET SC", "(1)", "COMMON"),
(46, "B5039-206-000", "SET PLATE", "(1)", "COMMON"),
(47, "161-08300", "NUT B", "(1)", "COMMON"),
(48, "SS-7110840-SP", "SCREW 11/64-40 L=7.8", "(2)", "COMMON"),
(49, "WP-0480856-SP", "WASHER 4.8X8.4X0.8", "(2)", "COMMON"),
(50, "WZ-0430200-KH", "WAVED WASHER", "(1)", "COMMON"),
(51, "400-89698", "PRESSER PLATE LEFT ASM.", "(1)", "COMMON"),
(52, "400-89699", "PRESSER PLATE LEFT", "(1)", "COMMON"),
(53, "B2588-210-D00", "SLIDER HOLDING", "(1)", "COMMON"),
(54, "B5038-206-000", "SET SC", "(1)", "COMMON"),
(55, "B5039-206-000", "SET PLATE", "(1)", "COMMON"),
(56, "161-08300", "NUT B", "(1)", "COMMON"),
(57, "SS-7110840-SP", "SCREW 11/64-40 L=7.8", "(2)", "COMMON"),
(58, "WP-0480856-SP", "WASHER 4.8X8.4X0.8", "(2)", "COMMON"),
(59, "WZ-0430200-KH", "WAVED WASHER", "(1)", "COMMON"),
(60, "B2596-210-DA0", "SLIDER ASM. RIGHT", "(1)", "COMMON"),
(61, "B2596-210-D00", "SLIDER", "(1)", "COMMON"),
(62, "PS-0400082-KP", "SPRING PIN", "(3)", "COMMON"),
(63, "B2596-210-DAA", "SLIDER ASM. LEFT", "(1)", "COMMON"),
(64, "B2596-210-D00", "SLIDER", "(1)", "COMMON"),
(65, "PS-0400082-KP", "SPRING PIN", "(3)", "COMMON"),
(66, "B2597-210-D00", "CLAMP PLATE", "(1)", "COMMON"),
(67, "B5115-210-000", "FEEDING FRAME CLAMP LEVER", "(2)", "COMMON"),
(68, "B2535-210-000", "TANK BASE", "1", "COMMON"),
(69, "SM-4040855-SP", "SCREW", "2", "COMMON"),
(70, "400-72310", "THREAD TENTION NO.3 ASSY", "1", "COMMON"),
(71, "400-40560", "THREAD TENSION NO.3 ASM.", "(1)", "COMMON"),
(72, "B3114-771-000", "THREAD GUIDE", "(2)", "COMMON"),
(73, "NS-6090310-SP", "NUT 9/64-40", "(2)", "COMMON"),
(74, "PJ-3010405-02", "HALF UNION 4XM5", "(1)", "COMMON"),
(75, "NM-6160511-SE", "NUT M16X1.5", "(1)", "COMMON"),
(76, "PA-0600504-A0", "AIR CYLINDER", "(1)", "COMMON"),
(77, "G2302-309-000", "THREAD TENSION ROD BASE", "(1)", "COMMON"),
(78, "G2301-309-000", "THREAD TENSION ROD", "(1)", "COMMON"),
(79, "B3126-012-000", "THREAD TENSION DISK", "(2)", "COMMON"),
(80, "B3132-552-000", "THREAD TENSION DISK PRESSER", "(1)", "COMMON"),
(81, "B3121-352-000", "TENSION SPRING", "(1)", "COMMON"),
(82, "B3120-125-000", "ROTATING STOPPER", "(1)", "COMMON"),
(83, "110-72204", "TENSION NUT", "(1)", "COMMON"),
(84, "BT-0400251-EB", "URETHANE HOSE BLACK", "(2)", "COMMON"),
(85, "D4012-D10-N0H", "THREAD TENSION NO.3 BASE", "(1)", "COMMON"),
(86, "PV-1502090-00", "5 PORT SOLENOID VALVE", "(1)", "COMMON"),
(87, "PX-5000140-00", "PLUG", "(1)", "COMMON"),
(88, "400-35324", "SOLENOID VALVE CONNECTER ASM", "(1)", "COMMON"),
(89, "SM-6062002-TP", "SCREW M6 L=20", "(1)", "COMMON"),
(90, "WP-0612516-SD", "WASHER 6.1X15.2X2.5", "(1)", "COMMON"),
(91, "B3532-223-C00", "SILICON TANK", "1", "COMMON"),
(92, "B2426-210-00C", "NEEDLE HOLE GUIDE D=1.6", "1", "COMMON"),
(93, "B2426-210-00F", "NEEDLE HOLE GUIDE D=3.0", "1", "COMMON"),
(94, "B2426-210-00G", "NEEDLE HOLE GUIDE D=3", "1", "COMMON"),
(95, "B2426-210-00H", "NEEDLE HOLE GUIDE D=3.0", "1", "COMMON"),
(96, "400-14965", "SHUTTLE(H)", "1", "COMMON"),
(97, "400-98294", "INNER_PRESSER", "1", "COMMON"),
(98, "400-99714", "LOWER_PLATE_BLANK", "1", "#04"),
(99, "B2552-210-D00", "LOWER PLATE", "1", "#03"),
(100, "400-36477", "LOWER_PLATE", "1", "#05"),
]

def parse_quantity(raw):
    value = raw.strip().strip("()")
    try:
        number = Decimal(value)
        if number == number.to_integral_value():
            return int(number)
        return None
    except InvalidOperation:
        return None

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

if len(rows) != 100 or [r[0] for r in rows] != list(range(1, 101)):
    raise SystemExit("Data tidak valid: REF harus lengkap 1-100.")

backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"garment-before-insert-optional-section26-{stamp}.db"

shutil.copy2(DB, backup)
print("Backup:", backup)

con = sqlite3.connect(DB)

try:
    con.execute("BEGIN IMMEDIATE")

    existing = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id=? AND notes=?
    """, (MACHINE_ID, SECTION)).fetchone()[0]

    if existing != 0:
        raise RuntimeError(
            f"INSERT dibatalkan: Section 26 sudah memiliki {existing} baris."
        )

    payload = [
        (
            MACHINE_ID,
            part_no,
            part_name,
            parse_quantity(raw),
            ref,
            note,
            SECTION,
            raw
        )
        for ref, part_no, part_name, raw, note in rows
    ]

    con.executemany("""
        INSERT INTO parts (
            machine_id, part_number, part_name, quantity,
            catalog_ref, note, notes, quantity_raw
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, payload)

    con.commit()
    print("INSERT berhasil:", len(payload), "baris")

except Exception:
    con.rollback()
    raise
finally:
    con.close()

# Audit akhir
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

result = con.execute("""
    SELECT catalog_ref, part_number, part_name,
           quantity, quantity_raw, note
    FROM parts
    WHERE machine_id=? AND notes=?
    ORDER BY catalog_ref
""", (MACHINE_ID, SECTION)).fetchall()

refs = [r["catalog_ref"] for r in result]
missing = sorted(set(range(1, 101)) - set(refs))
duplicates = sorted({x for x in refs if refs.count(x) > 1})

print("\n=== AUDIT SECTION 26 ===")
print("Jumlah baris:", len(result))
print("REF lengkap 1-100:", not missing and len(refs) == 100)
print("REF hilang:", missing)
print("REF duplikat:", duplicates)

print("\n=== CEK KUANTITAS RAW ===")
for r in result:
    if r["quantity_raw"].startswith("("):
        print(
            f"REF {r['catalog_ref']}: "
            f"{r['part_number']} | "
            f"quantity={r['quantity']} | "
            f"raw={r['quantity_raw']}"
        )

con.close()
