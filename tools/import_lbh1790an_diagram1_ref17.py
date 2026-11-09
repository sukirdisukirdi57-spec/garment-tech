import sqlite3
import shutil
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("database")

MACHINE_ID = 6
DOCUMENT_ID = 119
COMPONENT_NAME = "HOOK OIL SHIELD COVER COMPL"
MAIN_REF = "17"
DIAGRAM_PAGE = 1

REFS = list(range(17, 30))

def main():
    apply = "--apply" in sys.argv

    if not DB.exists():
        raise SystemExit("Database tidak ditemukan.")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        component = con.execute("""
            SELECT id FROM components
            WHERE machine_id=?
              AND diagram_page=?
              AND catalog_ref=?
        """, (MACHINE_ID, DIAGRAM_PAGE, MAIN_REF)).fetchone()

        if component:
            raise ValueError(
                "Komponen REF 17 sudah ada. Impor dibatalkan."
            )

        parts = con.execute("""
            SELECT id, catalog_ref, part_number, part_name, note
            FROM parts
            WHERE machine_id=?
              AND source_document_id=?
              AND diagram_page=?
              AND CAST(catalog_ref AS INTEGER)
                    BETWEEN 17 AND 29
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

        found = [int(p["catalog_ref"]) for p in parts]

        if found != REFS:
            raise ValueError(
                f"REF tidak lengkap atau duplikat. Ditemukan: {found}"
            )

        if len({p["part_number"] for p in parts}) != len(parts):
            print("Peringatan: ada nomor part berulang.")

        print("=== PREFLIGHT SECTION 1 / REF 17–29 ===")
        for p in parts:
            print(
                f"REF {p['catalog_ref']} | "
                f"ID {p['id']} | {p['part_number']} | "
                f"{p['part_name']} | Marker {p['note']}"
            )

        print("\nJumlah REF:", len(parts))
        print("Komponen baru:", COMPONENT_NAME)
        print("Relasi yang akan dibuat:", len(parts))

        if not apply:
            print("\nDRY-RUN: belum ada perubahan database.")
            return

        backup = BACKUP_DIR / (
            "garment-before-lbh1790an-diagram1-ref17-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )

        con.commit()
        shutil.copy2(DB, backup)
        print("\nBackup:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")

            cur = con.execute("""
                INSERT INTO components (
                    machine_id, component_name, part_number,
                    location, function, notes, image_path,
                    source_url, catalog_ref, diagram_page
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                COMPONENT_NAME,
                parts[0]["part_number"],
                "Diagram 1",
                "HOOK OIL SHIELD COVER assembly",
                "Catalog REF 17–29; main REF 17",
                "component_images/lbh1790an_diagram1.png",
                None,
                MAIN_REF,
                DIAGRAM_PAGE
            ))

            component_id = cur.lastrowid

            for p in parts:
                con.execute("""
                    INSERT INTO component_parts (
                        component_id, part_id,
                        relation_type, notes
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    component_id,
                    p["id"],
                    "catalog_component_part",
                    f"REF {p['catalog_ref']}"
                ))

            count = con.execute("""
                SELECT COUNT(*)
                FROM component_parts
                WHERE component_id=?
            """, (component_id,)).fetchone()[0]

            if count != 13:
                raise ValueError(
                    f"Validasi relasi gagal: {count}, seharusnya 13."
                )

            con.commit()

            print("\nIMPORT BERHASIL")
            print("Component ID:", component_id)
            print("Jumlah relasi:", count)

        except Exception:
            con.rollback()
            raise

    finally:
        con.close()

if __name__ == "__main__":
    main()
