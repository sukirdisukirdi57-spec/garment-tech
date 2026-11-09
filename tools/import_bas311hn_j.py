#!/usr/bin/env python3
import argparse
import csv
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
CSV_FILE = Path("tmp/bas311hn/j_staging_audited_v1.csv")
BACKUP_DIR = Path("backups")

MACHINE_ID = 227
DOCUMENT_ID = 582
PAGE = 39
CATEGORY = "J - Thread trimmer mechanism"
SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/"
    "-/media/ap2/ism/pdf/parts-book-download/"
    "bas311hn_326h_pb.pdf?rev=-1"
)

def stop(message):
    raise RuntimeError(message)

def load_rows():
    if not CSV_FILE.is_file():
        stop(f"CSV tidak ditemukan: {CSV_FILE}")

    with CSV_FILE.open(
        "r", newline="", encoding="utf-8-sig"
    ) as f:
        reader = csv.DictReader(f)
        required = {
            "catalog_ref", "part_number", "quantity_raw",
            "part_name", "diagram_page", "mechanism",
            "verification", "review_note", "audit_note", "status",
        }
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            stop("Kolom CSV tidak lengkap.")

        rows = list(reader)

    if len(rows) != 72:
        stop(f"Harus 72 baris; ditemukan {len(rows)}.")

    refs = []
    for row in rows:
        try:
            ref = int(row["catalog_ref"])
        except (ValueError, TypeError):
            stop(f"catalog_ref tidak valid: {row.get('catalog_ref')!r}")
        refs.append(ref)

        if row["diagram_page"].strip() != str(PAGE):
            stop(f"Ref {ref}: halaman harus {PAGE}.")
        if row["verification"].strip() != "VERIFIED":
            stop(f"Ref {ref}: verification belum VERIFIED.")
        if row["status"].strip() != "VERIFIED":
            stop(f"Ref {ref}: status audit belum VERIFIED.")
        if not row["part_number"].strip():
            stop(f"Ref {ref}: kode part kosong.")
        if not row["part_name"].strip():
            stop(f"Ref {ref}: nama part kosong.")
        if not row["quantity_raw"].strip().isdigit():
            stop(f"Ref {ref}: quantity tidak valid.")
        if row["mechanism"].strip() != (
            "J Thread trimmer mechanism (BAS-311HN/326H)"
        ):
            stop(f"Ref {ref}: label mekanisme tidak sesuai.")

    if sorted(refs) != list(range(1, 73)):
        stop("Referensi harus unik dan lengkap dari 1 sampai 72.")

    # Catatan: VERIFIED adalah status audit CSV, bukan bukti
    # independen kecocokan semua data terhadap katalog asli.
    return rows

def validate_database(con):
    machine = con.execute(
        "SELECT model FROM machines WHERE id = ?",
        (MACHINE_ID,),
    ).fetchone()
    if not machine or machine["model"] != "BAS-311HN-03S":
        stop("Mesin ID 227 tidak cocok dengan BAS-311HN-03S.")

    doc = con.execute("""
        SELECT machine_id, document_type, source_url
        FROM documents WHERE id = ?
    """, (DOCUMENT_ID,)).fetchone()

    if not doc:
        stop("Dokumen ID 582 tidak ditemukan.")
    if doc["machine_id"] != MACHINE_ID:
        stop("Dokumen bukan milik mesin ID 227.")
    if doc["document_type"] != "parts_catalog":
        stop("Jenis dokumen bukan parts_catalog.")
    if doc["source_url"] != SOURCE_URL:
        stop("URL dokumen tidak cocok.")

    existing = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id = ? AND diagram_page = ?
    """, (MACHINE_ID, PAGE)).fetchone()[0]
    if existing:
        stop(f"Halaman {PAGE} sudah berisi {existing} part.")

    categories = con.execute("""
        SELECT id FROM components
        WHERE machine_id = ? AND component_name = ?
    """, (MACHINE_ID, CATEGORY)).fetchall()
    if categories:
        stop(f"Kategori target sudah ada: {CATEGORY}.")

def main():
    parser = argparse.ArgumentParser(
        description="Importer J untuk Brother BAS-311HN-03S."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Simpan perubahan ke database lokal.",
    )
    parser.add_argument(
        "--confirm-catalog-reviewed",
        action="store_true",
        help=(
            "Konfirmasi manual bahwa 72 baris sudah diperiksa "
            "terhadap sumber katalog, termasuk varian -03S."
        ),
    )
    args = parser.parse_args()

    if not DB.is_file():
        stop(f"Database tidak ditemukan: {DB}")

    rows = load_rows()
    print("VALIDASI CSV: LULUS")
    print("Jumlah baris:", len(rows))
    print("Referensi: 1–72")
    print("Halaman:", PAGE)
    print("Kategori:", CATEGORY)
    print("Status CSV: 72 VERIFIED")
    print(
        "PERINGATAN: status VERIFIED belum membuktikan "
        "kecocokan independen dengan katalog."
    )

    if args.apply and not args.confirm_catalog_reviewed:
        stop(
            "Impor ditolak. Periksa seluruh data terhadap katalog "
            "terlebih dahulu. Setelah selesai, gunakan "
            "--confirm-catalog-reviewed."
        )

    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")

    try:
        validate_database(con)
        print("VALIDASI DATABASE: LULUS")
        print("Mesin: BAS-311HN-03S (ID 227)")
        print("Dokumen: parts_catalog (ID 582)")
        print("Halaman 39: kosong")
        print("Kategori J: belum ada")

        if not args.apply:
            print("\nDRY-RUN BERHASIL — database tidak diubah.")
            print("Rencana: 1 kategori, 72 parts, 72 relasi.")
            print("Belum ada data yang diimpor.")
            return

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / (
            "garment-before-bas311hn-page39-"
            + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            + ".db"
        )
        backup = sqlite3.connect(backup_path)
        try:
            con.backup(backup)
        finally:
            backup.close()
        print("Cadangan dibuat:", backup_path)

        try:
            con.execute("BEGIN IMMEDIATE")
            # Periksa kembali kondisi database di dalam transaksi.
            validate_database(con)

            cur = con.execute("""
                INSERT INTO components
                    (machine_id, component_name, function, notes,
                     source_url, diagram_page)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                CATEGORY,
                "Thread trimmer mechanism",
                "Brother BAS-311HN/326H Parts Book, halaman cetak 39. "
                "Pastikan kecocokan varian BAS-311HN-03S.",
                SOURCE_URL,
                PAGE,
            ))
            component_id = cur.lastrowid
            inserted_ids = []

            for row in rows:
                audit_note = row["audit_note"].strip()
                review_note = row["review_note"].strip()
                notes = (
                    "Audit: " + audit_note
                    if audit_note else review_note
                )

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
                    review_note,
                    SOURCE_URL,
                    notes,
                    row["quantity_raw"].strip(),
                ))
                part_id = cur.lastrowid
                inserted_ids.append(part_id)

                con.execute("""
                    INSERT INTO component_parts
                        (component_id, part_id, relation_type, notes)
                    VALUES (?, ?, ?, ?)
                """, (
                    component_id,
                    part_id,
                    "catalog_section",
                    "Brother BAS-311HN/326H Parts Book, halaman 39.",
                ))

            page_count = con.execute("""
                SELECT COUNT(*) FROM parts
                WHERE machine_id = ? AND diagram_page = ?
            """, (MACHINE_ID, PAGE)).fetchone()[0]

            placeholders = ",".join("?" for _ in inserted_ids)
            relation_count = con.execute(f"""
                SELECT COUNT(*) FROM component_parts
                WHERE component_id = ?
                  AND part_id IN ({placeholders})
            """, [component_id, *inserted_ids]).fetchone()[0]

            if len(inserted_ids) != 72:
                stop(f"Jumlah ID part baru salah: {len(inserted_ids)}.")
            if page_count != 72:
                stop(f"Jumlah part halaman 39 salah: {page_count}.")
            if relation_count != 72:
                stop(f"Jumlah relasi salah: {relation_count}.")

            con.commit()
            print("\nIMPOR BERHASIL.")
            print("Component ID:", component_id)
            print("Parts baru:", len(inserted_ids))
            print("Relasi baru:", relation_count)
            print("Backup:", backup_path)

        except Exception:
            con.rollback()
            raise
    finally:
        con.close()

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, AssertionError, sqlite3.Error) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        sys.exit(1)
