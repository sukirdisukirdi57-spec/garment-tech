import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = Path("database/garment.db")
MACHINE_ID = 6
DOCUMENT_ID = 119
DIAGRAM_PAGE = 24
IMAGE_PATH = "component_images/lbh1790an_diagram13.png"

TITLE = (
    "13. OPERATION BOX COMPONENTS "
    "(ACCESSORIES OF A CONTROL BOX)"
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        machine = db.execute(
            "SELECT model FROM machines WHERE id=?",
            (MACHINE_ID,)
        ).fetchone()

        if not machine or machine["model"] != "LBH-1790AN":
            raise SystemExit("GAGAL: model mesin tidak sesuai.")

        parts = db.execute("""
            SELECT id, catalog_ref, part_number, part_name
            FROM parts
            WHERE machine_id=? AND source_document_id=?
              AND diagram_page=?
            ORDER BY catalog_ref
        """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

        existing = db.execute("""
            SELECT id, component_name
            FROM components
            WHERE machine_id=? AND diagram_page=?
        """, (MACHINE_ID, DIAGRAM_PAGE)).fetchall()

        print("=== PREFLIGHT DIAGRAM 13 ===")
        print("Judul:", TITLE)
        print("Jumlah part:", len(parts))
        print("Komponen lama:", [dict(x) for x in existing])

        refs = [r["catalog_ref"] for r in parts]
        if refs != [1, 2, 3, 4]:
            raise SystemExit(
                f"GAGAL: REF harus 1-4, ditemukan {refs}"
            )

        if existing:
            raise SystemExit(
                "DIBATALKAN: komponen Diagram 13 sudah ada."
            )

        for p in parts:
            print(
                f"REF {p['catalog_ref']} | "
                f"ID {p['id']} | {p['part_number']} | {p['part_name']}"
            )

        print("Preflight: LULUS")

        if not args.apply:
            print("Mode DRY-RUN. Belum ada perubahan database.")
            print("Jika benar, jalankan dengan --apply.")
            return

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = DB_PATH.with_name(
            f"garment-before-lbh1790an-diagram13-{stamp}.db"
        )
        shutil.copy2(DB_PATH, backup)
        print("Backup:", backup)

        try:
            db.execute("BEGIN IMMEDIATE")

            cur = db.execute("""
                INSERT INTO components (
                    machine_id, component_name, part_number,
                    location, function, notes, image_path,
                    source_url, catalog_ref, diagram_page
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                TITLE,
                None,
                "Catalog Diagram 13",
                "Catalog component and assembly grouping.",
                "Main component for all REF entries in Diagram 13.",
                IMAGE_PATH,
                None,
                "1-4",
                DIAGRAM_PAGE
            ))

            component_id = cur.lastrowid

            for p in parts:
                db.execute("""
                    INSERT INTO component_parts (
                        component_id, part_id, relation_type, notes
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    component_id,
                    p["id"],
                    "catalog_component_part",
                    f"REF {p['catalog_ref']}"
                ))

            relation_count = db.execute("""
                SELECT COUNT(*) FROM component_parts
                WHERE component_id=?
            """, (component_id,)).fetchone()[0]

            if relation_count != 4:
                raise RuntimeError(
                    f"Relasi tidak lengkap: {relation_count}/4"
                )

            db.commit()
            print("IMPORT BERHASIL")
            print("Component ID:", component_id)
            print("Jumlah relasi:", relation_count)

        except Exception:
            db.rollback()
            raise

    finally:
        db.close()

if __name__ == "__main__":
    main()
