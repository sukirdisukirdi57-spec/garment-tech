import sqlite3, shutil, sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
DOC = 136
URL = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-23.jpg"
TITLE = "10. TENSION RELEASE & THREAD TENSION COMPONENTS"

# REF, part number, official description, quantity_raw, catalog marker
DATA = [
(1,"400-73660","AT SOLENOID","1","COMMON"),
(2,"SM-6040602-TP","SCREW M4 L=6","4","COMMON"),
(3,"RE-0900000-K0","E-RING 9","1","COMMON"),
(4,"400-06625","SPRING","1","COMMON"),
(5,"400-06617","AT_SOL_PIN","1","COMMON"),
(6,"400-10477","AT_SOL_COLLAR","1","COMMON"),
(7,"SM-8030412-TP","SCREW","2","COMMON"),
(8,"400-10479","AT_PLATE","1","COMMON"),
(9,"SM-6040802-TN","SCREW","2","COMMON"),
(10,"WP-0430801-SC","WASHER 4.3X9X0.8","2","COMMON"),
(11,"400-24070","AT_DRIVE_LINK(F)_ASM.","1","COMMON"),
(12,"400-23993","AT_PIVOT_BASE(F)","1","COMMON"),
(13,"SM-6040860-TP","SCREW M4 L=8","2","COMMON"),
(14,"400-32345","AT_DRIVE_LINK_R_ASM","1","COMMON"),
(15,"400-77932","AT_PIVOT_BASE (R)","1","COMMON"),
(16,"SM-6040602-TP","SCREW M4 L=6","2","COMMON"),
(17,"400-10487","AT_PIVOT_SCREW","2","COMMON"),
(18,"NM-6040003-SC","NUT M4","2","COMMON"),
(19,"400-10489","AT_PIVOT_SCREW_WASHER","4","COMMON"),
(20,"400-10490","AT_PIVOT_BEARING","2","COMMON"),
(21,"400-10497","AT_JOINT","2","COMMON"),
(22,"400-10498","AT_JOINT_BEARING","2","COMMON"),
(23,"400-10489","AT_PIVOT_SCREW_WASHER","2","COMMON"),
(24,"400-10499","AT_JOINT_NUT","2","COMMON"),
(25,"400-06622","AT_SNAP_PIN","2","COMMON"),
(26,"400-23997","AT_CONNECTION_BAR","1","COMMON"),
(27,"400-10503","THREAD_TENSION_1_ASM.","1","COMMON"),
(28,"229-28808","NUT","(1)","COMMON"),
(29,"229-21506","THREAD TENSION DISK","(2)","COMMON"),
(30,"400-10504","THREAD_TENSION_SHAFT","(1)","COMMON"),
(31,"262-18602","FIRST THREAD TENSION SPRING","(1)","COMMON"),
(32,"400-29411","THREAD_TENSION_2_ASM._H","1","#02"),
(33,"400-10508","THREAD_TENSION_2_ASM.","1","#01"),
(34,"400-10509","TENSION RELEASE PIN","(1)","COMMON"),
(35,"400-10510","THREAD_TENSION_POST_BASE","(1)","COMMON"),
(36,"400-10511","DISK_STOPPER_HOLDER_CAP","(1)","COMMON"),
(37,"400-10512","THREAD_TENSION_SHAFT_COLLAR","(1)","COMMON"),
(38,"400-10513","DISK_STOPPER_SPRING","(3)","COMMON"),
(39,"400-10514","DISK_STOPPER","(1)","COMMON"),
(40,"400-10515","ASSY_THREAD_TENSION_POST","(1)","COMMON"),
(41,"400-11359","POST_BASE_SCREW","(1)","COMMON"),
(42,"400-29412","THREAD_TAKE-UP_SPRING_H","(1)","☆ #02"),
(43,"400-10521","HOLD_CAP_SCREW","(3)","COMMON"),
(44,"400-10522","SHAFT_NUT","(1)","COMMON"),
(45,"400-10523","POST_BASE_C_RING","(1)","COMMON"),
(46,"229-21605","THREAD TAKE-UP SPRING","(1)","☆ #01"),
(47,"SM-8061612-TP","SCREW M6X16","1","COMMON"),
(48,"400-13967","AT FELT","1","COMMON"),
]

NEW_REFS = {16,23,33,42,46,47,48}
BAD_IDS = tuple(range(6883,6894))

def stop(msg):
    raise SystemExit("STOP: " + msg)

if not DB.exists():
    stop("database tidak ditemukan")
if not (Path("static") / IMAGE).is_file():
    stop("gambar katalog tidak ditemukan: " + str(Path("static") / IMAGE))

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    # Validasi dokumen dan komponen lama
    doc = con.execute(
        "SELECT source_url FROM documents WHERE id=? AND machine_id=15",
        (DOC,)
    ).fetchone()
    if not doc:
        stop("dokumen 136 untuk mesin 15 tidak ditemukan")

    for cid, expected in ((449,40),(450,5),(451,12)):
        row = con.execute(
            "SELECT COUNT(*) n FROM component_parts WHERE component_id=?",
            (cid,)
        ).fetchone()
        if row["n"] != expected:
            stop(f"jumlah relasi komponen {cid} berubah: {row['n']}")

    old_main = con.execute("""
        SELECT id FROM components
        WHERE machine_id=15 AND component_name=?
    """, (TITLE,)).fetchone()
    if old_main:
        stop(f"komponen utama sudah ada: ID {old_main['id']}")

    # Baris 6883-6893 harus tetap terhubung hanya ke komponen 449
    for pid in BAD_IDS:
        links = con.execute("""
            SELECT component_id FROM component_parts WHERE part_id=?
        """, (pid,)).fetchall()
        if len(links) != 1 or links[0]["component_id"] != 449:
            stop(f"relasi baris lama ID {pid} tidak sesuai")

    # Pemetaan part yang sudah ada untuk REF lama
    part_ids = {}
    for ref,pn,name,qty,note in DATA:
        if ref in NEW_REFS:
            continue

        if ref <= 31:
            rows = con.execute("""
                SELECT id FROM parts
                WHERE machine_id=15
                  AND notes='AMS-210EN catalog staging; section 10'
                  AND CAST(catalog_ref AS INTEGER)=?
                  AND part_number=?
            """, (ref,pn)).fetchall()
        else:
            cid = 451
            rows = con.execute("""
                SELECT p.id FROM component_parts cp
                JOIN parts p ON p.id=cp.part_id
                WHERE cp.component_id=? AND p.part_number=?
            """, (cid,pn)).fetchall()

        if len(rows) != 1:
            stop(f"REF {ref}: part lama tidak unik/ tidak ditemukan ({pn})")
        part_ids[ref] = rows[0]["id"]

    # Pastikan REF staging lama yang benar berjumlah 29
    if len(part_ids) != 41:
        stop(f"pemetaan part lama tidak lengkap: {len(part_ids)}")

    print("PREFLIGHT OK")
    print("Katalog: 48 REF")
    print("Part lama terpetakan: 41")
    print("Part baru yang akan dibuat: 7")
    print("Baris salah label yang akan dipindah ke Section 9: 11")
    print("Relasi lama ID450/451: dipertahankan (5 dan 12)")
    print("Komponen utama Section 10: belum ada")
    print("Backup dan perubahan belum dilakukan.")

    if "--apply" not in sys.argv:
        print("\nJalankan dengan --apply jika hasil preflight sesuai.")
        raise SystemExit(0)

    backup = DB.with_name(
        "garment-before-ams210en1510-section10-" +
        datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
    )
    shutil.copy2(DB, backup)
    print("BACKUP:", backup)

    try:
        con.execute("BEGIN IMMEDIATE")

        # Kembalikan label dan metadata 11 baris Section 9
        con.executemany("""
            UPDATE parts
            SET notes='AMS-210EN catalog staging; section 9',
                source_document_id=136, diagram_page=17, source_url=?
            WHERE id=?
        """, [(URL,pid) for pid in BAD_IDS])

        # Buat komponen utama Section 10
        cur = con.execute("""
            INSERT INTO components
            (machine_id,component_name,part_number,location,function,
             notes,image_path,source_url,catalog_ref,diagram_page)
            VALUES (15,?,NULL,?,?,?,?,?,10,18)
        """, (
            TITLE,
            "Mekanisme pelepas tegangan dan pengatur tegangan benang",
            "Mengatur pelepasan dan tegangan benang",
            "Komponen utama Section 10",
            IMAGE, URL
        ))
        main_id = cur.lastrowid

        # Buat tujuh baris REF yang belum ada
        for ref,pn,name,qty,note in DATA:
            if ref not in NEW_REFS:
                continue
            quantity = int(qty.strip("()"))
            cur = con.execute("""
                INSERT INTO parts
                (machine_id,source_document_id,part_number,part_name,
                 quantity,catalog_ref,diagram_page,note,source_url,
                 notes,quantity_raw)
                VALUES (15,136,?,?,?,?,18,?,?,?,?)
            """, (
                pn,name,quantity,ref,note,URL,
                "AMS-210EN catalog staging; section 10",qty
            ))
            part_ids[ref] = cur.lastrowid

        # Lengkapi data dan metadata seluruh 48 part
        for ref,pn,name,qty,note in DATA:
            pid = part_ids[ref]
            quantity = int(qty.strip("()"))
            con.execute("""
                UPDATE parts SET
                    source_document_id=136,part_number=?,part_name=?,
                    quantity=?,catalog_ref=?,diagram_page=18,note=?,
                    source_url=?,notes='AMS-210EN catalog staging; section 10',
                    quantity_raw=?
                WHERE id=? AND machine_id=15
            """, (pn,name,quantity,ref,note,URL,qty,pid))

            con.execute("""
                INSERT INTO component_parts
                (component_id,part_id,relation_type,notes)
                VALUES (?,?, 'catalog_component_part',?)
            """, (main_id,pid,f"REF {ref}"))

        con.commit()

    except Exception:
        con.rollback()
        raise

    print("\nAPPLY BERHASIL")
    print("Komponen utama ID:",main_id)
    print("Relasi utama:",con.execute(
        "SELECT COUNT(*) FROM component_parts WHERE component_id=?",
        (main_id,)
    ).fetchone()[0])
    print("Relasi ID450/451:",[
        con.execute(
            "SELECT COUNT(*) FROM component_parts WHERE component_id=?",
            (cid,)
        ).fetchone()[0] for cid in (450,451)
    ])
    print("Baris baru:",{r:part_ids[r] for r in sorted(NEW_REFS)})
    print("Backup:",backup)

finally:
    con.close()
