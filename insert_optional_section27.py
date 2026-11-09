import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
MARKER = "AMS-210EN catalog staging; section 27"

# REF, PART NO, DESCRIPTION, QTY RAW, NOTE
data = [
(1, "400-42352", "MECHANICAL VALVE UNIT", "1", "#01"),
(2, "D8001-D15-A0Y", "PEDAL BASE", "(1)", "COMMON"),
(3, "D8002-D15-A0Y", "PEDAL CUSHION", "(2)", "COMMON"),
(4, "SS-6111210-SP", "SCREW 11/64-40 L=12", "(2)", "COMMON"),
(5, "WP-0450801-SD", "WASHER 4.5X10X0.8", "(2)", "COMMON"),
(6, "WS-0451040-KP", "SPRING WASHER 4.5X8.5X1", "(2)", "COMMON"),
(7, "WP-0553216-SD", "WASHER", "(2)", "COMMON"),
(8, "PX-0200020-00", "ACTUATOR", "(1)", "COMMON"),
(9, "PV-0105020-00", "AIR VALVE", "(1)", "COMMON"),
(10, "PJ-3010405-01", "HALF UNION M5 D=4", "(6)", "COMMON"),
(11, "PX-5000140-00", "PLUG", "(2)", "COMMON"),
(12, "BT-0400251-EB", "URETHANE HOSE BLACK", "(1.9)", "COMMON"),
(13, "BT-0400251-EB", "URETHANE HOSE BLACK", "(1.8)", "COMMON"),
(14, "BT-0400251-EB", "URETHANE HOSE BLACK", "(1.9)", "COMMON"),
(15, "HX-0031400-0A", "SPIRAL TUBE", "(0.6)", "COMMON"),
(16, "EA-9500B01-00", "CABLE BAND", "(3)", "COMMON"),
(17, "GEP-01013000", "VALVE", "(1)", "COMMON"),
(18, "BT-0400251-EB", "URETHANE HOSE BLACK", "(0.1)", "COMMON"),
(19, "BT-0400251-EB", "URETHANE HOSE BLACK", "(0.1)", "COMMON"),
(20, "180-35204", "WIRE MARK (3)", "(2)", "COMMON"),
(21, "180-35303", "WIRE MARK (4)", "(1)", "COMMON"),
(22, "180-35600", "WIRE MARK (7)", "(2)", "COMMON"),
(23, "180-35709", "WIRE MARK (8)", "(1)", "COMMON"),
(24, "PJ-3080400-02", "QUICK COUPLING", "(2)", "COMMON"),
(25, "WP-0450801-SD", "WASHER 4.5X10X0.8", "(2)", "COMMON"),
(26, "WS-0451040-KP", "SPRING WASHER 4.5X8.5X1", "(2)", "COMMON"),
(27, "SS-7111120-TP", "SCREW", "(2)", "COMMON"),
(28, "400-89848", "AIR UNIT ASM.", "1", "#01"),
(29, "PV-9150050-00", "SOLENOID VALVE INSTALLING BASE", "(1)", "COMMON"),
(30, "SK-3412001-SE", "WOOD SCREW D=4.1 L=20", "(2)", "COMMON"),
(31, "PJ-3040600-01", "ELBOW", "(1)", "COMMON"),
(32, "PX-0500030-00", "SILENCER", "(1)", "COMMON"),
(33, "BT-0600401-EB", "TUBE", "(1.3)", "COMMON"),
(34, "400-30951", "FILTER_REGULATOR_ASM.", "(1)", "COMMON"),
(35, "SL-4051091-SC", "SCREW M5X0.8 L=10", "(2)", "COMMON"),
(36, "400-23662", "FILTER INSTALLING PLATE", "(1)", "COMMON"),
(37, "SL-9082093-SE", "SCREW", "(1)", "COMMON"),
(38, "WP-0871602-SE", "WASHER 8.7X18X1.6", "(1)", "COMMON"),
(39, "NM-6080721-SE", "NUT M8", "(1)", "COMMON"),
(40, "400-48529", "VALVE RELAY CORD ASM", "(1)", "COMMON"),
(41, "400-81601", "AIR RELAY CABLE ASM", "(1)", "COMMON"),
(42, "PJ-3095200-01", "SOCKET", "(1)", "COMMON"),
(43, "PB-0000100-00", "HOSE BAND", "(1)", "COMMON"),
(44, "EA-9500B01-00", "CABLE BAND", "(1)", "COMMON"),
(45, "400-93109", "AIR SW CABLE ASM", "(1)", "COMMON"),
]

# Validasi sumber sebelum menyentuh database
refs = [r[0] for r in data]
assert len(data) == 45
assert refs == list(range(1, 46))
assert len(set(refs)) == len(refs)

con = sqlite3.connect(DB)
try:
    con.execute("PRAGMA foreign_keys=ON")

    existing = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id=44 AND notes=?
    """, (MARKER,)).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Section 27 sudah berisi {existing} baris. Dibatalkan."
        )

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = Path(f"backups/garment-before-insert-optional-section27-{stamp}.db")
    backup.parent.mkdir(exist_ok=True)
    con.commit()
    shutil.copy2(DB, backup)
    print("BACKUP:", backup)

    con.execute("BEGIN IMMEDIATE")

    for ref, part_no, description, qty_raw, note in data:
        # Kuantitas desimal disimpan di quantity_raw; quantity dibuat NULL.
        raw = qty_raw.strip("()")
        quantity = int(raw) if raw.isdigit() else None

        con.execute("""
            INSERT INTO parts (
                machine_id, part_number, part_name,
                quantity, catalog_ref, note, quantity_raw, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            44, part_no, description,
            quantity, ref, note, qty_raw, MARKER
        ))

    con.commit()
    print("INSERT BERHASIL:", len(data), "baris")

except Exception:
    con.rollback()
    raise
finally:
    con.close()
