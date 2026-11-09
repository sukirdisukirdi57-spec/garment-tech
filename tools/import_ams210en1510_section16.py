import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID, DOC, SECTION, PAGE = 15, 136, 16, 29
TITLE = "16. CLOTH FEED MECHANISM COMPONENTS (TYPE L)"
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-34.jpg"
URL = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"

# REF, part number, official description, qty, marker
ROWS = [
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not DB.is_file():
        raise SystemExit("Database tidak ditemukan.")
    if not Path("static", IMAGE).is_file():
        raise SystemExit("Gambar diagram tidak ditemukan.")

    refs = [r[0] for r in ROWS]
    if len(ROWS) != 61 or len(set(refs)) != 61:
        raise SystemExit("Daftar REF tidak valid.")

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    # Cegah duplikasi komponen berdasarkan judul resmi.
    old = db.execute("""
        SELECT id,component_name,catalog_ref,diagram_page
        FROM components
        WHERE machine_id=? AND component_name=?
    """, (MID, TITLE)).fetchall()
    if old:
        db.close()
        raise SystemExit(f"Komponen dengan judul ini sudah ada: {[dict(x) for x in old]}")

    print("=== PREFLIGHT SECTION 16 ===")
    print("Judul:", TITLE)
    print("REF katalog:", len(ROWS))

    reuse = {}
    new = []
    errors = []

    for ref, pn, name, qty, marker in ROWS:
        candidates = db.execute("""
            SELECT id,part_number,quantity_raw,note,catalog_ref
            FROM parts
            WHERE machine_id=?
              AND notes LIKE ?
              AND CAST(catalog_ref AS INTEGER)=?
              AND part_number=?
              AND CAST(quantity_raw AS INTEGER)=?
              AND COALESCE(note,'')=?
            ORDER BY id
        """, (MID,"%section 16%",ref,pn,qty,marker)).fetchall()

        if len(candidates) > 1:
            errors.append(f"REF{ref}: staging ganda {[x['id'] for x in candidates]}")
        elif len(candidates) == 1:
            p = candidates[0]
            rel = db.execute(
                "SELECT COUNT(*) FROM component_parts WHERE part_id=?",
                (p["id"],)
            ).fetchone()[0]
            if rel:
                errors.append(f"REF{ref}: ID{p['id']} sudah memiliki {rel} relasi")
            else:
                reuse[ref] = p["id"]
                print(f"PAKAI ID{p['id']} | REF{ref} | {pn} | Qty {qty} | {marker}")
        else:
            new.append((ref,pn,name,qty,marker))
            print(f"BARU | REF{ref} | {pn} | Qty {qty} | {marker}")

    print("\nStaging cocok:", len(reuse))
    print("Part baru:", len(new))

    if errors:
        for e in errors:
            print("ERROR:", e)
        db.close()
        raise SystemExit("Preflight gagal; database tidak diubah.")

    if len(reuse) + len(new) != 61:
        db.close()
        raise SystemExit("Mapping REF tidak lengkap.")

    print("\nKomponen lama ID446 tidak disentuh.")
    print("Diagram page:", PAGE)
    print("Gambar:", IMAGE)

    if not args.apply:
        print("\nDRY-RUN: belum ada perubahan database.")
        db.close()
        return

    backup = Path(
        "database/garment-before-ams210en1510-section16-"
        + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
    )
    bdb = sqlite3.connect(backup)
    db.backup(bdb)
    bdb.close()
    print("Backup:", backup)

    try:
        db.execute("BEGIN IMMEDIATE")
        cur = db.execute("""
            INSERT INTO components
            (machine_id,component_name,part_number,location,function,
             notes,image_path,source_url,catalog_ref,diagram_page)
            VALUES (?,?,NULL,?,?,?,?,?,?,?)
        """, (
            MID,TITLE,
            "Mekanisme cloth feed tipe L",
            "Menggerakkan mekanisme cloth feed tipe L.",
            "Diimpor dari Parts List resmi JUKI AMS-210EN-1510.",
            IMAGE,URL,str(SECTION),PAGE
        ))
        component_id = cur.lastrowid

        for ref,pn,name,qty,marker in ROWS:
            if ref in reuse:
                part_id = reuse[ref]
            else:
                cur = db.execute("""
                    INSERT INTO parts
                    (machine_id,source_document_id,part_number,part_name,
                     quantity,catalog_ref,diagram_page,note,source_url,
                     notes,quantity_raw)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    MID,DOC,pn,name,qty,ref,PAGE,marker,URL,
                    "AMS-210EN-1510 section 16 staging",str(qty)
                ))
                part_id = cur.lastrowid

            db.execute("""
                INSERT INTO component_parts
                (component_id,part_id,relation_type,notes)
                VALUES (?,?,'catalog_component_part',?)
            """, (component_id,part_id,f"REF {ref}"))

        db.commit()
        print("\nAPPLY BERHASIL")
        print("Component ID:", component_id)
        print("Relasi dibuat:", len(ROWS))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
