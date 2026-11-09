import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
SECTION = "AMS-210EN catalog staging; section 16"

data = [
(1,"400-23636","FEED BRACKET",1,"COMMON"),
(2,"400-23643","LINK PLATE A",2,"COMMON"),
(3,"400-23640","LINK PLATE B",2,"COMMON"),
(4,"400-23644","CYLINDER KNUCKLE",2,"COMMON"),
(5,"B2567-210-D00","CYLINDER INSTALLING BASE",1,"COMMON"),
(6,"400-23641","CYLINDER SHAFT",1,"COMMON"),
(7,"400-23642","SLIDER BASE",1,"COMMON"),
(8,"400-23635","CYLINDER PIN",2,"COMMON"),
(9,"400-23663","SHAFT BLOCK SHAFT",1,"COMMON"),
(10,"G5126-172-000","CLAMP SHAFT HOLDER",1,"COMMON"),
(11,"BT-0400251-EB","URETHANE HOSE BLACK",4,"COMMON"),
(12,"CS-079073A-SH","THRUST COLLAR ASM.",2,"COMMON"),
(13,"PA-1602006-A0","AIR CYLINDER",2,"COMMON"),
(14,"PJ-0460525-03","HOSE ELBOW",4,"COMMON"),
(15,"RE-0300000-K0","E-RING 3",4,"COMMON"),
(16,"RE-0500000-K0","E-RING 5",2,"COMMON"),
(17,"SB-7100005-00","BEARING",1,"COMMON"),
(18,"SM-6051002-TP","SCREW M5X0.8 L=10",2,"COMMON"),
(19,"SM-6061002-TP","SCREW M6 L=10",2,"COMMON"),
(20,"SM-6061402-TN","BOLT",2,"COMMON"),
(21,"SM-8050812-TP","SCREW M5X8",1,"COMMON"),
(22,"SM-6450610-TP","SCREW",4,"COMMON"),
(23,"WP-0651001-SC","WASHER",2,"COMMON"),
(24,"WP-0651001-SC","WASHER",2,"COMMON"),
(25,"SM-6030802-TP","SCREW M3X0.5 L=8",1,"COMMON"),
(26,"400-39541","LOWER_PLATE",1,"#03"),
(27,"PC-0124050-00","UNION STRAIGHT SPEED CONTROLLER",4,"COMMON"),
(28,"SM-6041002-TP","SCREW M4 L=10",2,"COMMON"),
(29,"WS-0410002-KP","SPRING WASHER",2,"COMMON"),
(30,"400-71898","FEEDING_FRAME_2210",1,"#03"),
(31,"SM-1040870-TP","SCREW",4,"COMMON"),
(32,"400-86368","WORK_CLAMP_FOOT_PLATE_BASE",1,"COMMON"),
(33,"400-86370","WORK_CLAMP_FOOT_SLIDE_PLATE_ASM.",2,"COMMON"),
(34,"SM-6041002-TP","SCREW M4 L=10",2,"COMMON"),
(35,"400-52852","WORK_CLAMP_FOOT_PLATE_A_AMS.",1,"COMMON"),
(36,"WS-0410002-KP","SPRING WASHER",2,"COMMON"),
(37,"SM-1040801-SP","SCREW M4X0.7 L=8",2,"COMMON"),
(38,"400-52854","WORK_CLAMP_FOOT_PLATE_B_ASM.",2,"COMMON"),
(39,"SM-6041202-TP","SCREW M4X0.7 L=12",4,"COMMON"),
(40,"WP-0480856-SP","WASHER 4.8X8.4X0.8",4,"COMMON"),
(41,"NM-6040001-SP","NUT M4X0.7",4,"COMMON"),
(42,"SM-8030612-TP","SET SCREW",4,"COMMON"),
(43,"B2513-215-000","BEARING",4,"COMMON"),
(44,"WP-0450000-SD","WASHER 4.5X8X0.5",2,"COMMON"),
(45,"400-86378","RECEIVER_PLATE_LEFT_ASM",1,"#01"),
(46,"SM-6040800-SP","SCREW",2,"#01"),
(47,"WP-0480856-SP","WASHER 4.8X8.4X0.8",2,"#01"),
(48,"400-86376","RECEIVER_PLATE_RIGHT_ASM",1,"#01"),
(49,"SM-6041050-TP","SCREW",2,"COMMON"),
(50,"SM-6041050-TP","SCREW",2,"COMMON"),
(51,"400-23639","2-STEP FEEDING FRAME",2,"#01"),
(52,"400-86374","RECEIVER_PLATE_LEFT_ASM",1,"#04"),
(53,"SM-6050800-SP","SCREW M5 L=8",4,"#04"),
(54,"WP-0550800-SP","WASHER 5.5X10X0.8",4,"#04"),
(55,"NM-6050001-SD","NUT M5X0.8",2,"#04"),
(56,"SM-8050812-TP","SCREW M5X8",2,"#04"),
(57,"400-86372","RECEIVER_PLATE_RIGHT_ASM",1,"#04"),
(58,"400-71897","FEEDING_FRAME_1510",1,"#02"),
(59,"401-78093","LOWER PLATE",1,"#01"),
(60,"401-78092","LOWER_PLATE",1,"#02"),
(61,"HX-0023300-00","CLIP",6,"COMMON"),
]

con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys=ON")

try:
    existing = con.execute("""
        SELECT id, catalog_ref
        FROM parts
        WHERE machine_id=44 AND notes=?
    """, (SECTION,)).fetchall()

    refs = [int(r[1]) for r in existing]
    expected_existing = (
        set(range(1,22)) |
        {23,25,26,27,29,30,33} |
        set(range(36,49)) |
        {50,55}
    )

    if len(existing) != 43 or len(set(refs)) != 43:
        raise RuntimeError("Jumlah atau keunikan ref awal tidak sesuai.")
    if set(refs) != expected_existing:
        raise RuntimeError("Daftar ref awal berbeda dari audit.")

    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_dir / f"garment-before-repair-section16-{stamp}.db"
    shutil.copy2(DB, backup)
    print("BACKUP:", backup)

    con.execute("BEGIN IMMEDIATE")
    by_ref = {int(ref): row_id for row_id, ref in existing}

    for ref, pn, name, qty, note in data:
        if ref in by_ref:
            cur = con.execute("""
                UPDATE parts
                SET part_number=?, part_name=?, quantity=?,
                    quantity_raw=?, note=?
                WHERE id=? AND machine_id=44 AND notes=?
            """, (pn, name, qty, str(qty), note, by_ref[ref], SECTION))
            if cur.rowcount != 1:
                raise RuntimeError(f"Gagal update REF {ref}")
        else:
            con.execute("""
                INSERT INTO parts (
                    machine_id, part_number, part_name, quantity,
                    catalog_ref, note, notes, quantity_raw
                ) VALUES (44,?,?,?,?,?,?,?)
            """, (pn, name, qty, ref, note, SECTION, str(qty)))

    check = con.execute("""
        SELECT catalog_ref, part_number, part_name,
               quantity, quantity_raw, note
        FROM parts
        WHERE machine_id=44 AND notes=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (SECTION,)).fetchall()

    actual = [
        (int(r[0]), r[1], r[2], r[3], r[4], r[5])
        for r in check
    ]
    expected = [
        (ref, pn, name, qty, str(qty), note)
        for ref, pn, name, qty, note in data
    ]

    if len(check) != 61:
        raise RuntimeError(f"Jumlah hasil salah: {len(check)}")
    if [r[0] for r in actual] != list(range(1,62)):
        raise RuntimeError("Ref tidak lengkap atau duplikat.")
    if actual != expected:
        for a, e in zip(actual, expected):
            if a != e:
                print("AKTUAL:", a)
                print("TARGET:", e)
        raise RuntimeError("Isi data tidak cocok.")

    con.commit()
    print("HASIL: BERHASIL")
    print("TOTAL:", len(check))
    print("REF UNIK:", len(set(r[0] for r in actual)))
    print("RENTANG: 1–61")
    print("VERIFIKASI ISI: COCOK 61/61")

except Exception as e:
    con.rollback()
    print("TRANSAKSI DIBATALKAN:", e)
    raise
finally:
    con.close()
