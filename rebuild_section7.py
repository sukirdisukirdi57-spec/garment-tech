import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MARKER = "AMS-210EN catalog staging; section 7"
MACHINE_ID = 44

# REF, NOTE, PART NUMBER, DESCRIPTION, QUANTITY
data = [
(1,"#07","400-77923","ARM_A",2),
(2,"#07","SM-8060612-TP","SCREW M6 L=6",4),
(3,"#07","400-77924","CONNECTING_LINK",1),
(4,"#07","SD-0800346-TP","SHOULDER SCREW",1),
(5,"#04","HX-0015000-0D","CABLE CLIP",1),
(6,"#07","400-77928","PRESSER SHAFT",1),
(7,"#07","400-77929","PIN",1),
(8,"#08","B1520-210-D00-A","PRESSER PLATE SHEET",1),
(9,"#02","400-36471","PRESSURE_PLATE_SEET",1),
(10,"#09","400-39538","PRESSURE_PLATE_SHEET",1),
(11,"#06","400-77927","PRESSURE_PLATE",1),
(12,"#08","B1531-210-D00","PRESSER PLATE FITTING SHEET",1),
(13,"#02","400-36472","PRESSURE_PLATE_FITTING_SEET",1),
(14,"#09","400-39539","PRESSURE PLATE FITTING SHEET",1),
(15,"#07","400-77930","PRESSURE_SHAFT_METAL",1),
(16,"#07","B1516-210-D00","SCREW",1),
(17,"#01","400-77936","PRESSURE_PLATE",1),
(18,"#02","400-36470","PRESSURE_PLATE",1),
(19,"#05","400-77935","PRESSURE_PLATE",1),
(20,"#03","400-39537","PRESSURE_PLATE",1),
(21,"#04","SM-6051002-TP","SCREW M5X0.8 L=10",4),
(22,"COMMON","401-03968","ENCODER MOTOR ASM.(TC)",1),
(23,"COMMON","400-72211","MOTOR_BASE",1),
(24,"COMMON","SM-6061802-TP","SCREW M6 L=18",3),
(25,"COMMON","B1816-215-P00","GUIDE PIN",2),
(26,"#07","400-25009","PRESSER_LOWER_LINK_A",1),
(27,"#07","400-24996","PRESSER_LOWER_ADJUSTING_LINK",1),
(28,"#07","SM-6061202-TP","SCREW M6 L=12",1),
(29,"#07","WP-0611626-SP","WASHER 15X6X1.6",1),
(30,"#07","400-77931","PRESSURE_LOWERING_SHAFT",1),
(31,"#07","400-10464","THRUST_COLLAR_ASM.",1),
(32,"#07","SM-8060812-TP","SCREW M6 L=8",2),
(33,"#07","400-25436","LOWER_SPRING_HOOK",1),
(34,"#07","SM-6040802-TP","SCREW M4X0.7 L=8",1),
(35,"#07","262-26209","SPRING",1),
(36,"#07","400-23627","PRESSER PLATE SHEET WASHER",3),
(37,"#07","400-34922","PRESSER LINK SHAFT",1),
(38,"#07","229-31505","RUBBER WASHER",1),
(39,"#07","NM-6050001-SP","NUT M5",2),
(40,"#07","SD-0800327-TP","SHOULDER SCREW",1),
(41,"COMMON","HD-0005700-0A","PHOTO SENSOR",1),
(42,"COMMON","SL-4031291-SC","SCREW M3X12",1),
(43,"COMMON","400-10443","SENSOR_INSTALLING_BASE",1),
(44,"COMMON","SM-6040802-TP","SCREW M4X0.7 L=8",1),
(45,"COMMON","400-06666","SENSOR_SLIT_ASM.",1),
(46,"COMMON","SM-8050592-TP","SCREW",2),
(47,"COMMON","SB-1100024-00","BEARING",1),
(48,"COMMON","SM-6040650-TP","SCREW",1),
(49,"COMMON","SM-4051655-SP","SCREW M5 L=16",4),
(50,"COMMON","WP-0651001-SC","WASHER",3),
(51,"#07","400-24992","MANUAL_LOWER_PLATE",1),
(52,"#07","400-24993","MANUAL_LOWER_LEVER",1),
(53,"#07","400-24994","MANUAL_LOWER_LINK",1),
(54,"#07","SD-0800337-TP","SHOULDER SCREW",2),
(55,"#07","SD-1000406-TP","SHOULDER SCREW",1),
(56,"#07","262-28809","SLIDE ROLLER",1),
(57,"#07","400-24995","SPRING_HOOK",1),
(58,"#07","SM-4061255-SP","SCREW M6 L=12",1),
(59,"#07","137-47001","BELL CRANK SHAFT",1),
(60,"#07","SM-8060812-TP","SCREW M6 L=8",1),
(61,"#07","SD-0801506-TP","SHOULDER SCREW D8 H15",1),
(62,"#07","B1642-210-D00","INTERMEDIATE PRESSER SPRING B",1),
(63,"#07","E3051-802-000","MINIATURE CAM FOLLOW",1),
(64,"#07","B1527-581-000-A","THREAD RELEASE PIN",1),
(65,"#07","SB-7160002-00","BEARING",1),
(66,"#07","B1515-210-D00","PIN",2),
(67,"#04","SL-4040891-SC","SCREW M4 L=8",1),
(68,"#07","SM-8050412-TP","SCREW M5 L=4",1),
(69,"#07","SM-8050412-TP","SCREW M5 L=4",1),
(70,"#07","SM-6061602-TP","SCREW M6 L=16",1),
(71,"#07","EA-9500B01-00","CABLE BAND",1),
(72,"#06","400-78577","PRESSURE_PLATE_SEET_1510S",1),
(73,"#06","400-78578","PRESSURE_PLATE_FITTING_SEET_15",1),
]

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

if len(data) != 73 or [r[0] for r in data] != list(range(1, 74)):
    raise SystemExit("DATA SUMBER TIDAK VALID: REF harus 1 sampai 73.")

# Backup sebelum koneksi tulis
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)
backup = backup_dir / f"garment-before-rebuild-section7-{stamp}.db"
shutil.copy2(DB, backup)

print("Backup dibuat:", backup)

con = sqlite3.connect(DB)
try:
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("BEGIN IMMEDIATE")

    count = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id=? AND notes=?
    """, (MACHINE_ID, MARKER)).fetchone()[0]

    if count != 24:
        raise RuntimeError(
            f"Jumlah awal berubah: ditemukan {count}, seharusnya 24. "
            "Transaksi dibatalkan."
        )

    # Hapus hanya staging Section 7 machine 44
    con.execute("""
        DELETE FROM parts
        WHERE machine_id=? AND notes=?
    """, (MACHINE_ID, MARKER))

    # Masukkan ulang dari katalog
    con.executemany("""
        INSERT INTO parts (
            machine_id, source_document_id, part_number, part_name,
            quantity, catalog_ref, diagram_page, note,
            source_url, notes, quantity_raw
        )
        VALUES (?, NULL, ?, ?, ?, ?, NULL, ?, NULL, ?, ?)
    """, [
        (
            MACHINE_ID,
            part_number,
            part_name,
            quantity,
            ref,
            note,
            MARKER,
            str(quantity)
        )
        for ref, note, part_number, part_name, quantity in data
    ])

    rows = con.execute("""
        SELECT catalog_ref, part_number, part_name, quantity, note, quantity_raw
        FROM parts
        WHERE machine_id=? AND notes=?
        ORDER BY catalog_ref
    """, (MACHINE_ID, MARKER)).fetchall()

    refs = [r[0] for r in rows]
    if len(rows) != 73 or refs != list(range(1, 74)):
        raise RuntimeError("Validasi REF gagal. Transaksi dibatalkan.")

    if len(set(refs)) != 73:
        raise RuntimeError("REF duplikat terdeteksi. Transaksi dibatalkan.")

    con.commit()

    print("\n=== KOREKSI BERHASIL ===")
    print("Jumlah baris:", len(rows))
    print("REF lengkap:", refs[0], "sampai", refs[-1])
    print("Jumlah REF unik:", len(set(refs)))
    print("Backup:", backup)

except Exception:
    con.rollback()
    print("\nKOREKSI DIBATALKAN. Database tidak diubah.")
    raise
finally:
    con.close()
