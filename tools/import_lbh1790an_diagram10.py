import sqlite3
import shutil
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram10.png")
IMAGE_DB = "component_images/lbh1790an_diagram10.png"

MACHINE_ID = 6
DOC_ID = 119
PAGE = 19

MAIN_TITLE = "10. CLOTH CUTTING KNIFE COMPONENTS"
OUTER_TITLE = "KNIFE_DRIVING_ASSY"
INNER_TITLE = "KNIFE_DRIVING_LINK_ASSY"

def main():
    if not DB.exists():
        raise SystemExit("Database tidak ditemukan.")
    if not IMAGE.exists():
        raise SystemExit(f"Gambar tidak ditemukan: {IMAGE}")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        parts = con.execute("""
            SELECT id, catalog_ref, part_number, part_name
            FROM parts
            WHERE machine_id=? AND source_document_id=? AND diagram_page=?
            ORDER BY CAST(catalog_ref AS INTEGER), id
        """, (MACHINE_ID, DOC_ID, PAGE)).fetchall()

        refs = [
            int(p["catalog_ref"]) for p in parts
            if str(p["catalog_ref"]).isdigit()
        ]

        print("=== PREFLIGHT DIAGRAM 10 ===")
        print("Judul:", MAIN_TITLE)
        print("Jumlah baris:", len(parts))
        print("REF unik:", len(set(refs)))
        print("REF hilang:", sorted(set(range(1, 31)) - set(refs)))
        print("REF di luar target:", sorted(set(refs) - set(range(1, 31))))
        print("REF ganda:", sorted(r for r in set(refs) if refs.count(r) > 1))

        if len(parts) != 30 or set(refs) != set(range(1, 31)):
            raise SystemExit("GAGAL: REF harus lengkap 1-30.")

        existing = con.execute("""
            SELECT id, component_name, catalog_ref, diagram_page
            FROM components
            WHERE machine_id=? AND diagram_page=?
        """, (MACHINE_ID, PAGE)).fetchall()

        print("Komponen lama:", [dict(x) for x in existing])
        if existing:
            raise SystemExit("GAGAL: Komponen diagram 10 sudah ada. Audit dahulu.")

        by_ref = {int(p["catalog_ref"]): p for p in parts}

        if by_ref[11]["part_name"] != OUTER_TITLE:
            raise SystemExit(
                f"Nama REF 11 tidak cocok: {by_ref[11]['part_name']}"
            )

        if by_ref[12]["part_name"] != INNER_TITLE:
            raise SystemExit(
                f"Nama REF 12 tidak cocok: {by_ref[12]['part_name']}"
            )

        outer_parts = [by_ref[r] for r in range(11, 21)]
        inner_parts = [by_ref[r] for r in range(12, 15)]

        print("Subassembly luar:", OUTER_TITLE, "| REF 11-20 |", len(outer_parts), "relasi")
        print("Subassembly dalam:", INNER_TITLE, "| REF 12-14 |", len(inner_parts), "relasi")
        print("REF 12-14 akan terhubung ke main, outer, dan inner.")
        print("\nDRY-RUN BERHASIL. Belum ada perubahan database.")
        print("Jika benar, jalankan dengan --apply.")

        if "--apply" not in sys.argv:
            return

        backup = DB.with_name(
            f"garment-before-lbh1790an-diagram10-{datetime.now():%Y%m%d-%H%M%S}.db"
        )

        con.commit()
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        con.execute("BEGIN IMMEDIATE")

        def add_component(name, catalog_ref, notes):
            cur = con.execute("""
                INSERT INTO components
                (machine_id, component_name, location, function, notes,
                 image_path, source_url, catalog_ref, diagram_page)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID, name, "Catalog Diagram 10",
                "Catalog component and assembly grouping.",
                notes, IMAGE_DB, None, catalog_ref, PAGE
            ))
            return cur.lastrowid

        main_id = add_component(
            MAIN_TITLE, "1-30",
            "Main component for all REF entries in Diagram 10."
        )

        outer_id = add_component(
            OUTER_TITLE, "11-20",
            "Outer dashed-box assembly. Includes REF 11-20."
        )

        inner_id = add_component(
            INNER_TITLE, "12-14",
            "Nested dashed-box assembly inside KNIFE_DRIVING_ASSY. Includes REF 12-14."
        )

        def add_relations(component_id, selected_parts):
            for p in selected_parts:
                ref = int(p["catalog_ref"])
                con.execute("""
                    INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                    VALUES (?, ?, ?, ?)
                """, (
                    component_id, p["id"],
                    "catalog_component_part", f"REF {ref}"
                ))

        add_relations(main_id, parts)
        add_relations(outer_id, outer_parts)
        add_relations(inner_id, inner_parts)

        con.commit()

        print("\nAPPLY BERHASIL")
        print("Main ID:", main_id, "| relasi:", len(parts))
        print("Outer ID:", outer_id, "| relasi:", len(outer_parts))
        print("Inner ID:", inner_id, "| relasi:", len(inner_parts))
        print("Backup:", backup)

    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
