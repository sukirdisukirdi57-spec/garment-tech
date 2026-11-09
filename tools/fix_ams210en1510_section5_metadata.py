import argparse
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINE_ID = 15
DOCUMENT_ID = 136
PAGE = 9
NOTE = "AMS-210EN catalog staging; section 5"

URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

def stop(message):
    raise SystemExit("STOP: " + message)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file():
        stop("Database tidak ditemukan")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        doc = con.execute("""
            SELECT id, source_url
            FROM documents
            WHERE id=? AND machine_id=?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

        if not doc or doc["source_url"] != URL:
            stop("Dokumen Parts List tidak sesuai")

        rows = con.execute("""
            SELECT id, catalog_ref, source_document_id,
                   diagram_page, source_url
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, NOTE)).fetchall()

        refs = [r["catalog_ref"] for r in rows]

        if len(rows) != 66 or refs != list(range(1, 67)):
            stop(f"Staging tidak lengkap atau tidak berurutan: {refs}")

        for r in rows:
            metadata = (
                r["source_document_id"],
                r["diagram_page"],
                r["source_url"],
            )
            allowed = (
                (None, None, None),
                (None, PAGE, URL),
            )
            if metadata not in allowed:
                stop(
                    f"Metadata REF {r['catalog_ref']} "
                    f"memiliki nilai tidak terduga: {metadata}"
                )

        print("=== PREFLIGHT METADATA SECTION 5 ===")
        print("Staging:", len(rows), "/ 66")
        print("REF:", refs[0], "-", refs[-1])
        print("Target metadata:", (DOCUMENT_ID, PAGE, URL))
        print("Kolom yang akan diperbarui: source_document_id, diagram_page, source_url")

        if not args.apply:
            print("DRY-RUN OK: database tidak diubah.")
            return

        backup = DB.with_name(
            "garment-before-ams210en1510-section5-metadata-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )

        con.close()
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        con.execute("BEGIN IMMEDIATE")

        current = con.execute("""
            SELECT id, catalog_ref, source_document_id,
                   diagram_page, source_url
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, NOTE)).fetchall()

        if len(current) != 66:
            stop("Jumlah staging berubah sebelum transaksi")

        for r in current:
            metadata = (
                r["source_document_id"],
                r["diagram_page"],
                r["source_url"],
            )
            if metadata not in ((None, None, None), (None, PAGE, URL)):
                stop(f"Metadata berubah sebelum transaksi: REF {r['catalog_ref']}")

        con.execute("""
            UPDATE parts
            SET source_document_id=?,
                diagram_page=?,
                source_url=?
            WHERE machine_id=? AND notes=?
        """, (DOCUMENT_ID, PAGE, URL, MACHINE_ID, NOTE))

        result = con.execute("""
            SELECT COUNT(*)
            FROM parts
            WHERE machine_id=? AND notes=?
              AND source_document_id=?
              AND diagram_page=?
              AND source_url=?
        """, (MACHINE_ID, NOTE, DOCUMENT_ID, PAGE, URL)).fetchone()[0]

        if result != 66:
            raise RuntimeError(f"Validasi metadata gagal: {result}/66")

        con.commit()
        print("APPLY BERHASIL")
        print("Metadata valid:", result, "/ 66")
        print("Backup:", backup)

    except BaseException:
        if con and con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
