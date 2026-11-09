
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINE_ID = 47
DOCUMENT_ID = 583

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

# Judul resmi katalog dan halaman PDF
SECTIONS = [
    {
        "key": "FRAME & MISCELLANEOUS COVER COMPONENTS",
        "name": "FRAME & MISCELLANEOUS COVER COMPONENTS (4) (FOR 6030)",
        "min_ref": 1,
        "max_ref": 91,
        "page": 13,
    },
    {
        "key": "X-Y COMPONENTS",
        "name": "X-Y COMPONENTS (2) (FOR 6030)",
        "min_ref": 1,
        "max_ref": 96,
        "page": 57,
    },
]

def main():
    if not DB.exists():
        raise FileNotFoundError(DB)

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        # BACKUP DATABASE
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = DB.parent / f"garment-before-ams224-components-{timestamp}.db"

        backup_con = sqlite3.connect(backup)
        con.backup(backup_con)
        backup_con.close()

        print("BACKUP:", backup)

        con.execute("BEGIN IMMEDIATE")

        # PREFLIGHT
        machine = con.execute(
            "SELECT * FROM machines WHERE id=?",
            (MACHINE_ID,)
        ).fetchone()

        if not machine or machine["model"] != "AMS-224EN-6030":
            raise ValueError("Machine ID tidak sesuai.")

        doc = con.execute(
            "SELECT id FROM documents WHERE id=? AND machine_id=?",
            (DOCUMENT_ID, MACHINE_ID)
        ).fetchone()

        if not doc:
            raise ValueError("Dokumen katalog tidak ditemukan.")

        existing = con.execute(
            "SELECT COUNT(*) FROM components WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0]

        if existing:
            raise ValueError(
                f"Sudah ada {existing} komponen. "
                "Script dihentikan untuk mencegah duplikasi."
            )

        created_components = []
        total_parts = 0

        for section in SECTIONS:

            rows = con.execute("""
                SELECT id, catalog_ref, part_number
                FROM parts
                WHERE machine_id=?
                  AND source_document_id=?
                  AND notes LIKE ?
                ORDER BY catalog_ref
            """, (
                MACHINE_ID,
                DOCUMENT_ID,
                f"%{section['key']}%"
            )).fetchall()

            refs = [r["catalog_ref"] for r in rows]

            expected = list(range(
                section["min_ref"],
                section["max_ref"] + 1
            ))

            if len(rows) != len(expected):
                raise ValueError(
                    f"Jumlah part tidak cocok: {section['key']}"
                )

            if refs != expected:
                raise ValueError(
                    f"REF tidak berurutan: {section['key']}"
                )

            # Buat komponen induk
            cur = con.execute("""
                INSERT INTO components (
                    machine_id,
                    component_name,
                    part_number,
                    location,
                    function,
                    notes,
                    image_path,
                    source_url,
                    catalog_ref,
                    diagram_page
                )
                VALUES (?, ?, NULL, ?, ?, ?, NULL, ?, NULL, ?)
            """, (
                MACHINE_ID,
                section["name"],
                section["name"],
                "Assembly group berdasarkan katalog resmi JUKI.",
                f"Catalog No.1575-03. Section: {section['name']}",
                SOURCE_URL,
                section["page"],
            ))

            component_id = cur.lastrowid
            created_components.append(component_id)

            # Hubungkan spare part berdasarkan ID
            for part in rows:
                con.execute("""
                    INSERT INTO component_parts (
                        component_id,
                        part_id,
                        relation_type,
                        notes
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    component_id,
                    part["id"],
                    "catalog_component_part",
                    f"Catalog REF {part['catalog_ref']}"
                ))

            total_parts += len(rows)

            print(
                f"\nCREATED: {section['name']}"
                f"\nComponent ID: {component_id}"
                f"\nParts linked: {len(rows)}"
                f"\nDiagram page: {section['page']}"
            )

        # VERIFIKASI
        component_count = con.execute("""
            SELECT COUNT(*)
            FROM components
            WHERE machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        relation_count = con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            JOIN parts p ON p.id=cp.part_id
            WHERE c.machine_id=?
              AND p.machine_id=?
        """, (MACHINE_ID, MACHINE_ID)).fetchone()[0]

        if component_count != 2:
            raise ValueError("Jumlah komponen tidak sesuai.")

        if relation_count != 187:
            raise ValueError(
                f"Jumlah relasi salah: {relation_count}"
            )

        # Pastikan setiap part terhubung tepat satu kali
        duplicates = con.execute("""
            SELECT p.id, COUNT(cp.id) AS total
            FROM parts p
            JOIN component_parts cp ON cp.part_id=p.id
            JOIN components c ON c.id=cp.component_id
            WHERE p.machine_id=?
              AND c.machine_id=?
            GROUP BY p.id
            HAVING COUNT(cp.id) != 1
        """, (MACHINE_ID, MACHINE_ID)).fetchall()

        if duplicates:
            raise ValueError("Ditemukan relasi ganda.")

        con.commit()

        print("\n" + "=" * 50)
        print("HASIL AKHIR")
        print("=" * 50)
        print("Components :", component_count)
        print("Relations  :", relation_count)
        print("Parts      :", total_parts)
        print("Status     : BERHASIL")
        print("Backup     :", backup)

    except Exception:
        con.rollback()
        print("\nERROR: TRANSAKSI DIBATALKAN.")
        raise

    finally:
        con.close()


if __name__ == "__main__":
    main()
