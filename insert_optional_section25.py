import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation

DB = Path("database/garment.db")
SECTION = "AMS-210EN catalog staging; section 25"
MACHINE_ID = 44

# Format: REF, PART NUMBER, PART NAME, QUANTITY RAW, NOTE
rows = [
(1, "400-92951", "FU-07", "1", "#03"),
(2, "400-89686", "FU INTERMEDIATE PRESSER ASM.", "(1)", "#03"),
(3, "GFU-01002000", "INVERTING LAC", "(1)", "COMMON"),
(4, "400-89688", "FU INTERMEDIATE PRESSER PLATE", "(1)", "COMMON"),
(5, "PA-1600801-A0", "AIR CYLINDER", "(1)", "COMMON"),
(6, "GFU-01006000", "TURN CYLINDER BRACKET", "(1)", "COMMON"),
(7, "B4303-210-000", "TURN AROUND CRANK BEARING", "(1)", "COMMON"),
(8, "B4314-210-000", "INTERMEDIATE PRESSER BASE", "(1)", "COMMON"),
(9, "RE-0400000-K0", "E-RING 4", "(1)", "COMMON"),
(10, "SS-6081210-SP", "SCREW 1/8-44 L=12", "(4)", "COMMON"),
(11, "SS-7060610-SP", "SCREW 3/32-56 L=5.5", "(1)", "COMMON"),
(12, "SS-6120940-SP", "SCREW 3/16-28 L=9", "(2)", "COMMON"),
(13, "SS-1090750-SP", "SCREW 9/64-40 L=7", "(2)", "COMMON"),
(14, "WP-0250516-SD", "WASHER 2.5X6X0.5", "(1)", "COMMON"),
(15, "B4306-220-000", "KNUCKLE", "(1)", "COMMON"),
(16, "BT-0400251-EB", "URETHANE HOSE BLACK", "(1.3)", "COMMON"),
(17, "PJ-0460525-03", "HOSE ELBOW", "(2)", "COMMON"),
(18, "SD-0460703-TP", "HINGE SCREW D=4.6 H=7", "(1)", "COMMON"),
(19, "400-89687", "FU INTERMEDIATE PRESSER LEFT", "(1)", "COMMON"),
(20, "B1816-280-000", "GUIDE PIN", "(1)", "COMMON"),
(21, "SM-6041000-SP", "SCREW M4 L=10", "(1)", "COMMON"),
(22, "WP-0480856-SP", "WASHER 4.8X8.4X0.8", "(1)", "COMMON"),
(23, "GFU-01001000", "TURN AROUND CRANK SHAFT", "(1)", "COMMON"),
(24, "400-89689", "FU OUTER PRESSER ASM.", "(1)", "#03"),
(25, "D2554-21X-X00", "COMPENSATING FOOT", "(2)", "COMMON"),
(26, "SS-5090610-SP", "SCREW 9/64-40 L=6", "(2)", "COMMON"),
(27, "SS-7110840-SP", "SCREW 11/64-40 L=7.8", "(4)", "COMMON"),
(28, "WP-0371026-SD", "WASHER 3.7X7X1", "(2)", "COMMON"),
(29, "WP-0480856-SP", "WASHER 4.8X8.4X0.8", "(4)", "COMMON"),
(30, "D2551-21X-X00", "WALKING FOOT (A)", "(1)", "COMMON"),
(31, "400-89691", "FU OUTER PRESSER PLATE", "(1)", "COMMON"),
(32, "400-89690", "FU OUTER PRESSER RIGHT", "(1)", "COMMON"),
(33, "B1816-280-000", "GUIDE PIN", "(1)", "COMMON"),
(34, "SM-6040800-SP", "SCREW", "(1)", "COMMON"),
(35, "WP-0480856-SP", "WASHER 4.8X8.4X0.8", "(1)", "COMMON"),
(36, "D2552-21X-X00", "WALKING FOOT (B)", "(1)", "COMMON"),
(37, "GFU-01007000", "SPRING", "(1)", "#01"),
(38, "WP-0502616-SD", "WASHER", "(1)", "COMMON"),
(39, "PV-1502091-00", "SOLENOID VALVE", "(1)", "COMMON"),
(40, "PF-0205030-A0", "REGULATOR", "(1)", "#02"),
(41, "PJ-3010405-05", "HALF UNION", "(2)", "#01"),
(42, "PJ-3010405-05", "HALF UNION", "(1)", "#02"),
(43, "400-35324", "SOLENOID VALVE CONNECTER ASM", "(1)", "COMMON"),
(44, "EA-9500B01-00", "CABLE BAND", "(3)", "COMMON"),
(45, "229-32800", "ACCESSORIE BAG", "(1)", "COMMON"),
(46, "400-92950", "FU-07 INSTRACTION MANUAL/PARTS", "(1)", "COMMON"),
(47, "400-58422", "WIPER RELAY CABLE ASM.", "1", "#05"),
(48, "400-36526", "AMS-210E(MU12)SET", "1", "COMMON"),
(49, "400-36524", "HOLDER PLATE", "(1)", "COMMON"),
(50, "400-36525", "PIPE HOLDER STUD", "(1)", "COMMON"),
(51, "400-35867", "WIPER ASM.", "1", "COMMON"),
(52, "NM-6040003-SC", "NUT M4", "(2)", "COMMON"),
(53, "HP-0002002-00", "PIN-SHAPE TERMINAL MALE", "(2)", "COMMON"),
(54, "HK-0188000-20", "2-POLE PLUG", "(1)", "COMMON"),
(55, "B2101-220-000", "WIPER SOLENOID", "(1)", "COMMON"),
(56, "400-36229", "WIPER CONNECTING PLATE", "(1)", "COMMON"),
(57, "400-35866", "WIPER_BASE", "(1)", "COMMON"),
(58, "400-36230", "WIPER INSTALLING PLATE", "(1)", "COMMON"),
(59, "B2107-210-000", "WIPER", "(1)", "COMMON"),
(60, "400-36392", "WIPER ARM", "(1)", "COMMON"),
(61, "SM-67506C0-TP", "SCREW M3.5 L=6", "(1)", "COMMON"),
(62, "SM-8050812-TP", "SCREW M5X8", "(1)", "COMMON"),
(63, "SD-0700406-TP", "SHOULDER SCREW", "(1)", "COMMON"),
(64, "SD-0640327-TP", "SHOULDER SCREW D=6.35 H=3.2", "(1)", "COMMON"),
(65, "SD-0640327-TP", "SHOULDER SCREW D=6.35 H=3.2", "(1)", "COMMON"),
(66, "WP-0371016-SD", "WASHER 3.7X8X1", "(1)", "COMMON"),
(67, "WP-0561616-SC", "WASHER 5.6X16X1.6", "(1)", "COMMON"),
(68, "400-35692", "NEEDLE COOLER ASM.", "1", "#04"),
(69, "400-92717", "NEEDLE_COOLER_ASM", "1", "COMMON"),
(70, "SL-4051091-SC", "SCREW M5X0.8 L=10", "(1)", "#04"),
(71, "400-92688", "NEEDLE_COOLER_COMPL", "(1)", "COMMON"),
(72, "400-10457", "WIPER_STOPPER", "(1)", "COMMON"),
(73, "PX-5000140-00", "PLUG", "(1)", "COMMON"),
(74, "BT-0400251-EB", "URETHANE HOSE BLACK", "(0.7)", "COMMON"),
(75, "BT-0400251-EB", "URETHANE HOSE BLACK", "(0.3)", "COMMON"),
(76, "PV-1502090-00", "5 PORT SOLENOID VALVE", "(1)", "COMMON"),
(77, "HX-0023300-00", "CLIP", "(3)", "COMMON"),
(78, "PC-0124010-00", "SPEED CONTROLLER", "(1)", "COMMON"),
(79, "400-35324", "SOLENOID VALVE CONNECTER ASM", "(1)", "COMMON"),
(80, "400-35694", "NEEDLE COOLER COMPL.", "(1)", "#04"),
(81, "400-98302", "UNDER_WIPER_SET", "1", "COMMON"),
(82, "400-97552", "WIPER_SHAFT_CAP", "(1)", "COMMON"),
(83, "B2107-210-D0B", "WIPER", "(1)", "COMMON"),
(84, "SM-8040412-TP", "SET SCREW M4 L=4", "(2)", "COMMON"),
(85, "B2557-210-DA0", "PLASTIC BLANK PLATE ASM.", "2", "#03"),
(86, "400-36479", "PLASTIC_BLANK_PLATE_ASM", "2", "#06"),
(87, "400-39543", "PLASTIC_BLANK_PLATE_ASM.", "2", "#07"),
(88, "400-86361", "PLASTIC_PLATE_STOPPER", "2", "#08"),
(89, "SM-6040450-TP", "SCREW M4 L=4", "1", "#08"),
(90, "PJ-3095200-01", "SOCKET", "1", "#09"),
(91, "PB-0000100-00", "HOSE BAND", "1", "#09"),
(92, "B9141-372-000", "HEXAGONAL WRENCH LARGE", "1", "COMMON"),
(93, "229-33006", "SCREW DRIVER LARGE", "1", "COMMON"),
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

if len(rows) != 93 or [r[0] for r in rows] != list(range(1, 94)):
    raise SystemExit("Data sumber tidak valid: REF harus lengkap 1–93.")

backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"garment-before-insert-optional-section25-{stamp}.db"
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
            f"INSERT dibatalkan: Section 25 sudah memiliki {existing} baris."
        )

    payload = []
    for ref, part_no, part_name, raw, note in rows:
        payload.append((
            MACHINE_ID,
            part_no,
            part_name,
            parse_quantity(raw),
            ref,
            note,
            SECTION,
            raw
        ))

    con.executemany("""
        INSERT INTO parts (
            machine_id,
            part_number,
            part_name,
            quantity,
            catalog_ref,
            note,
            notes,
            quantity_raw
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

# Audit sesudah commit
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

result = con.execute("""
    SELECT catalog_ref, part_number, part_name, quantity,
           quantity_raw, note
    FROM parts
    WHERE machine_id=? AND notes=?
    ORDER BY catalog_ref
""", (MACHINE_ID, SECTION)).fetchall()

refs = [r["catalog_ref"] for r in result]
duplicates = sorted({x for x in refs if refs.count(x) > 1})
missing = sorted(set(range(1, 94)) - set(refs))

print("\n=== AUDIT SECTION 25 ===")
print("Jumlah baris:", len(result))
print("REF lengkap 1–93:", not missing and len(refs) == 93)
print("REF hilang:", missing)
print("REF duplikat:", duplicates)
print("Kuantitas desimal:")
for r in result:
    if r["quantity"] is None:
        print(dict(r))

con.close()
