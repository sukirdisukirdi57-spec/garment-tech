#!/usr/bin/env python3
import argparse
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
CSV_FILE = Path("tmp/bas311hn/f_staging_review.csv")
BACKUP_DIR = Path("backups")

MACHINE_ID = 227
DOCUMENT_ID = 582
PAGE = 31
CATEGORY_NAME = "F - Lubrication"

SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/"
    "-/media/ap2/ism/pdf/parts-book-download/"
    "bas311hn_326h_pb.pdf?rev=-1"
)

# Impor aktual hanya boleh dilakukan setelah semua baris
# mendapat status VERIFIED atau VERIFIED_NOT_APPLICABLE.
APPROVED_STATUSES = {
    "VERIFIED",
    "VERIFIED_NOT_APPLICABLE",
}


def stop(message):
    raise RuntimeError(message)


def load_csv():
    if not CSV_FILE.is_file():
        stop(f"CSV tidak ditemukan: {CSV_FILE}")

    with CSV_FILE.open(
        "r", newline="", encoding="utf-8-sig"
    ) as f:
        reader = csv.DictReader(f)
        required = {
            "catalog_ref", "part_number", "quantity_raw",
            "part_name", "diagram_page", "mechanism",
            "verification", "review_note",
        }
        if not reader.fieldnames or not required.issubset(
            reader.fieldnames
        ):
            stop("Kolom CSV tidak sesuai dengan staging yang diharapkan.")
        rows = list(reader)

    if len(rows) != 65:
        stop(f"Jumlah baris harus 65, ditemukan {len(rows)}.")

    refs = []
    for row in rows:
        ref = int(row["catalog_ref"])
        refs.append(ref)

        status = row["verification"].strip()
        if status not in APPROVED_STATUSES | {
            "REVIEW_REQUIRED",
            "VARIANT_OPTION_REVIEW",
        }:
            stop(f"Ref {ref}: status verifikasi tidak dikenal: {status!r}.")

        if row["diagram_page"].strip() != str(PAGE):
            stop(f"Ref {ref}: halaman bukan {PAGE}.")
        if not row["part_name"].strip():
            stop(f"Ref {ref}: nama part kosong.")
        if not row["quantity_raw"].strip().isdigit():
            stop(f"Ref {ref}: quantity tidak valid.")
        if not row["part_number"].strip():
            stop(f"Ref {ref}: kode part kosong.")

    if sorted(refs) != list(range(1, 66)):
        stop("Ref harus lengkap, unik, dan berurutan 1–65.")

    return rows


def validate_database(con):
    machine = con.execute(
        "SELECT model FROM machines WHERE id=?",
        (MACHINE_ID,),
    ).fetchone()
    if not machine or machine[0] != "BAS-311HN-03S":
        stop("Mesin ID 227 tidak cocok dengan BAS-311HN-03S.")

    doc = con.execute("""
        SELECT machine_id, document_type, source_url
        FROM documents WHERE id=?
    """, (DOCUMENT_ID,)).fetchone()

    if not doc:
        stop("Dokumen sumber ID 582 tidak ditemukan.")
    if doc[0] != MACHINE_ID:
        stop("Dokumen sumber bukan milik mesin ID 227.")
    if doc[1] != "parts_catalog":
        stop("Jenis dokumen sumber bukan parts_catalog.")
    if doc[2] != SOURCE_URL:
        stop("URL dokumen sumber tidak sesuai.")

    existing_page = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id=? AND diagram_page=?
    """, (MACHINE_ID, PAGE)).fetchone()[0]

    if existing_page:
        stop(
            f"Halaman {PAGE} sudah memiliki {existing_page} baris part. "
            "Impor dihentikan untuk mencegah duplikasi."
        )

    existing_category = con.execute("""
        SELECT id FROM components
        WHERE machine_id=? AND component_name=?
    """, (MACHINE_ID, CATEGORY_NAME)).fetchall()

    if len(existing_category) > 1:
        stop("Kategori target terduplikasi.")

    return existing_category[0][0] if existing_category else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Jalankan impor aktual setelah seluruh status disetujui.",
    )
    args = parser.parse_args()

    rows = load_csv()

    print("CSV:", CSV_FILE)
    print("Jumlah baris:", len(rows))
    print("Ref:", min(int(r["catalog_ref"]) for r in rows),
          "sampai", max(int(r["catalog_ref"]) for r in rows))
    print("Kode kosong: tidak diizinkan")

    if not DB.is_file():
        stop(f"Database tidak ditemukan: {DB}")

    con = sqlite3.connect(DB, timeout=30)
    con.execute("PRAGMA foreign_keys=ON")

    try:
        category_id = validate_database(con)

        print("Mesin ID:", MACHINE_ID, "BAS-311HN-03S")
        print("Dokumen ID:", DOCUMENT_ID)
        print("Halaman diagram 31 masih kosong.")
        print("Kategori target:", category_id or "belum dibuat")

        status_counts = {}
        for row in rows:
            status = row["verification"].strip()
            status_counts[status] = status_counts.get(status, 0) + 1
        print("Status staging:", status_counts)

        if not args.apply:
            print("\nMODE DRY-RUN: database tidak diubah.")
            print("Validasi dasar lulus.")
            print("Impor aktual belum dijalankan.")
            return

        unapproved = [
            r["catalog_ref"] for r in rows
            if r["verification"].strip() not in APPROVED_STATUSES
        ]
        if unapproved:
            stop(
                "Impor ditolak: status belum disetujui untuk ref "
                + ", ".join(unapproved)
                + ". Tinjau semua baris terlebih dahulu."
            )

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / (
            "garment-before-bas311hn-page31-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )

        backup = sqlite3.connect(backup_path)
        try:
            con.backup(backup)
        finally:
            backup.close()

        print("Backup dibuat:", backup_path)

        try:
            con.execute("BEGIN IMMEDIATE")

            if category_id is None:
                cur = con.execute("""
                    INSERT INTO components
                        (machine_id, component_name, function, notes)
                    VALUES (?, ?, ?, ?)
                """, (
                    MACHINE_ID,
                    CATEGORY_NAME,
                    "Kelompok katalog spare part BROTHER BAS-311HN-03S",
                    "Sumber: Brother BAS-311HN/326H Parts Book; "
                    "seksi F, halaman cetak 31–33.",
                ))
                category_id = cur.lastrowid

            inserted_ids = []

            for row in rows:
                cur = con.execute("""
                    INSERT INTO parts (
                        machine_id, source_document_id, part_number,
                        part_name, quantity, catalog_ref, diagram_page,
                        note, source_url, notes, quantity_raw
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID,
                    DOCUMENT_ID,
                    row["part_number"].strip(),
                    row["part_name"].strip(),
                    int(row["quantity_raw"]),
                    int(row["catalog_ref"]),
                    PAGE,
                    row["review_note"].strip(),
                    SOURCE_URL,
                    row["mechanism"].strip(),
                    row["quantity_raw"].strip(),
                ))
                part_id = cur.lastrowid
                inserted_ids.append(part_id)

                con.execute("""
                    INSERT INTO component_parts (
                        component_id, part_id, relation_type, notes
                    ) VALUES (?, ?, ?, ?)
                """, (
                    category_id,
                    part_id,
                    "catalog_section",
                    "Brother BAS-311HN/326H Parts Book, "
                    "section F, printed pages 31–33; diagram page 31.",
                ))

            part_count = con.execute("""
                SELECT COUNT(*) FROM parts
                WHERE machine_id=? AND diagram_page=?
            """, (MACHINE_ID, PAGE)).fetchone()[0]

            placeholders = ",".join("?" for _ in inserted_ids)
            relation_count = con.execute(
                f"""
                SELECT COUNT(*) FROM component_parts
                WHERE component_id=? AND part_id IN ({placeholders})
                """,
                [category_id, *inserted_ids],
            ).fetchone()[0]

            if part_count != 65:
                stop(f"Verifikasi jumlah part gagal: {part_count}.")
            if len(inserted_ids) != 65:
                stop(
                    f"Jumlah ID part baru tidak sesuai: {len(inserted_ids)}."
                )
            if relation_count != 65:
                stop(
                    "Verifikasi relasi untuk part baru gagal: "
                    f"{relation_count}."
                )

            con.commit()
            print("\nIMPOR BERHASIL.")
            print("Kategori ID:", category_id)
            print("Part ditambahkan:", part_count)
            print("Relasi ditambahkan:", relation_count)
            print("Backup:", backup_path)

        except Exception:
            con.rollback()
            raise

    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("GAGAL:", exc, file=sys.stderr)
        sys.exit(1)
