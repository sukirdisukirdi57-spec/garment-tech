#!/usr/bin/env python3
import argparse
import csv
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
CSV_FILE = Path("tmp/bas311hn/k_staging_review.csv")
PDF_FILE = Path("tmp/bas311hn/bas311hn_326h_pb.pdf")
BACKUP_DIR = Path("backups")

MACHINE_ID = 227
DOCUMENT_ID = 582
PAGE = 43
PDF_LIST_PAGE = 49
CATEGORY = "K - Thread wiper mechanism"
MECHANISM = "K Thread wiper mechanism (BAS-311HN/326H)"
SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/"
    "-/media/ap2/ism/pdf/parts-book-download/"
    "bas311hn_326h_pb.pdf?rev=-1"
)


def stop(message):
    raise RuntimeError(message)


def load_rows(require_verified=False):
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

    if len(rows) != 27:
        stop(f"Harus 27 baris; ditemukan {len(rows)}.")

    refs = []
    codes = []

    for row in rows:
        try:
            ref = int(row["catalog_ref"])
        except (ValueError, TypeError):
            stop(f"Referensi tidak valid: {row.get('catalog_ref')!r}")
        refs.append(ref)

        code = row["part_number"].strip()
        name = row["part_name"].strip()
        qty = row["quantity_raw"].strip()

        if not code or not name:
            stop(f"Ref {ref}: kode atau nama part kosong.")
        if not qty.isdigit() or int(qty) < 1:
            stop(f"Ref {ref}: kuantitas tidak valid.")
        if row["diagram_page"].strip() != str(PAGE):
            stop(f"Ref {ref}: diagram_page harus {PAGE}.")
        if row["mechanism"].strip() != MECHANISM:
            stop(f"Ref {ref}: label mekanisme tidak cocok.")

        codes.append(code)

        if require_verified:
            if row["verification"].strip() != "VERIFIED":
                stop(f"Ref {ref}: verification belum VERIFIED.")
            if row["status"].strip() != "VERIFIED":
                stop(f"Ref {ref}: status belum VERIFIED.")

    if sorted(refs) != list(range(1, 28)):
        stop("Referensi harus unik dan lengkap dari 1 sampai 27.")
    if len(set(codes)) != 27:
        stop("Kode part duplikat ditemukan di CSV.")

    return rows


def validate_pdf(rows):
    if not PDF_FILE.is_file():
        stop(f"PDF katalog tidak ditemukan: {PDF_FILE}")

    try:
        result = subprocess.run(
            [
                "pdftotext", "-f", str(PDF_LIST_PAGE),
                "-l", str(PDF_LIST_PAGE), "-layout",
                str(PDF_FILE), "-"
            ],
            check=True, capture_output=True, text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        stop(f"Gagal membaca halaman daftar part PDF: {exc}")

    normalized = re.sub(r"\s+", " ", result.stdout)
    source = {}

    pattern = re.compile(
        r"(?<!\d)(\d{1,2})\s+([A-Z0-9]{6,})\s+(\d+)\s+"
    )
    for match in pattern.finditer(normalized):
        ref = int(match.group(1))
        if 1 <= ref <= 27 and ref not in source:
            source[ref] = (match.group(2), int(match.group(3)))

    if len(source) != 27:
        stop(
            "Ekstraksi otomatis PDF tidak menemukan semua 27 referensi "
            f"(terbaca {len(source)}). Periksa teks halaman PDF secara manual."
        )

    for row in rows:
        ref = int(row["catalog_ref"])
        expected = (
            row["part_number"].strip(),
            int(row["quantity_raw"]),
        )
        if source.get(ref) != expected:
            stop(
                f"Ref {ref}: CSV={expected}, PDF={source.get(ref)}. "
                "Impor dibatalkan."
            )

    print("PEMERIKSAAN PDF: 27 kode dan kuantitas cocok.")
    print("Catatan: nama part tetap perlu pemeriksaan katalog.")


def validate_database(con):
    machine = con.execute(
        "SELECT model FROM machines WHERE id = ?", (MACHINE_ID,)
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

    count = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id = ? AND diagram_page = ?
    """, (MACHINE_ID, PAGE)).fetchone()[0]
    if count:
        stop(f"Halaman {PAGE} sudah memiliki {count} part.")

    existing = con.execute("""
        SELECT id, component_name FROM components
        WHERE machine_id = ?
          AND lower(component_name) LIKE '%thread wiper%'
    """, (MACHINE_ID,)).fetchall()
    if existing:
        stop(f"Komponen Thread Wiper sudah ada: {[tuple(x) for x in existing]}")


def main():
    parser = argparse.ArgumentParser(
        description="Importer K — Brother BAS-311HN-03S"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Simpan data ke database lokal."
    )
    parser.add_argument(
        "--confirm-catalog-reviewed", action="store_true",
        help="Konfirmasi manual pemeriksaan nama, kode, jumlah, dan varian."
    )
    args = parser.parse_args()

    if not DB.is_file():
        stop(f"Database tidak ditemukan: {DB}")

    rows = load_rows(require_verified=args.apply)
    validate_pdf(rows)

    print("VALIDASI CSV: LULUS")
    print("Baris:", len(rows))
    print("Referensi: 1–27")
    print("Halaman diagram cetak:", PAGE)
    print("Halaman daftar part PDF:", PDF_LIST_PAGE)
    print("Kategori:", CATEGORY)

    if args.apply and not args.confirm_catalog_reviewed:
        stop(
            "Impor ditolak. Periksa seluruh nama part dan kecocokan varian "
            "terhadap katalog, lalu berikan --confirm-catalog-reviewed."
        )

    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")

    try:
        validate_database(con)
        print("VALIDASI DATABASE: LULUS")
        print("Mesin: BAS-311HN-03S (ID 227)")
        print("Dokumen katalog: ID 582")
        print("Halaman 43 kosong; kategori Thread Wiper belum ada.")

        if not args.apply:
            print("\nDRY-RUN BERHASIL — database tidak diubah.")
            print("Rencana: 1 komponen, 27 parts, 27 relasi.")
            if any(
                r["verification"].strip() != "VERIFIED"
                or r["status"].strip() != "VERIFIED"
                for r in rows
            ):
                print("IMPOR PERMANEN TERKUNCI: CSV masih berstatus REVIEW.")
            else:
                print("CSV berstatus VERIFIED; konfirmasi katalog tetap diperlukan.")
            return

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / (
            "garment-before-bas311hn-k-"
            + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            + ".db"
        )
        backup = sqlite3.connect(backup_path)
        try:
            con.backup(backup)
        finally:
            backup.close()

        print("Cadangan database dibuat:", backup_path)

        try:
            con.execute("BEGIN IMMEDIATE")
            validate_database(con)

            cur = con.execute("""
                INSERT INTO components
                    (machine_id, component_name, function, notes,
                     source_url, diagram_page)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                CATEGORY,
                "Thread wiper mechanism",
                "Brother BAS-311HN/326H Parts Book, halaman cetak 43. "
                "Kecocokan varian harus sudah ditinjau manual.",
                SOURCE_URL,
                PAGE,
            ))
            component_id = cur.lastrowid
            part_ids = []

            for row in rows:
                ref = int(row["catalog_ref"])
                code = row["part_number"].strip()
                name = row["part_name"].strip()
                qty_raw = row["quantity_raw"].strip()
                review = row["review_note"].strip()
                audit = row["audit_note"].strip()
                notes = "Audit: " + audit if audit else review

                cur = con.execute("""
                    INSERT INTO parts (
                        machine_id, source_document_id, part_number,
                        part_name, quantity, catalog_ref, diagram_page,
                        note, source_url, notes, quantity_raw
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID, DOCUMENT_ID, code, name, int(qty_raw),
                    ref, PAGE, review, SOURCE_URL, notes, qty_raw,
                ))
                part_id = cur.lastrowid
                part_ids.append(part_id)

                con.execute("""
                    INSERT INTO component_parts
                        (component_id, part_id, relation_type, notes)
                    VALUES (?, ?, ?, ?)
                """, (
                    component_id, part_id, "catalog_section",
                    "Brother BAS-311HN/326H Parts Book, halaman cetak 43.",
                ))

            part_count = con.execute("""
                SELECT COUNT(*) FROM parts
                WHERE machine_id = ? AND diagram_page = ?
            """, (MACHINE_ID, PAGE)).fetchone()[0]
            relation_count = con.execute("""
                SELECT COUNT(*) FROM component_parts
                WHERE component_id = ?
            """, (component_id,)).fetchone()[0]

            if part_count != 27 or relation_count != 27:
                stop(
                    f"Hitungan pasca-insert tidak cocok: "
                    f"parts halaman={part_count}, relasi={relation_count}."
                )

            con.commit()
            print("IMPOR BERHASIL.")
            print("Component ID:", component_id)
            print("Jumlah parts:", part_count)
            print("Jumlah relasi:", relation_count)

        except Exception:
            con.rollback()
            raise

    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"DITOLAK: {exc}")
        raise SystemExit(1)
