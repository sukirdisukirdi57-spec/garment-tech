import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = Path("database/garment.db")
IMAGE = "component_images/lbh1790an_diagram14.png"

MACHINE_ID = 6
DOCUMENT_ID = 119
DIAGRAM_PAGE = 25

COMPONENTS = [
    {
        "component_name": "14.CONTROL BOX COMPONENTS",
        "catalog_ref": "1-63",
        "refs": range(1, 64),
        "notes": "Main component for all REF entries in Diagram 14.",
    },
    {
        "component_name": "Accesories of sewing machine main unit",
        "catalog_ref": "4-44",
        "refs": range(4, 45),
        "notes": "Subassembly grouping for REF 4-44 in Diagram 14.",
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB_PATH.is_file():
        raise SystemExit(f"Database tidak ditemukan: {DB_PATH}")

    if not Path("static", IMAGE).is_file():
        raise SystemExit(f"Gambar tidak ditemukan: static/{IMAGE}")

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        rows = db.execute("""
            SELECT id, catalog_ref, part_number, part_name
            FROM parts
            WHERE machine_id=? AND source_document_id=? AND diagram_page=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

        refs = [int(r["catalog_ref"]) for r in rows]
        expected = list(range(1, 64))

        if refs != expected:
            raise SystemExit(
                f"REF tidak sesuai. Jumlah={len(refs)}, REF={refs}"
            )

        print("=== PREFLIGHT DIAGRAM 14 ===")
        print("Jumlah part:", len(rows))
        print("REF lengkap:", refs[0], "-", refs[-1])

        for item in COMPONENTS:
            existing = db.execute("""
                SELECT id FROM components
                WHERE machine_id=? AND component_name=?
            """, (MACHINE_ID, item["component_name"])).fetchall()

            if existing:
                raise SystemExit(
                    f"Komponen sudah ada: {item['component_name']} "
                    f"(ID {[r['id'] for r in existing]})"
                )

            count = len(item["refs"])
            print(f"\nKomponen: {item['component_name']}")
            print("Catalog REF:", item["catalog_ref"])
            print("Jumlah relasi:", count)

        old_relations = db.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=? AND c.diagram_page=?
        """, (MACHINE_ID, DIAGRAM_PAGE)).fetchone()[0]

        if old_relations:
            raise SystemExit(
                f"Sudah ada {old_relations} relasi pada Diagram 14. "
                "Audit manual diperlukan."
            )

        print("\nRelasi Diagram 14 sebelumnya:", old_relations)

        if not args.apply:
            print("\nDRY-RUN: tidak ada perubahan database.")
            print("Jika hasil sudah benar, jalankan dengan --apply.")
            return

        backup = DB_PATH.with_name(
            "garment-before-lbh1790an-diagram14-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        shutil.copy2(DB_PATH, backup)
        print("\nBackup:", backup)

        try:
            db.execute("BEGIN IMMEDIATE")

            part_by_ref = {
                int(r["catalog_ref"]): r["id"] for r in rows
            }

            created = {}

            for item in COMPONENTS:
                cur = db.execute("""
                    INSERT INTO components (
                        machine_id, component_name, part_number,
                        location, function, notes, image_path,
                        source_url, catalog_ref, diagram_page
                    )
                    VALUES (?, ?, NULL, ?, ?, ?, ?, NULL, ?, ?)
                """, (
                    MACHINE_ID,
                    item["component_name"],
                    "Catalog Diagram 14",
                    "Catalog component and assembly grouping.",
                    item["notes"],
                    IMAGE,
                    item["catalog_ref"],
                    DIAGRAM_PAGE,
                ))

                component_id = cur.lastrowid
                created[item["component_name"]] = component_id

                for ref in item["refs"]:
                    db.execute("""
                        INSERT INTO component_parts (
                            component_id, part_id, relation_type, notes
                        )
                        VALUES (?, ?, ?, ?)
                    """, (
                        component_id,
                        part_by_ref[ref],
                        "catalog_component_part",
                        f"REF {ref}",
                    ))

            db.commit()

        except Exception:
            db.rollback()
            raise

        print("\n=== IMPOR BERHASIL ===")
        for name, component_id in created.items():
            count = db.execute("""
                SELECT COUNT(*) FROM component_parts
                WHERE component_id=?
            """, (component_id,)).fetchone()[0]
            print(f"ID {component_id} | {name} | {count} relasi")

        print("Total relasi:", db.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=? AND c.diagram_page=?
        """, (MACHINE_ID, DIAGRAM_PAGE)).fetchone()[0])

    finally:
        db.close()


if __name__ == "__main__":
    main()
