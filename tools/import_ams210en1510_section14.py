import sqlite3, shutil, argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("database")
MACHINE_ID = 15
DOCUMENT_ID = 136
TITLE = "14. X-Y COMPONENTS (2)"
SOURCE = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-30.jpg"
PAGE = 25

# REF, part number, description, quantity, marker
ROWS = [
(1,"401-03969","ENCODER MOTOR ASM.(IP)",1,"COMMON"),
(2,"401-03969","ENCODER MOTOR ASM.(IP)",1,"COMMON"),
(3,"400-78061","X_GUIDE_SHAFT_SUPPORT_B",1,"#01"),
(4,"400-78060","X_GUIDE_SHAFT_SUPPORT_A",1,"#02"),
(5,"SM-6061202-TP","SCREW M6 L=12",2,"COMMON"),
(6,"400-77985","X_DRIVEN_GEAR",1,"COMMON"),
(7,"B2526-210-D00","X DRIVE GEAR",1,"COMMON"),
(8,"WP-0430801-SC","WASHER 4.3X9X0.8",2,"COMMON"),
(9,"400-77984","Y_REMOVAL_BUSHING_A",1,"COMMON"),
(10,"400-78064","Y_FEED_SHAFT",1,"COMMON"),
(11,"CS-1000881-TP","THRUST COLLAR",1,"COMMON"),
(12,"400-36475","X_GUIDE_SHAFT",1,"#01"),
(13,"400-38564","X GUIDE SHAFT",1,"#02"),
(14,"400-78057","Y_REMOVAL_BUSHING_A",2,"COMMON"),
(15,"SM-8050512-TP","SCREW",2,"COMMON"),
(16,"400-78062","Y_REMOVAL_SHAFT_HOLDER",1,"COMMON"),
(17,"SM-6051802-TP","SCREW M5 L=18",1,"COMMON"),
(18,"WP-0550800-SP","WASHER 5.5X10X0.8",1,"COMMON"),
(19,"112-72408","THRUST COLLAR",2,"COMMON"),
(20,"SB-4080001-00","BEARING",2,"COMMON"),
(21,"SM-6041200-SP","SCREW M4 L=12",4,"COMMON"),
(22,"SB-3100013-00","BEARING",1,"COMMON"),
(23,"SM-8060812-TP","SCREW M6 L=8",2,"COMMON"),
(24,"SM-8060602-TP","SCREW M6X6",2,"COMMON"),
(25,"SM-8060612-TP","SCREW M6 L=6",2,"COMMON"),
(26,"SM-8050612-TP","SCREW M5X6",2,"COMMON"),
(27,"SB-3100012-00","BEARING",1,"COMMON"),
(28,"EA-9500B01-00","CABLE BAND",1,"COMMON"),
(29,"WP-0450846-SP","WASHER",8,"COMMON"),
(30,"169-92604","THRUST WASHER",4,"COMMON"),
(31,"400-25439","Y_FEED_MOTOR_BASE",1,"COMMON"),
(32,"SM-6041200-SP","SCREW M4 L=12",4,"COMMON"),
(33,"SM-6042000-SP","SCREW",2,"COMMON"),
(34,"WP-0450846-SP","WASHER",2,"COMMON"),
(35,"B2526-210-D00","X DRIVE GEAR",1,"COMMON"),
(36,"SM-8060602-TP","SCREW M6X6",2,"COMMON"),
(37,"400-77994","DRIVE SPROCKET",1,"COMMON"),
(38,"HD-0005700-0A","PHOTO SENSOR",1,"COMMON"),
(39,"SL-4031081-SC","SCREW M3X10",1,"COMMON"),
(40,"B4004-210-D00","X SENSOR INSTALLING PLATE",1,"COMMON"),
(41,"SM-6040802-TP","SCREW M4X0.7 L=8",2,"COMMON"),
(42,"SM-6040602-TP","SCREW M4 L=6",2,"COMMON"),
(43,"400-32505","Y_SENSOR_ASM.",1,"COMMON"),
(44,"SL-4031081-SC","SCREW M3X10",1,"COMMON"),
(45,"400-78058","Y_SENSOR_INSTALLING_PLATE_A",1,"COMMON"),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if len(ROWS) != 45 or [r[0] for r in ROWS] != list(range(1,46)):
        raise SystemExit("ERROR: daftar REF tidak lengkap/berurutan.")

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    try:
        existing = db.execute("""
            SELECT id FROM components
            WHERE machine_id=? AND component_name=?
        """, (MACHINE_ID,TITLE)).fetchall()
        if existing:
            raise SystemExit(f"STOP: komponen sudah ada: {[r['id'] for r in existing]}")

        plans, missing = [], []
        for ref,pn,desc,qty,marker in ROWS:
            candidates = db.execute("""
                SELECT id FROM parts
                WHERE machine_id=? AND catalog_ref=?
                  AND part_number=? AND quantity_raw=?
                  AND COALESCE(note,'COMMON')=?
                  AND notes LIKE '%section 14%'
                  AND source_document_id IS NULL
            """, (MACHINE_ID,ref,pn,str(qty),marker)).fetchall()

            if len(candidates) > 1:
                raise SystemExit(
                    f"STOP: staging ganda untuk REF{ref}: {[x['id'] for x in candidates]}"
                )
            if candidates:
                plans.append((ref,pn,candidates[0]["id"],"PAKAI STAGING"))
            else:
                plans.append((ref,pn,None,"BUAT PART BARU"))
                missing.append(ref)

        print("=== PREFLIGHT SECTION 14 ===")
        print("Judul:", TITLE)
        print("REF katalog:", len(ROWS))
        print("Staging cocok:", sum(x[2] is not None for x in plans))
        print("Part baru:", len(missing), missing)
        for ref,pn,pid,status in plans:
            print(f"REF{ref:02} | {pn:16} | {status}" +
                  (f" ID{pid}" if pid else ""))

        if not args.apply:
            print("\nDRY-RUN: database tidak diubah.")
            print("Jika hasil sudah benar, jalankan ulang dengan --apply.")
            return

        backup = BACKUP_DIR / (
            "garment-before-ams210en1510-section14-" +
            datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
        )
        shutil.copy2(DB,backup)
        print("\nBackup:",backup)

        cur = db.cursor()
        cur.execute("""
            INSERT INTO components
            (machine_id,component_name,location,function,notes,image_path,
             source_url,catalog_ref,diagram_page)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            MACHINE_ID,TITLE,"X-Y mechanism",
            "Mendukung gerakan X-Y pada mekanisme pengumpan",
            "JUKI AMS-210EN Parts List; Section 14",
            IMAGE,SOURCE,"14",PAGE
        ))
        component_id = cur.lastrowid

        for ref,pn,desc,qty,marker in ROWS:
            match = next(x for x in plans if x[0] == ref)
            part_id = match[2]
            if part_id is None:
                cur.execute("""
                    INSERT INTO parts
                    (machine_id,source_document_id,part_number,part_name,
                     quantity,catalog_ref,diagram_page,note,source_url,
                     notes,quantity_raw)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    MACHINE_ID,DOCUMENT_ID,pn,desc,qty,ref,PAGE,
                    marker,SOURCE,
                    "AMS-210EN Parts List; Section 14",str(qty)
                ))
                part_id = cur.lastrowid

            cur.execute("""
                INSERT INTO component_parts
                (component_id,part_id,relation_type,notes)
                VALUES (?,?,?,?)
            """, (
                component_id,part_id,
                "catalog_component_part",f"REF {ref}"
            ))

        db.commit()

        rels = db.execute("""
            SELECT COUNT(*) FROM component_parts WHERE component_id=?
        """,(component_id,)).fetchone()[0]
        print("\nAPPLY SELESAI")
        print("Component ID:",component_id)
        print("Relasi:",rels)
        if rels != 45:
            raise SystemExit("PERINGATAN: jumlah relasi tidak sama dengan 45.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
