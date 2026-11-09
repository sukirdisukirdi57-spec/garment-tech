import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINE_ID = 6
DOCUMENT_ID = 119
PART_PAGE = 22
DIAGRAM_PAGE = 23
IMAGE = "component_images/lbh1790an_diagram12.png"

TITLE = "12. EXCLUSIVE PARTS FOR LBH-1790ANB"
EXPECTED_REFS = list(range(1, 12))

def stop(message):
    raise SystemExit("STOP: " + message)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file():
        stop("Database tidak ditemukan.")

    if not Path("static", IMAGE).is_file():
        stop("Gambar Diagram 12 tidak ditemukan.")

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    try:
        machine = db.execute("""
            SELECT model FROM machines WHERE id=?
        """, (MACHINE_ID,)).fetchone()

        if not machine or machine["model"] != "LBH-1790AN":
            stop("Identitas mesin tidak sesuai.")

        document = db.execute("""
            SELECT id, source_url FROM documents
            WHERE id=? AND machine_id=?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

        if not document:
            stop("Dokumen Parts List ID 119 tidak ditemukan.")

        parts = db.execute("""
            SELECT id, catalog_ref, part_number, part_name
            FROM parts
            WHERE machine_id=? AND source_document_id=?
              AND diagram_page=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, DOCUMENT_ID, PART_PAGE)).fetchall()

        refs = [int(p["catalog_ref"]) for p in parts
                if str(p["catalog_ref"]).isdigit()]

        existing = db.execute("""
            SELECT id, component_name
            FROM components
            WHERE machine_id=? AND diagram_page=?
        """, (MACHINE_ID, DIAGRAM_PAGE)).fetchall()

        linked = db.execute("""
            SELECT p.catalog_ref, COUNT(cp.id) AS total
            FROM parts p
            JOIN component_parts cp ON cp.part_id=p.id
            WHERE p.machine_id=? AND p.source_document_id=?
              AND p.diagram_page=?
            GROUP BY p.id
        """, (MACHINE_ID, DOCUMENT_ID, PART_PAGE)).fetchall()

        print("=== PREFLIGHT DIAGRAM 12 ===")
        print("Mesin:", machine["model"])
        print("Judul:", TITLE)
        print("PDF page: 28 | Catalog page: 23")
        print("Parts diagram_page:", PART_PAGE)
        print("Components diagram_page:", DIAGRAM_PAGE)
        print("Jumlah part:", len(parts))
        print("REF:", refs)
        print("Komponen pada halaman target:",
              [dict(x) for x in existing])
        print("Part yang sudah memiliki relasi:", len(linked))
        print("Gambar:", IMAGE)

        if refs != EXPECTED_REFS or len(parts) != 11:
            stop("REF harus lengkap dan berurutan 1-11.")

        if len(set(refs)) != 11:
            stop("REF duplikat ditemukan.")

        if existing:
            stop("Komponen pada halaman target sudah ada.")

        if linked:
            stop("Sebagian part sudah memiliki relasi.")

        print("\n=== DAFTAR PART ===")
        for p in parts:
            print(
                f"REF {p['catalog_ref']} | ID {p['id']} | "
                f"{p['part_number']} | {p['part_name']}"
            )

        print("\nPREFLIGHT: LULUS")

        if not args.apply:
            print("DRY-RUN BERHASIL. Database belum diubah.")
            print("Untuk menerapkan, jalankan dengan --apply.")
            return

        db.close()

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = DB.with_name(
            f"garment-before-lbh1790an-diagram12-{stamp}.db"
        )
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        db = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row

        try:
            db.execute("BEGIN IMMEDIATE")

            current = db.execute("""
                SELECT id, catalog_ref
                FROM parts
                WHERE machine_id=? AND source_document_id=?
                  AND diagram_page=?
                ORDER BY CAST(catalog_ref AS INTEGER)
            """, (MACHINE_ID, DOCUMENT_ID, PART_PAGE)).fetchall()

            current_refs = [
                int(p["catalog_ref"]) for p in current
                if str(p["catalog_ref"]).isdigit()
            ]

            if current_refs != EXPECTED_REFS or len(current) != 11:
                raise RuntimeError("Data part berubah sejak preflight.")

            if db.execute("""
                SELECT COUNT(*) FROM components
                WHERE machine_id=? AND diagram_page=?
            """, (MACHINE_ID, DIAGRAM_PAGE)).fetchone()[0]:
                raise RuntimeError("Komponen target muncul sejak preflight.")

            if db.execute("""
                SELECT COUNT(*)
                FROM component_parts cp
                JOIN parts p ON p.id=cp.part_id
                WHERE p.machine_id=? AND p.source_document_id=?
                  AND p.diagram_page=?
            """, (MACHINE_ID, DOCUMENT_ID, PART_PAGE)).fetchone()[0]:
                raise RuntimeError("Relasi part berubah sejak preflight.")

            cur = db.execute("""
                INSERT INTO components (
                    machine_id, component_name, part_number,
                    location, function, notes, image_path,
                    source_url, catalog_ref, diagram_page
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                TITLE,
                "Catalog Diagram 12",
                "Main component for all REF entries in Diagram 12.",
                "Main catalog component for the LBH-1790ANB exclusive parts.",
                IMAGE,
                document["source_url"],
                "1-11",
                DIAGRAM_PAGE
            ))

            component_id = cur.lastrowid

            for p in current:
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

            count = db.execute("""
                SELECT COUNT(*) FROM component_parts
                WHERE component_id=?
            """, (component_id,)).fetchone()[0]

            if count != 11:
                raise RuntimeError(f"Relasi tidak lengkap: {count}/11")

            db.commit()

            print("\nIMPORT BERHASIL")
            print("Component ID:", component_id)
            print("Relasi:", count)

        except Exception:
            db.rollback()
            raise

    finally:
        db.close()

if __name__ == "__main__":
    main()
