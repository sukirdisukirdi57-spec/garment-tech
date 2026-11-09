import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = "component_images/lbh1790an_diagram11.png"
DIAGRAM_PAGE = 21
MACHINE_ID = 6
DOCUMENT_ID = 119

MAIN_NAME = "11. TABLE COMPONENTS"
SUB_NAME = "ACCESSORIES OF A CONTROL BOX"

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

if not DB.exists():
    raise SystemExit("ERROR: Database tidak ditemukan.")

if not Path("static", IMAGE).exists():
    raise SystemExit("ERROR: Gambar diagram tidak ditemukan.")

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

try:
    rows = db.execute("""
        SELECT id, catalog_ref, part_number, part_name
        FROM parts
        WHERE machine_id=? AND source_document_id=?
          AND diagram_page=?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

    refs = [int(r["catalog_ref"]) for r in rows
            if str(r["catalog_ref"]).isdigit()]

    expected = list(range(1, 22))
    missing = sorted(set(expected) - set(refs))
    extra = sorted(set(refs) - set(expected))
    duplicates = sorted({x for x in refs if refs.count(x) > 1})

    existing = db.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND diagram_page=?
    """, (MACHINE_ID, DIAGRAM_PAGE)).fetchall()

    print("=== PREFLIGHT DIAGRAM 11 ===")
    print("Judul:", MAIN_NAME)
    print("Jumlah baris:", len(rows))
    print("REF unik:", len(set(refs)))
    print("REF hilang:", missing)
    print("REF di luar target:", extra)
    print("REF ganda:", duplicates)
    print("Komponen lama:", [dict(x) for x in existing])
    print("Subassembly:", SUB_NAME, "REF 8-15")

    if len(rows) != 21 or refs != expected:
        raise SystemExit("STOP: Data REF tidak sesuai target.")

    if missing or extra or duplicates:
        raise SystemExit("STOP: Validasi REF gagal.")

    if existing:
        raise SystemExit("STOP: Komponen Diagram 11 sudah ada. Audit dahulu.")

    if not args.apply:
        print("\nDRY-RUN BERHASIL. Database belum diubah.")
        print("Jika hasil sudah benar, jalankan dengan --apply.")
        raise SystemExit(0)

    db.close()

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.with_name(f"garment-before-lbh1790an-diagram11-{stamp}.db")
    shutil.copy2(DB, backup)
    print("\nBackup:", backup)

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    try:
        db.execute("BEGIN IMMEDIATE")

        rows = db.execute("""
            SELECT id, catalog_ref
            FROM parts
            WHERE machine_id=? AND source_document_id=?
              AND diagram_page=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

        refs_now = [int(r["catalog_ref"]) for r in rows
                    if str(r["catalog_ref"]).isdigit()]

        if refs_now != expected:
            raise RuntimeError("Data REF berubah sejak preflight.")

        if db.execute("""
            SELECT COUNT(*) FROM components
            WHERE machine_id=? AND diagram_page=?
        """, (MACHINE_ID, DIAGRAM_PAGE)).fetchone()[0]:
            raise RuntimeError("Komponen Diagram 11 muncul sejak preflight.")

        def create_component(name, ref_range, notes, selected_rows):
            cur = db.execute("""
                INSERT INTO components (
                    machine_id, component_name, part_number,
                    location, function, notes, image_path,
                    source_url, catalog_ref, diagram_page
                ) VALUES (?, ?, NULL, ?, ?, ?, ?, NULL, ?, ?)
            """, (
                MACHINE_ID, name,
                "Catalog Diagram 11",
                "Catalog component and assembly grouping.",
                notes,
                IMAGE,
                ref_range,
                DIAGRAM_PAGE
            ))

            component_id = cur.lastrowid

            for part in selected_rows:
                db.execute("""
                    INSERT INTO component_parts (
                        component_id, part_id, relation_type, notes
                    ) VALUES (?, ?, ?, ?)
                """, (
                    component_id,
                    part["id"],
                    "catalog_component_part",
                    f"REF {part['catalog_ref']}"
                ))

            return component_id

        main_id = create_component(
            MAIN_NAME,
            "1-21",
            "Main component for all REF entries in Diagram 11.",
            rows
        )

        sub_rows = [
            r for r in rows
            if 8 <= int(r["catalog_ref"]) <= 15
        ]

        sub_id = create_component(
            SUB_NAME,
            "8-15",
            "Dashed-box assembly. Includes REF 8-15.",
            sub_rows
        )

        db.commit()

        print("\n=== IMPORT BERHASIL ===")
        print("Main component ID:", main_id, "| REF:", len(rows))
        print("Subassembly ID:", sub_id, "| REF:", len(sub_rows))

        for cid in (main_id, sub_id):
            count = db.execute("""
                SELECT COUNT(*) FROM component_parts
                WHERE component_id=?
            """, (cid,)).fetchone()[0]
            print("Komponen", cid, "jumlah relasi:", count)

    except Exception:
        db.rollback()
        raise

finally:
    db.close()
