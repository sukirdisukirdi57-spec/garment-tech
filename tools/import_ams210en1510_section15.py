import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINE_ID = 15
DOCUMENT_ID = 136
SECTION = 15
TITLE = "15. CLOTH FEED MECHANISM COMPONENTS (TYPE S)"
PAGE = 27
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-32.jpg"
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

# REF, part number, official part name, quantity, marker
ROWS = [
    (1, "400-23636", "FEED BRACKET", 1, "COMMON"),
    (2, "400-23645", "LIFTING LEVER RIGHT", 1, "COMMON"),
    (3, "400-23646", "LIFTING LEVER LEFT", 1, "COMMON"),
    (4, "400-23652", "FEED BRACKET UPPER LINK RIGHT", 1, "COMMON"),
    (5, "400-23653", "FEED BRACKET UPPER LINK LEFT", 1, "COMMON"),
    (6, "400-23649", "SUPPORT LINK RIGHT", 1, "COMMON"),
    (7, "400-23650", "SUPPORT LINK LEFT", 1, "COMMON"),
    (8, "B2579-210-D00-A", "SLIDER", 1, "COMMON"),
    (9, "400-23648", "SLIDER SHAFT", 1, "COMMON"),
    (10, "400-23638", "FEEDING FRAME", 1, "#01"),
    (11, "400-71897", "FEEDING_FRAME_1510", 1, "#02"),
    (12, "401-78093", "LOWER PLATE", 1, "#01"),
    (13, "401-78092", "LOWER PLATE", 1, "#02"),
    (14, "B2583-210-D00", "SPRING", 2, "COMMON"),
    (15, "B2581-210-D00", "SPRING RIGHT", 1, "COMMON"),
    (16, "B2582-210-D00", "SPRING LEFT", 1, "COMMON"),
    (17, "400-23651", "FEED BRACKET LINK", 1, "COMMON"),
    (18, "400-23654", "LINK STOPPER", 2, "COMMON"),
    (19, "B1626-555-000", "FEED REGULATOR CONNECTING ROD PIN", 2, "COMMON"),
    (20, "400-23663", "SHAFT BLOCK SHAFT", 1, "COMMON"),
    (21, "400-23635", "CYLINDER PIN", 2, "COMMON"),
    (22, "CS-079073A-SH", "THRUST COLLAR ASM.", 1, "COMMON"),
    (23, "RE-0300000-K0", "E-RING 3", 4, "COMMON"),
    (24, "RE-0300000-K0", "E-RING 3", 2, "COMMON"),
    (25, "RE-0700000-K0", "E-RING 7", 1, "COMMON"),
    (26, "SB-7100005-00", "BEARING", 1, "COMMON"),
    (27, "SM-6030802-TP", "SCREW M3X0.5 L=8", 1, "COMMON"),
    (28, "WS-0410002-KP", "SPRING WASHER", 2, "COMMON"),
    (29, "SM-6061002-TP", "SCREW M6 L=10", 2, "COMMON"),
    (30, "WP-0651001-SC", "WASHER", 2, "COMMON"),
    (31, "SM-6061402-TN", "BOLT", 2, "COMMON"),
    (32, "WP-0651001-SC", "WASHER", 2, "COMMON"),
    (33, "SM-8050412-TP", "SCREW M5 L=4", 2, "COMMON"),
    (34, "SM-6040800-SP", "SCREW", 2, "#01"),
    (35, "WP-0480856-SP", "WASHER 4.8X8.4X0.8", 2, "#01"),
    (36, "SM-6450610-TP", "SCREW", 4, "COMMON"),
    (37, "B2557-280-00C", "WASHER", 1, "COMMON"),
    (38, "400-86368", "WORK_CLAMP_FOOT_PLATE_BASE", 1, "COMMON"),
    (39, "SM-1040870-TP", "SCREW", 4, "COMMON"),
    (40, "SM-6041002-TP", "SCREW M4 L=10", 2, "COMMON"),
    (41, "400-86370", "WORK_CLAMP_FOOT_SLIDE_PLATE_ASM.", 2, "COMMON"),
    (42, "B2513-215-000", "BEARING", 4, "COMMON"),
    (43, "400-52852", "WORK_CLAMP_FOOT_PLATE_A_ASM.", 1, "COMMON"),
    (44, "SM-1040801-SP", "SCREW M4X0.7 L=8", 2, "COMMON"),
    (45, "400-52854", "WORK_CLAMP_FOOT_PLATE_B_ASM.", 2, "COMMON"),
    (46, "SM-6041202-TP", "SCREW M4X0.7 L=12", 4, "COMMON"),
    (47, "WP-0480856-SP", "WASHER 4.8X8.4X0.8", 4, "COMMON"),
    (48, "NM-6040001-SP", "NUT M4X0.7", 4, "COMMON"),
    (49, "400-86376", "RECEIVER_PLATE_RIGHT_ASM", 1, "#01"),
    (50, "SM-6041050-TP", "SCREW", 2, "COMMON"),
    (51, "400-86378", "RECEIVER_PLATE_LEFT_ASM", 1, "#01"),
    (52, "SM-6041050-TP", "SCREW", 2, "COMMON"),
    (53, "400-86372", "RECEIVER_PLATE_RIGHT_ASM", 1, "#02"),
    (54, "400-86374", "RECEIVER_PLATE_LEFT_ASM", 1, "#02"),
    (55, "SM-8030612-TP", "SET SCREW", 4, "COMMON"),
    (56, "SM-6050800-SP", "SCREW M5 L=8", 4, "#02"),
    (57, "WP-0550800-SP", "WASHER 5.5X10X0.8", 4, "#02"),
    (58, "SM-8050812-TP", "SCREW M5X8", 2, "#02"),
    (59, "NM-6050001-SD", "NUT M5X0.8", 2, "#02"),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file():
        raise SystemExit(f"Database tidak ditemukan: {DB}")
    if not Path("static/" + IMAGE).is_file():
        raise SystemExit(f"Gambar tidak ditemukan: static/{IMAGE}")

    refs = [r[0] for r in ROWS]
    if len(refs) != 59 or len(set(refs)) != 59:
        raise SystemExit("ERROR: daftar REF tidak lengkap atau duplikat.")

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")

    existing = db.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND component_name=?
    """, (MACHINE_ID, TITLE)).fetchall()

    if existing:
        raise SystemExit(
            "Komponen Section 15 sudah ada: " +
            str([dict(x) for x in existing]) +
            ". Hentikan agar tidak membuat duplikat."
        )

    print("=== PREFLIGHT SECTION 15 ===")
    print("Judul:", TITLE)
    print("REF katalog:", len(ROWS))

    chosen = {}
    new_rows = []
    errors = []

    for ref, pn, name, qty, marker in ROWS:
        candidates = db.execute("""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note, notes
            FROM parts
            WHERE machine_id=?
              AND notes LIKE ?
              AND CAST(catalog_ref AS INTEGER)=?
              AND part_number=?
              AND CAST(quantity_raw AS INTEGER)=?
              AND COALESCE(note,'')=?
            ORDER BY id
        """, (
            MACHINE_ID, "%section 15%", ref, pn, qty, marker
        )).fetchall()

        if len(candidates) > 1:
            errors.append(
                f"REF{ref}: kandidat staging ganda " +
                str([x["id"] for x in candidates])
            )
        elif len(candidates) == 1:
            p = candidates[0]
            rel = db.execute("""
                SELECT COUNT(*) FROM component_parts WHERE part_id=?
            """, (p["id"],)).fetchone()[0]
            if rel:
                errors.append(
                    f"REF{ref}: staging ID{p['id']} sudah punya {rel} relasi"
                )
            else:
                chosen[ref] = p["id"]
                print(
                    f"PAKAI ID{p['id']} | REF{ref} | {pn} "
                    f"| Qty {qty} | {marker}"
                )
        else:
            new_rows.append((ref, pn, name, qty, marker))
            print(
                f"BARU      | REF{ref} | {pn} "
                f"| Qty {qty} | {marker}"
            )

    print("\nStaging cocok:", len(chosen))
    print("Part baru:", len(new_rows))

    if errors:
        print("\n=== ERROR PREFLIGHT ===")
        for e in errors:
            print("-", e)
        db.close()
        raise SystemExit("Preflight gagal. Database tidak diubah.")

    if len(chosen) + len(new_rows) != 59:
        db.close()
        raise SystemExit("Jumlah mapping bukan 59. Database tidak diubah.")

    print("\nKomponen baru:", TITLE)
    print("Diagram page:", PAGE)
    print("Gambar:", IMAGE)

    if not args.apply:
        print("\nDRY-RUN: belum ada perubahan database.")
        print("Jika hasil preflight benar, jalankan dengan --apply.")
        db.close()
        return

    backup = Path(
        "database/garment-before-ams210en1510-section15-"
        + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    bdb = sqlite3.connect(backup)
    db.backup(bdb)
    bdb.close()
    print("\nBackup:", backup)

    try:
        db.execute("BEGIN IMMEDIATE")

        cur = db.execute("""
            INSERT INTO components
            (machine_id, component_name, part_number, location, function,
             notes, image_path, source_url, catalog_ref, diagram_page)
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID, TITLE,
            "Cloth feed mechanism, Type S",
            "Menggerakkan mekanisme cloth feed tipe S.",
            "Diimpor dari Parts List resmi JUKI AMS-210EN-1510.",
            IMAGE, SOURCE_URL, str(SECTION), PAGE
        ))
        component_id = cur.lastrowid

        for ref, pn, name, qty, marker in ROWS:
            if ref in chosen:
                part_id = chosen[ref]
            else:
                cur = db.execute("""
                    INSERT INTO parts
                    (machine_id, source_document_id, part_number, part_name,
                     quantity, catalog_ref, diagram_page, note, source_url,
                     notes, quantity_raw)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID, DOCUMENT_ID, pn, name, qty, ref, PAGE,
                    marker, SOURCE_URL,
                    "AMS-210EN-1510 section 15 staging",
                    str(qty)
                ))
                part_id = cur.lastrowid

            db.execute("""
                INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
                VALUES (?, ?, 'catalog_component_part', ?)
            """, (component_id, part_id, f"REF {ref}"))

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
