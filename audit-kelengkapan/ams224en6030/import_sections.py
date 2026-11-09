import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path.cwd()
DB = ROOT / "database/garment.db"
TXT = ROOT / "audit-kelengkapan/ams224en6030/partslist.txt"
BACKUP_DIR = ROOT / "database/backups"

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/"
    "j/u/juki_ams224en_parts_book.pdf"
)
DOC_TITLE = "JUKI AMS-224EN/IP-420 Parts List — No.1575-03"

SECTIONS = [
    {
        "name": "FRAME & MISCELLANEOUS COVER COMPONENTS (4)",
        "header_line": 670,
        "expected": 91,
    },
    {
        "name": "X-Y COMPONENTS (2)",
        "header_line": 2192,
        "expected": 96,
    },
]

ROW_RE = re.compile(
    r"^\s*(\d{1,3})\s+"
    r"(#\d{2})?\s*"
    r"([A-Z0-9][A-Z0-9-]*)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)


def parse_catalog():
    if not TXT.is_file():
        raise RuntimeError(f"File katalog tidak ditemukan: {TXT}")

    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    result = []

    for section in SECTIONS:
        header_idx = section["header_line"] - 1

        if header_idx < 0 or header_idx >= len(lines):
            raise RuntimeError("Nomor baris header di luar file.")

        header = lines[header_idx].upper()
        if "REF.NO" not in header or "PART NO" not in header:
            raise RuntimeError(
                f"Header tidak cocok pada baris {section['header_line']}."
            )

        section_rows = []
        expected_ref = 1

        for idx in range(header_idx + 1, len(lines)):
            line = lines[idx]

            if not line.strip():
                continue

            m = ROW_RE.match(line)
            if not m:
                break

            ref_s, note_marker, part_no, part_name, qty_raw = m.groups()
            ref = int(ref_s)

            if ref != expected_ref:
                raise RuntimeError(
                    f"{section['name']}: baris {idx + 1}, "
                    f"referensi {ref}, seharusnya {expected_ref}."
                )

            if not part_name.strip():
                raise RuntimeError(f"Deskripsi kosong pada baris {idx + 1}.")

            # Kolom quantity bertipe INTEGER.
            # Pecahan seperti 0.05 disimpan NULL di quantity,
            # tetapi teks aslinya tetap disimpan di quantity_raw.
            q = qty_raw.strip("()")
            d = Decimal(q)
            quantity = int(d) if d == d.to_integral_value() else None

            note_text = note_marker or ""
            notes = (
                f"AMS-224EN-6030 section: {section['name']}; "
                f"source line {idx + 1}"
            )

            section_rows.append({
                "machine_id": 47,
                "part_number": part_no,
                "part_name": part_name.strip(),
                "quantity": quantity,
                "catalog_ref": ref,
                "diagram_page": None,
                "note": note_text,
                "source_url": SOURCE_URL,
                "notes": notes,
                "quantity_raw": qty_raw,
                "_section": section["name"],
                "_line": idx + 1,
            })

            expected_ref += 1

            if ref == section["expected"]:
                break

        refs = [r["catalog_ref"] for r in section_rows]
        wanted = list(range(1, section["expected"] + 1))

        if refs != wanted:
            raise RuntimeError(
                f"{section['name']}: validasi gagal; "
                f"terbaca {len(refs)}/{section['expected']} referensi."
            )

        result.extend(section_rows)

    if len(result) != 187:
        raise RuntimeError(f"Total baris tidak sesuai: {len(result)}.")

    # Validasi bahwa kombinasi section + ref tidak berulang.
    keys = [(r["_section"], r["catalog_ref"]) for r in result]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Ada referensi ganda dalam bagian yang sama.")

    return result


def table_columns(con, table):
    return {
        row[1] for row in con.execute(f"PRAGMA table_info({table})")
    }


def main():
    parser = argparse.ArgumentParser(
        description="Impor parts katalog AMS-224EN-6030 secara aman."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Terapkan impor setelah validasi dan membuat backup.",
    )
    args = parser.parse_args()

    rows = parse_catalog()

    if not DB.is_file():
        raise RuntimeError(f"Database tidak ditemukan: {DB}")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        con.execute("PRAGMA foreign_keys=ON")

        required = {
            "machine_id", "source_document_id", "part_number",
            "part_name", "quantity", "catalog_ref", "diagram_page",
            "note", "source_url", "notes", "quantity_raw",
        }
        cols = table_columns(con, "parts")

        if not required.issubset(cols):
            raise RuntimeError(
                "Kolom tabel parts belum sesuai. "
                f"Kolom yang kurang: {sorted(required - cols)}"
            )

        machine = con.execute(
            "SELECT id, model FROM machines WHERE id=47"
        ).fetchone()

        if not machine:
            raise RuntimeError("machine_id=47 tidak ditemukan.")

        if "AMS-224EN-6030" not in (machine["model"] or "").upper():
            raise RuntimeError(
                f"Model machine_id=47 tidak cocok: {machine['model']!r}"
            )

        doc = con.execute(
            "SELECT id, title FROM documents WHERE source_url=?",
            (SOURCE_URL,),
        ).fetchone()

        if doc:
            doc_id = doc["id"]
            print(f"Dokumen sumber sudah ada: id={doc_id}")
        else:
            doc_id = None
            print("Dokumen sumber belum terdaftar; akan dibuat saat --apply.")

        # Cocokkan baris berdasarkan dokumen, section, ref, dan nomor part.
        existing = []
        if doc_id is not None:
            existing = con.execute(
                """
                SELECT id, part_number, part_name, quantity,
                       catalog_ref, note, notes, quantity_raw
                FROM parts
                WHERE machine_id=47 AND source_document_id=?
                """,
                (doc_id,),
            ).fetchall()

        by_key = {}
        for r in existing:
            key = (r["notes"], r["catalog_ref"])
            if key in by_key:
                raise RuntimeError(
                    f"Data database sudah memiliki kunci ganda: {key}"
                )
            by_key[key] = r

        to_insert = []
        already_ok = 0

        for r in rows:
            key = (r["notes"], r["catalog_ref"])
            old = by_key.get(key)

            if old is None:
                to_insert.append(r)
                continue

            expected_values = (
                r["part_number"], r["part_name"], r["quantity"],
                r["catalog_ref"], r["note"], r["notes"],
                r["quantity_raw"],
            )
            existing_values = (
                old["part_number"], old["part_name"], old["quantity"],
                old["catalog_ref"], old["note"], old["notes"],
                old["quantity_raw"],
            )

            if expected_values != existing_values:
                raise RuntimeError(
                    f"Konflik data pada section {r['_section']}, "
                    f"ref {r['catalog_ref']}. Tidak ada perubahan dibuat."
                )

            already_ok += 1

        print("\n=== RINGKASAN VALIDASI ===")
        print(f"Mesin: {machine['model']} (id 47)")
        print(f"Jumlah baris katalog: {len(rows)}")
        print(f"Baris sudah cocok: {already_ok}")
        print(f"Baris baru yang akan ditambahkan: {len(to_insert)}")
        print("Diagram page: NULL (belum dipetakan)")
        print("Quantity pecahan: NULL di quantity, teks asli di quantity_raw")

        print("\nContoh baris yang akan diimpor:")
        for r in to_insert[:5]:
            print({
                "section": r["_section"],
                "ref": r["catalog_ref"],
                "part_number": r["part_number"],
                "part_name": r["part_name"],
                "quantity": r["quantity"],
                "quantity_raw": r["quantity_raw"],
                "note": r["note"],
            })

        if not args.apply:
            print("\nDRY-RUN: database tidak diubah.")
            print("Jika hasil di atas benar, jalankan ulang dengan --apply.")
            return

        if not to_insert:
            print("\nSemua 187 baris sudah cocok. Tidak perlu impor ulang.")
            return

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = BACKUP_DIR / f"garment_before_ams224en6030_parts_{stamp}.db"

        # Gunakan SQLite backup API agar backup konsisten.
        backup_con = sqlite3.connect(backup)
        try:
            con.backup(backup_con)
        finally:
            backup_con.close()

        print(f"\nBackup dibuat: {backup}")

        try:
            con.execute("BEGIN IMMEDIATE")

            # Buat catatan dokumen sumber bila URL belum terdaftar.
            doc = con.execute(
                "SELECT id FROM documents WHERE source_url=?",
                (SOURCE_URL,),
            ).fetchone()

            if doc:
                doc_id = doc["id"]
            else:
                dcols = table_columns(con, "documents")
                needed_doc_cols = {
                    "machine_id", "document_type", "title",
                    "source_url", "local_file", "notes",
                }
                if not needed_doc_cols.issubset(dcols):
                    raise RuntimeError("Skema tabel documents tidak sesuai.")

                cur = con.execute(
                    """
                    INSERT INTO documents
                    (machine_id, document_type, title, source_url,
                     local_file, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        47,
                        "Parts List",
                        DOC_TITLE,
                        SOURCE_URL,
                        str(TXT.with_name("partslist.pdf").relative_to(ROOT)),
                        "Edition No.1575-03; teks diekstrak untuk impor "
                        "bagian katalog yang khusus AMS-224EN-6030.",
                    ),
                )
                doc_id = cur.lastrowid

            for r in to_insert:
                con.execute(
                    """
                    INSERT INTO parts (
                        machine_id, source_document_id, part_number,
                        part_name, quantity, catalog_ref, diagram_page,
                        note, source_url, notes, quantity_raw
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        47, doc_id, r["part_number"], r["part_name"],
                        r["quantity"], r["catalog_ref"], None,
                        r["note"], r["source_url"], r["notes"],
                        r["quantity_raw"],
                    ),
                )

            # Verifikasi jumlah baris per section sebelum commit.
            for section in SECTIONS:
                count = con.execute(
                    """
                    SELECT COUNT(*)
                    FROM parts
                    WHERE machine_id=47 AND source_document_id=?
                      AND notes LIKE ?
                    """,
                    (doc_id, f"%section: {section['name']};%"),
                ).fetchone()[0]

                if count != section["expected"]:
                    raise RuntimeError(
                        f"Verifikasi gagal untuk {section['name']}: "
                        f"{count}/{section['expected']}."
                    )

            con.commit()

        except Exception:
            con.rollback()
            raise

        print("\nIMPOR BERHASIL.")
        print(f"Baris baru ditambahkan: {len(to_insert)}")
        print(f"Baris yang sudah ada dan cocok: {already_ok}")
        print("Verifikasi akhir: 91 + 96 baris.")
        print("Backup tersedia untuk pemulihan manual jika diperlukan.")

    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"\nDIBATALKAN: {exc}")
