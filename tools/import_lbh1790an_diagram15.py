import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = Path("database/garment.db")
IMAGE = "component_images/lbh1790an_diagram15.png"

MACHINE_ID = 6
DOCUMENT_ID = 119
DIAGRAM_PAGE = 27
COMPONENT_NAME = "15.WIRING DIAGRAM"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB_PATH.is_file():
        raise SystemExit("Database tidak ditemukan.")

    if not Path("static", IMAGE).is_file():
        raise SystemExit("Gambar Diagram 15 tidak ditemukan.")

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        rows = db.execute("""
            SELECT id, catalog_ref, part_number, part_name
            FROM parts
            WHERE machine_id=? AND source_document_id=?
              AND diagram_page=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

        refs = [int(r["catalog_ref"]) for r in rows]

        if refs != list(range(1, 45)):
            raise SystemExit(
                f"REF tidak sesuai: jumlah {len(refs)}, REF {refs}"
            )

        existing = db.execute("""
            SELECT id FROM components
            WHERE machine_id=? AND component_name=?
        """, (MACHINE_ID, COMPONENT_NAME)).fetchall()

        if existing:
            raise SystemExit(
                f"Komponen sudah ada: {[r['id'] for r in existing]}"
            )

        print("=== PREFLIGHT DIAGRAM 15 ===")
        print("Jumlah part:", len(rows))
        print("REF lengkap:", refs[0], "-", refs[-1])
        print("Komponen baru:", COMPONENT_NAME)
        print("Catalog REF: 1-44")
        print("Jumlah relasi: 44")

        print("\n=== KOMPONEN LAMA DIPERTAHANKAN ===")
        old = db.execute("""
            SELECT id, component_name
            FROM components
            WHERE machine_id=? AND diagram_page=?
            ORDER BY id
        """, (MACHINE_ID, DIAGRAM_PAGE)).fetchall()

        for r in old:
            print(f"ID {r['id']} | {r['component_name']}")

        if not args.apply:
            print("\nDRY-RUN: tidak ada perubahan database.")
            print("Jika benar, jalankan dengan --apply.")
            return

        backup = DB_PATH.with_name(
            "garment-before-lbh1790an-diagram15-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        shutil.copy2(DB_PATH, backup)
        print("\nBackup:", backup)

        try:
            db.execute("BEGIN IMMEDIATE")

            cur = db.execute("""
                INSERT INTO components (
                    machine_id, component_name, part_number,
                    location, function, notes, image_path,
                    source_url, catalog_ref, diagram_page
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?, NULL, ?, ?)
            """, (
                MACHINE_ID,
                COMPONENT_NAME,
                "Catalog Diagram 15",
                "Catalog component and wiring diagram grouping.",
                "Main component linking all REF entries in Diagram 15.",
                IMAGE,
                "1-44",
                DIAGRAM_PAGE,
            ))

            component_id = cur.lastrowid

            for r in rows:
                ref = int(r["catalog_ref"])
                db.execute("""
                    INSERT INTO component_parts (
                        component_id, part_id, relation_type, notes
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    component_id,
                    r["id"],
                    "catalog_component_part",
                    f"REF {ref}",
                ))

            db.commit()

        except Exception:
            db.rollback()
            raise

        count = db.execute("""
            SELECT COUNT(*) FROM component_parts
            WHERE component_id=?
        """, (component_id,)).fetchone()[0]

        print("\n=== IMPOR BERHASIL ===")
        print("Component ID:", component_id)
        print("Nama:", COMPONENT_NAME)
        print("Jumlah relasi:", count)

    finally:
        db.close()


if __name__ == "__main__":
    main()
