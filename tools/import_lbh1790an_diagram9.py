import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram9.png")
IMAGE_DB = "component_images/lbh1790an_diagram9.png"

MACHINE_ID = 6
DOC_ID = 119
PAGE = 17
MAIN_TITLE = "9. BOBBIN THREAD TRIMMER COMPONENTS"
SUB_TITLE = "THROAT_PLATE_BASE_UNIT"

def main():
    if not DB.exists():
        raise SystemExit(f"Database tidak ditemukan: {DB}")
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

        refs = [int(p["catalog_ref"]) for p in parts
                if str(p["catalog_ref"]).isdigit()]

        print("=== PREFLIGHT DIAGRAM 9 ===")
        print("Judul:", MAIN_TITLE)
        print("Jumlah baris:", len(parts))
        print("Jumlah REF unik:", len(set(refs)))
        print("REF hilang:", sorted(set(range(1, 76)) - set(refs)))
        print("REF di luar target:", sorted(set(refs) - set(range(1, 76))))
        print("REF ganda:", sorted(r for r in set(refs) if refs.count(r) > 1))

        if len(parts) != 75 or set(refs) != set(range(1, 76)):
            raise SystemExit("GAGAL: REF harus lengkap 1-75 dan masing-masing satu baris.")

        existing = con.execute("""
            SELECT id, component_name, catalog_ref, diagram_page
            FROM components
            WHERE machine_id=? AND diagram_page=?
        """, (MACHINE_ID, PAGE)).fetchall()

        print("Komponen lama:", [dict(x) for x in existing])
        if existing:
            raise SystemExit("GAGAL: Sudah ada komponen pada diagram_page 17. Audit manual dahulu.")

        sub_parent = next(p for p in parts if int(p["catalog_ref"]) == 27)
        if sub_parent["part_name"] != SUB_TITLE:
            print("Nama REF 27 di database:", sub_parent["part_name"])
            raise SystemExit("GAGAL: Nama REF 27 tidak cocok dengan nama subassembly yang dikonfirmasi.")

        subparts = [p for p in parts if 27 <= int(p["catalog_ref"]) <= 46]
        print("Subassembly:", SUB_TITLE)
        print("REF subassembly:", len(subparts), "REF 27-46")

        if len(subparts) != 20:
            raise SystemExit("GAGAL: Anggota subassembly bukan 20 REF.")

        print("\nDRY-RUN BERHASIL. Belum ada perubahan database.")
        print("Jika hasil ini benar, jalankan dengan --apply.")

        if "--apply" not in __import__("sys").argv:
            return

        backup = DB.with_name(
            f"garment-before-lbh1790an-diagram9-{datetime.now():%Y%m%d-%H%M%S}.db"
        )
        con.commit()
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO components
            (machine_id, component_name, location, function, notes,
             image_path, source_url, catalog_ref, diagram_page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID, MAIN_TITLE, "Catalog Diagram 9",
            "Main component for all REF entries in Diagram 9.",
            "Official catalog title. Includes REF 1-75.",
            IMAGE_DB, None, "1-75", PAGE
        ))
        main_id = cur.lastrowid

        cur = con.execute("""
            INSERT INTO components
            (machine_id, component_name, location, function, notes,
             image_path, source_url, catalog_ref, diagram_page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID, SUB_TITLE, "Catalog Diagram 9",
            "Subassembly shown inside the dotted boundary.",
            "Subassembly REF 27-46; parent REF 27 included.",
            IMAGE_DB, None, "27-46", PAGE
        ))
        sub_id = cur.lastrowid

        for p in parts:
            ref = int(p["catalog_ref"])
            con.execute("""
                INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
                VALUES (?, ?, ?, ?)
            """, (main_id, p["id"], "catalog_component_part", f"REF {ref}"))

            if 27 <= ref <= 46:
                con.execute("""
                    INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                    VALUES (?, ?, ?, ?)
                """, (sub_id, p["id"], "catalog_component_part", f"REF {ref}"))

        con.commit()
        print("\nAPPLY BERHASIL")
        print("Main component ID:", main_id, "| relasi:", len(parts))
        print("Subassembly ID:", sub_id, "| relasi:", len(subparts))
        print("Backup:", backup)

    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
