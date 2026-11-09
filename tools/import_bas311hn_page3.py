import argparse
import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
CSV_FILE = Path("tmp/bas311hn/page3_staging_review.csv")
BACKUP_DIR = Path("backups")
MACHINE_ID = 227
COMPONENT_ID = 526
DOCUMENT_ID = 582
PAGE = 3

SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/-/media/ap2/"
    "ism/pdf/parts-book-download/bas311hn_326h_pb.pdf?rev=-1"
)

NEEDLE_NOTE = (
    "Katalog REF 40+: For -03[] mencantumkan NEEDLE, DPX5 (#16); "
    "For -05[] mencantumkan DPX17 (#19); For -07[] mencantumkan "
    "DPX17 (#25). Kode part dan jumlah tidak tercantum pada sumber "
    "yang diekstrak. Belum diverifikasi sebagai jarum terpasang; "
    "jangan membuat nomor part atau jumlah sendiri."
)

def fail(message):
    raise RuntimeError(message)

def load_csv():
    if not CSV_FILE.is_file():
        fail(f"CSV tidak ditemukan: {CSV_FILE}")

    with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = set(reader.fieldnames or [])

    required = {
        "catalog_ref", "part_number", "quantity_raw", "part_name",
        "diagram_page", "mechanism", "verification"
    }
    if not required.issubset(fields):
        fail(f"Kolom CSV kurang: {required - fields}")

    if len(rows) != 54:
        fail(f"Jumlah staging berubah: {len(rows)}, seharusnya 54")

    # REF 40+ disimpan sebagai catatan karena kode dan quantity kosong.
    parts = [r for r in rows if r["catalog_ref"] != "40+"]

    if len(parts) != 51:
        fail(f"Kandidat part {len(parts)}, seharusnya 51")

    for r in parts:
        ref = r["catalog_ref"]
        if r["diagram_page"] != "3":
            fail(f"REF {ref}: halaman bukan 3")
        if not r["part_number"].strip() or not r["part_name"].strip():
            fail(f"REF {ref}: nomor/nama part kosong")
        raw = r["quantity_raw"].strip()
        if not raw.isdigit():
            fail(f"REF {ref}: quantity tidak valid: {raw!r}")
        if not ref.isdigit():
            fail(f"REF katalog tidak valid: {ref!r}")

    if sum(r["catalog_ref"] == "4" for r in parts) != 4:
        fail("REF 4 harus berisi empat opsi bearing")

    if sum(r["catalog_ref"] == "40+" for r in rows) != 3:
        fail("REF 40+ harus berisi tiga opsi jarum")

    return parts

def check_schema(con):
    tables = {
        row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    for table in ("machines", "components", "documents", "parts",
                  "component_parts"):
        if table not in tables:
            fail(f"Tabel tidak ditemukan: {table}")

    part_columns = {
        row[1] for row in con.execute("PRAGMA table_info(parts)")
    }
    required_parts = {
        "machine_id", "source_document_id", "part_number", "part_name",
        "quantity", "catalog_ref", "diagram_page", "note",
        "source_url", "notes", "quantity_raw"
    }
    if not required_parts.issubset(part_columns):
        fail(f"Kolom parts kurang: {required_parts - part_columns}")

def validate_initial_state(con):
    machine = con.execute(
        "SELECT model FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone()
    component = con.execute(
        "SELECT machine_id, component_name, notes FROM components WHERE id=?",
        (COMPONENT_ID,)
    ).fetchone()
    document = con.execute(
        "SELECT machine_id, document_type, source_url "
        "FROM documents WHERE id=?", (DOCUMENT_ID,)
    ).fetchone()

    if machine != ("BAS-311HN-03S",):
        fail(f"Mesin tidak sesuai: {machine}")
    if not component or component[0] != MACHINE_ID:
        fail(f"Komponen {COMPONENT_ID} tidak sesuai: {component}")
    if not document or document[0] != MACHINE_ID:
        fail(f"Dokumen {DOCUMENT_ID} tidak sesuai: {document}")
    if document[1] != "parts_catalog" or document[2] != SOURCE_URL:
        fail(f"Dokumen katalog berbeda dari yang diaudit: {document}")

    page_count = con.execute(
        "SELECT COUNT(*) FROM parts WHERE machine_id=? AND diagram_page=?",
        (MACHINE_ID, PAGE)
    ).fetchone()[0]
    total = con.execute(
        "SELECT COUNT(*) FROM parts WHERE machine_id=?",
        (MACHINE_ID,)
    ).fetchone()[0]

    if page_count != 0:
        fail(f"Halaman 3 sudah berisi {page_count} part; berhenti demi keamanan")
    if total != 170:
        fail(f"Total part berubah: {total}, seharusnya 170")

    # Hindari membuat relasi ganda bila ada perubahan database sejak audit.
    relations = con.execute(
        "SELECT COUNT(*) FROM component_parts WHERE component_id=?",
        (COMPONENT_ID,)
    ).fetchone()[0]
    if relations != 0:
        fail(f"Komponen {COMPONENT_ID} sudah memiliki {relations} relasi; "
             "skrip ini mengharapkan komponen yang masih kosong")

def perform_import(parts):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"garment-before-bas311hn-page3-{stamp}.db"

    if backup.exists():
        fail(f"File cadangan sudah ada: {backup}")

    # Buat salinan konsisten melalui SQLite Backup API.
    source = sqlite3.connect(str(DB))
    target = sqlite3.connect(str(backup))
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()

    print("Cadangan dibuat:", backup)

    con = sqlite3.connect(str(DB))
    con.execute("PRAGMA foreign_keys = ON")

    try:
        check_schema(con)
        validate_initial_state(con)
        con.execute("BEGIN IMMEDIATE")

        inserted_ids = []
        for r in parts:
            ref = int(r["catalog_ref"])
            is_bearing_option = (r["catalog_ref"] == "4")

            if is_bearing_option:
                note = (
                    "OPSI KATALOG REF 4 — bearing alternatif; "
                    "bearing yang terpasang belum diverifikasi."
                )
                relation_type = "catalog_option"
                relation_notes = (
                    "Opsi katalog REF 4; jangan dianggap sebagai "
                    "bearing terpasang sebelum verifikasi unit."
                )
            else:
                note = None
                relation_type = "catalog_part"
                relation_notes = "Diambil dari daftar part katalog halaman 3."

            detail = (
                f"Mekanisme: {r['mechanism']}. "
                f"Status staging: {r['verification']}."
            )

            cur = con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number, part_name,
                    quantity, catalog_ref, diagram_page, note, source_url,
                    notes, quantity_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID, DOCUMENT_ID,
                r["part_number"].strip(),
                r["part_name"].strip(),
                int(r["quantity_raw"].strip()),
                ref, PAGE, note, SOURCE_URL, detail,
                r["quantity_raw"].strip()
            ))
            part_id = cur.lastrowid
            inserted_ids.append(part_id)

            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                ) VALUES (?, ?, ?, ?)
            """, (
                COMPONENT_ID, part_id, relation_type, relation_notes
            ))

        # Simpan catatan REF 40+ pada komponen tanpa membuat kode part palsu.
        old_notes = con.execute(
            "SELECT notes FROM components WHERE id=?", (COMPONENT_ID,)
        ).fetchone()[0] or ""

        if NEEDLE_NOTE not in old_notes:
            new_notes = old_notes.rstrip()
            if new_notes:
                new_notes += "\n\n"
            new_notes += NEEDLE_NOTE
            con.execute(
                "UPDATE components SET notes=? WHERE id=?",
                (new_notes, COMPONENT_ID)
            )

        # Pastikan hasil persis seperti yang direncanakan.
        page_count = con.execute(
            "SELECT COUNT(*) FROM parts WHERE machine_id=? AND diagram_page=?",
            (MACHINE_ID, PAGE)
        ).fetchone()[0]
        total = con.execute(
            "SELECT COUNT(*) FROM parts WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0]
        rel_count = con.execute(
            "SELECT COUNT(*) FROM component_parts WHERE component_id=?",
            (COMPONENT_ID,)
        ).fetchone()[0]

        if len(inserted_ids) != 51 or page_count != 51:
            fail(f"Jumlah part tidak sesuai: inserted={len(inserted_ids)}, "
                 f"halaman={page_count}")
        if total != 221:
            fail(f"Total part tidak sesuai: {total}, seharusnya 221")
        if rel_count != 51:
            fail(f"Relasi komponen tidak sesuai: {rel_count}, seharusnya 51")

        # Relasi komponen 528 tidak boleh berubah.
        con.commit()
        print("\nIMPOR BERHASIL")
        print("Part baru:", len(inserted_ids))
        print("Part halaman 3:", page_count)
        print("Total part mesin 227:", total)
        print("Relasi komponen 526:", rel_count)
        print("REF 4 ditandai sebagai opsi katalog.")
        print("Catatan REF 40+ disimpan tanpa nomor part rekaan.")

    except Exception:
        con.rollback()
        print("\nTRANSAKSI DIBATALKAN — perubahan database di-rollback.")
        print("Cadangan tetap tersedia:", backup)
        raise
    finally:
        con.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true",
        help="Jalankan impor sungguhan; tanpa flag ini hanya dry-run"
    )
    args = parser.parse_args()

    if not DB.is_file():
        fail(f"Database tidak ditemukan: {DB}")

    parts = load_csv()
    con = sqlite3.connect(str(DB))
    try:
        check_schema(con)
        validate_initial_state(con)
    finally:
        con.close()

    print("Mesin: Brother BAS-311HN-03S (ID 227)")
    print("Komponen tujuan: ID 526")
    print("Dokumen sumber: ID 582")
    print("Kandidat part:", len(parts))
    print("Opsi bearing REF 4:", sum(
        r["catalog_ref"] == "4" for r in parts
    ))
    print("Opsi jarum REF 40+ dikecualikan dari tabel parts: 3")

    if not args.apply:
        print("\nDRY-RUN LULUS — database tidak diubah.")
        print("Jika hasil ini sesuai, impor sungguhan dijalankan dengan:")
        print("python tools/import_bas311hn_page3.py --apply")
        return

    perform_import(parts)

if __name__ == "__main__":
    main()
