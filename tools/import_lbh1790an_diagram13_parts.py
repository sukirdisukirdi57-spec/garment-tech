import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = Path("database/garment.db")
MACHINE_ID = 6
DOCUMENT_ID = 119
DIAGRAM_PAGE = 24

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)

DATA = [
    (1, "401-89780", "LBH OPERATION BOX ASSY", 1, "#01"),
    (2, "401-91872", "LBH OPERATION BOX ASSY CE", 1, "#02"),
    (3, "SK-3382001-SE", "SCREW D=3.8 L=20", 4, None),
    (4, "CM-6001001-01", "WEEE MARK LABEL S", 1, "#02"),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"Database tidak ditemukan: {DB_PATH}")

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        machine = db.execute(
            "SELECT id, model FROM machines WHERE id=?",
            (MACHINE_ID,)
        ).fetchone()

        if not machine or machine["model"] != "LBH-1790AN":
            raise SystemExit("GAGAL: machine ID 6 bukan LBH-1790AN.")

        existing = db.execute("""
            SELECT id, catalog_ref, part_number, part_name, diagram_page
            FROM parts
            WHERE machine_id=? AND source_document_id=?
              AND diagram_page=?
            ORDER BY catalog_ref
        """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchall()

        print("=== PREFLIGHT DIAGRAM 13 PARTS ===")
        print("Model:", machine["model"])
        print("Diagram page:", DIAGRAM_PAGE)
        print("Jumlah target:", len(DATA))
        print("Baris yang sudah ada:", len(existing))

        for row in existing:
            print(dict(row))

        if existing:
            raise SystemExit(
                "DIBATALKAN: diagram_page 24 sudah memiliki data. "
                "Audit dahulu sebelum impor."
            )

        refs = [x[0] for x in DATA]
        if refs != [1, 2, 3, 4] or len(set(refs)) != len(refs):
            raise SystemExit("GAGAL: REF tidak lengkap atau duplikat.")

        for ref, pn, name, qty, note in DATA:
            print(
                f"REF {ref}: {pn} | {name} | Qty {qty} | Note {note}"
            )

        print("\nPreflight: LULUS")

        if not args.apply:
            print("Mode DRY-RUN. Belum ada perubahan database.")
            print("Jika data sudah benar, jalankan dengan --apply.")
            return

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = DB_PATH.with_name(
            f"garment-before-lbh1790an-diagram13-parts-{stamp}.db"
        )
        shutil.copy2(DB_PATH, backup)
        print("Backup:", backup)

        try:
            db.execute("BEGIN IMMEDIATE")

            for ref, pn, name, qty, note in DATA:
                db.execute("""
                    INSERT INTO parts (
                        machine_id, source_document_id,
                        part_number, part_name, quantity,
                        catalog_ref, diagram_page, note,
                        source_url, notes, quantity_raw
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID, DOCUMENT_ID, pn, name, qty,
                    ref, DIAGRAM_PAGE, note,
                    SOURCE_URL, "JUKI LBH-1790AN Parts List - Diagram 13",
                    str(qty)
                ))

            count = db.execute("""
                SELECT COUNT(*) FROM parts
                WHERE machine_id=? AND source_document_id=?
                  AND diagram_page=?
            """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE)).fetchone()[0]

            if count != 4:
                raise RuntimeError(
                    f"Validasi gagal: ditemukan {count} baris, seharusnya 4."
                )

            db.commit()
            print("IMPORT BERHASIL: 4 baris part tersimpan.")

        except Exception:
            db.rollback()
            raise

    finally:
        db.close()

if __name__ == "__main__":
    main()
