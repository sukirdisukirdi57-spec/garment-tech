import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MID, DOC, SECTION, PAGE = 15, 136, 17, 31
TITLE = "17. TABLE COMPONENTS"
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-36.jpg"
URL = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"

# REF, part number, official description, quantity, quantity_raw, marker
ROWS = [
    (1,"141-91951","T-STAND COMPL.",1,"1","#01"),
    (2,"400-38255","T-STAND COMPL.(AIR TYPE)",1,"1","#03"),
    (3,"B8101-210-AAB","UPPER STAND COMPL.",1,"(1)","COMMON"),
    (4,"141-18152","UPPER STAND ASM. RIGHT",1,"(1)","COMMON"),
    (5,"111-58409","STAND SIDE SUPPORT",1,"1","COMMON"),
    (6,"111-58607","RUBBER CAP",4,"4","COMMON"),
    (7,"B8105-210-AAA","STAND COMPL.",1,"(1)","COMMON"),
    (8,"141-18251","STAND ASM. RIGHT",1,"(1)","COMMON"),
    (9,"170-07402","NUT",2,"2","COMMON"),
    (10,"111-58516","UPPER STAND PLATE",2,"2","COMMON"),
    (11,"SL-9082091-SE","WASHER HEXAGONAL BOLT",10,"(10)","#01"),
    (12,"SL-9082091-SE","WASHER HEXAGONAL BOLT",12,"(12)","#03"),
    (13,"138-17754","Z-STAND PEDAL COMPL.",1,"(1)","#01"),
    (14,"WP-0871602-SE","WASHER 8.7X18X1.6",4,"(4)","#01"),
    (15,"WS-0861410-KR","SPRING WASHER 8.6X15X1.4",2,"(2)","#01"),
    (16,"NM-6080721-SE","NUT M8",2,"(2)","#01"),
    (17,"111-59001","PEDAL SHAFT BRACKET",2,"(2)","#01"),
    (18,"B8153-771-000","PEDAL CONNECTING ROD",1,"(1)","#01"),
    (19,"D8113-555-B00","PEDAL BUSHING",2,"(2)","#01"),
    (20,"GPF-06080000","PEDAL ADJUSTING PLATE",1,"(1)","#01"),
    (21,"GPF-060600A0","PEDAL COMPL.",1,"(1)","#01"),
    (22,"SM-9061203-SE","SCREW M6 L=12",2,"(2)","#01"),
    (23,"WP-0671016-SE","WASHER 6.7X13X1",2,"(2)","#01"),
    (24,"WS-0621210-KR","SPRING WASHER 6.2X11.4X1.2",2,"(2)","#01"),
    (25,"SM-9082023-SE","SCREW M8 L=20",2,"(2)","#01"),
    (26,"WP-0871602-SE","WASHER 8.7X18X1.6",2,"(2)","#01"),
    (27,"111-59506","STRUT AUXILIARY PLATE",2,"(2)","#01"),
    (28,"WS-0861410-KR","SPRING WASHER 8.6X15X1.4",2,"(2)","#01"),
    (29,"B8150-210-000","CASTER",4,"4","COMMON"),
    (30,"NM-6120003-SE","NUT M12",4,"4","COMMON"),
    (31,"SM-9086523-SE","HEXAGONAL BOLT",2,"(2)","#01"),
    (32,"111-58300","STAND SIDE SUPPORT",1,"1","COMMON"),
    (33,"B1115-210-D00","HINGE RUBBER",2,"2","#02"),
    (34,"SM-6066002-TN","BOLT M6 L=60",4,"4","#02"),
    (35,"400-30949","TABLE",1,"1","COMMON"),
    (36,"111-55157","DRAWER ASM.",1,"1","COMMON"),
    (37,"111-55108","DRAWER",1,"(1)","COMMON"),
    (38,"111-55207","DRAWER SUPPORT",2,"(2)","COMMON"),
    (39,"SK-3311600-SC","WOOD SCREW D=3.1 L=16",6,"(6)","COMMON"),
    (40,"D8204-555-D00","DRAWER STOPPER",1,"(1)","COMMON"),
    (41,"NM-6080001-SC","NUT M8X1.25",1,"1","#02"),
    (42,"SM-6086002-TP","SCREW",1,"1","#02"),
    (43,"WP-0851846-SC","WASHER 8.5X22.0X1.8",1,"1","#02"),
    (44,"B8202-205-000","OIL MANAGEMENT",1,"1","#02"),
    (45,"B9121-012-000","OIL CAN",1,"1","#02"),
    (46,"SK-3311601-SE","WOOD SCREW D=3.1 L=16",2,"2","#02"),
    (47,"WP-0651646-SC","WASHER",4,"4","#02"),
    (48,"NM-6060001-SC","NUT M6",8,"8","#02"),
    (49,"B1111-210-D00","BED HINGE",2,"2","#02"),
    (50,"ST-9053511-SR","TAPPING SCREW M5X35",4,"4","COMMON"),
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
    if len(ROWS) != 50 or len(set(refs)) != 50 or sorted(refs) != list(range(1, 51)):
        raise SystemExit("Daftar REF tidak valid.")

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    old = db.execute("""
        SELECT id, component_name, catalog_ref, diagram_page
        FROM components
        WHERE machine_id=? AND component_name=?
    """, (MID, TITLE)).fetchall()
    if old:
        db.close()
        raise SystemExit(f"Komponen dengan judul ini sudah ada: {[dict(x) for x in old]}")

    print("=== PREFLIGHT SECTION 17 ===")
    print("Judul:", TITLE)
    print("REF katalog:", len(ROWS))

    reuse = {}
    new = []
    errors = []

    for ref, pn, name, qty, raw, marker in ROWS:
        candidates = db.execute("""
            SELECT id, part_number, part_name, quantity, quantity_raw,
                   note, catalog_ref
            FROM parts
            WHERE machine_id=?
              AND notes LIKE ?
              AND CAST(catalog_ref AS INTEGER)=?
              AND part_number=?
              AND quantity=?
              AND quantity_raw=?
              AND COALESCE(note,'')=?
            ORDER BY id
        """, (MID, "%section 17%", ref, pn, qty, raw, marker)).fetchall()

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
                print(f"PAKAI ID{p['id']} | REF{ref} | {pn} | Qty {raw} | {marker}")
        else:
            new.append(ref)
            print(f"BARU | REF{ref} | {pn} | Qty {raw} | {marker}")

    print("\nStaging cocok:", len(reuse))
    print("Part baru:", len(new))

    if errors:
        for e in errors:
            print("ERROR:", e)
        db.close()
        raise SystemExit("Preflight gagal; database tidak diubah.")

    if len(reuse) + len(new) != 50:
        db.close()
        raise SystemExit("Mapping REF tidak lengkap.")

    print("\nKomponen lama ID452 dan ID454 tidak disentuh.")
    print("Part Section27 ID15054 dan ID15055 tidak akan dipakai ulang.")
    print("Diagram page:", PAGE)
    print("Gambar:", IMAGE)

    if not args.apply:
        print("\nDRY-RUN: belum ada perubahan database.")
        db.close()
        return

    backup = Path(
        "database/garment-before-ams210en1510-section17-"
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
            (machine_id, component_name, part_number, location, function,
             notes, image_path, source_url, catalog_ref, diagram_page)
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MID, TITLE,
            "Meja dan dudukan mesin",
            "Menopang mesin, pedal, laci, dan perlengkapan meja.",
            "Diimpor dari Parts List resmi JUKI AMS-210EN-1510.",
            IMAGE, URL, str(SECTION), PAGE
        ))
        component_id = cur.lastrowid

        for ref, pn, name, qty, raw, marker in ROWS:
            if ref in reuse:
                part_id = reuse[ref]
            else:
                cur = db.execute("""
                    INSERT INTO parts
                    (machine_id, source_document_id, part_number, part_name,
                     quantity, catalog_ref, diagram_page, note, source_url,
                     notes, quantity_raw)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    MID, DOC, pn, name, qty, ref, PAGE, marker, URL,
                    "AMS-210EN-1510 section 17 staging", raw
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
