import sqlite3
import shutil
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram8.png")
IMAGE_DB = "component_images/lbh1790an_diagram8.png"

MACHINE_ID = 6
DOC_ID = 119
PAGE = 15

MAIN_TITLE = "8. NEEDLE THREAD TRIMMER COMPONENTS"
SUB_TITLE = "ASSY_UTT_CAM_ARM"

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

        refs = [
            int(p["catalog_ref"]) for p in parts
            if str(p["catalog_ref"]).isdigit()
        ]

        print("=== PREFLIGHT DIAGRAM 8 ===")
        print("Judul:", MAIN_TITLE)
        print("Jumlah baris:", len(parts))
        print("Jumlah REF unik:", len(set(refs)))
        print("REF hilang:", sorted(set(range(1, 72)) - set(refs)))
        print("REF di luar target:", sorted(set(refs) - set(range(1, 72))))
        print("REF ganda:", sorted(r for r in set(refs) if refs.count(r) > 1))

        if len(parts) != 71 or set(refs) != set(range(1, 72)):
            raise SystemExit("GAGAL: REF harus lengkap 1-71.")

        existing = con.execute("""
            SELECT id, component_name, catalog_ref, diagram_page
            FROM components
            WHERE machine_id=? AND diagram_page=?
        """, (MACHINE_ID, PAGE)).fetchall()

        print("Komponen lama:", [dict(x) for x in existing])
        if existing:
            raise SystemExit(
                "GAGAL: Sudah ada komponen pada diagram_page 15. Audit dahulu."
            )

        subparts = [p for p in parts if 28 <= int(p["catalog_ref"]) <= 32]
        parent = next(p for p in parts if int(p["catalog_ref"]) == 28)

        if parent["part_name"] != SUB_TITLE:
            print("Nama REF 28:", parent["part_name"])
            raise SystemExit("GAGAL: Nama induk REF 28 tidak cocok.")

        if len(subparts) != 5:
            raise SystemExit("GAGAL: Subassembly harus memiliki REF 28-32.")

        print("Subassembly:", SUB_TITLE)
        print("REF subassembly:", len(subparts), "(28-32)")
        print("REF 31: satu part katalog; posisi A kiri dan B kanan.")
        print("\nDRY-RUN BERHASIL. Belum ada perubahan database.")
        print("Jika benar, jalankan dengan --apply.")

        if "--apply" not in sys.argv:
            return

        backup = DB.with_name(
            f"garment-before-lbh1790an-diagram8-{datetime.now():%Y%m%d-%H%M%S}.db"
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
            MACHINE_ID, MAIN_TITLE, "Catalog Diagram 8",
            "Main component for all REF entries in Diagram 8.",
            "Official catalog title. Includes REF 1-71.",
            IMAGE_DB, None, "1-71", PAGE
        ))
        main_id = cur.lastrowid

        cur = con.execute("""
            INSERT INTO components
            (machine_id, component_name, location, function, notes,
             image_path, source_url, catalog_ref, diagram_page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID, SUB_TITLE, "Catalog Diagram 8",
            "Subassembly indicated by dotted boundary REF 28-32.",
            "REF 28 is parent; REF 29-32 are subparts. REF 31 is shown at A (left) and B (right), one catalog part.",
            IMAGE_DB, None, "28-32", PAGE
        ))
        sub_id = cur.lastrowid

        for p in parts:
            ref = int(p["catalog_ref"])

            con.execute("""
                INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
                VALUES (?, ?, ?, ?)
            """, (
                main_id, p["id"],
                "catalog_component_part", f"REF {ref}"
            ))

            if 28 <= ref <= 32:
                note = f"REF {ref}"
                if ref == 31:
                    note += " - position A left / B right; one catalog REF"

                con.execute("""
                    INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                    VALUES (?, ?, ?, ?)
                """, (
                    sub_id, p["id"],
                    "catalog_component_part", note
                ))

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
