#!/usr/bin/env python3
import argparse
import csv
import sqlite3
import sys
from collections import Counter
from pathlib import Path

DB = Path("database/garment.db")
CSV = Path("tmp/bas311hn/g_staging_audited_v3.csv")
BACKUP_DIR = Path("backups")
MACHINE_ID = 227
DOCUMENT_ID = 582
PAGE = 35
CATEGORY = "G - Threading mechanism"
SOURCE_URL = (
    "https://industrialsewingmachine.global.brother/"
    "-/media/ap2/ism/pdf/parts-book-download/"
    "bas311hn_326h_pb.pdf?rev=-1"
)
ELIGIBLE = {"VERIFIED"}
EXPECTED_STATUS_COUNTS = {
    "VERIFIED": 38,
    "VERIFIED_NOT_APPLICABLE": 10,
    "REVIEW_REQUIRED": 1,
    "VARIANT_OPTION_REVIEW": 5,
}
EXPECTED_REFS = {str(i) for i in range(1, 55)}

def stop(message):
    raise RuntimeError(message)

def load_rows():
    if not CSV.is_file():
        stop(f"CSV tidak ditemukan: {CSV}")
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            stop("CSV tidak memiliki header.")
        rows = list(reader)

    if len(rows) != 54:
        stop(f"Jumlah baris harus 54, ditemukan {len(rows)}.")

    refs = [r.get("catalog_ref", "").strip() for r in rows]
    if len(set(refs)) != 54 or set(refs) != EXPECTED_REFS:
        stop("Ref katalog harus unik dan lengkap dari 1 sampai 54.")

    statuses = Counter(r.get("verification", "").strip() for r in rows)
    if dict(statuses) != EXPECTED_STATUS_COUNTS:
        stop(f"Distribusi status berubah/tidak cocok: {dict(statuses)}")

    # Hanya status VERIFIED yang boleh menjadi kandidat impor.
    eligible = [r for r in rows if r["verification"].strip() in ELIGIBLE]
    if len(eligible) != 38:
        stop(f"Kandidat VERIFIED harus 38, ditemukan {len(eligible)}.")

    for r in eligible:
        for field in ("catalog_ref", "part_number", "part_name"):
            if not r.get(field, "").strip():
                stop(f"Kolom {field} kosong pada ref {r.get('catalog_ref')}.")

    return rows, eligible, statuses

def validate_database(con):
    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone()
    if not machine or machine["model"] != "BAS-311HN-03S":
        stop("Mesin target tidak cocok dengan BAS-311HN-03S.")

    doc = con.execute(
        """SELECT id, machine_id, document_type, source_url
           FROM documents WHERE id=?""", (DOCUMENT_ID,)
    ).fetchone()
    if not doc:
        stop("Dokumen sumber 582 tidak ditemukan.")
    if doc["machine_id"] != MACHINE_ID:
        stop("Dokumen 582 bukan milik mesin target.")
    if doc["document_type"] != "parts_catalog":
        stop("Jenis dokumen 582 bukan parts_catalog.")
    if doc["source_url"] != SOURCE_URL:
        stop("URL dokumen 582 tidak cocok dengan katalog resmi.")

    existing = con.execute(
        "SELECT COUNT(*) FROM parts WHERE machine_id=? AND diagram_page=?",
        (MACHINE_ID, PAGE),
    ).fetchone()[0]
    if existing:
        stop(f"Halaman {PAGE} sudah berisi {existing} part; batal untuk mencegah duplikasi.")

    category = con.execute(
        """SELECT id FROM components
           WHERE machine_id=? AND component_name=?""",
        (MACHINE_ID, CATEGORY),
    ).fetchall()
    if category:
        stop("Kategori G sudah ada; batal untuk mencegah duplikasi.")

    return dict(machine), dict(doc)

def main():
    parser = argparse.ArgumentParser(
        description="Dry-run/import terkontrol bagian G BAS-311HN-03S."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Menulis 38 baris VERIFIED ke database setelah validasi."
    )
    args = parser.parse_args()

    rows, eligible, statuses = load_rows()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        machine, doc = validate_database(con)
        print("VALIDASI STAGING: LULUS")
        print("Distribusi status:", dict(statuses))
        print("Baris VERIFIED untuk impor:", len(eligible))
        print("Baris yang ditahan/tidak diimpor:", len(rows) - len(eligible))
        print("Mesin:", machine)
        print("Dokumen:", doc["id"], doc["document_type"])
        print("Halaman diagram:", PAGE)
        print("Kategori:", CATEGORY)
        print("Contoh kandidat:")
        for r in eligible[:5]:
            print(
                f"  ref={r['catalog_ref']} | "
                f"{r['part_number']} | {r['part_name']} | "
                f"qty={r.get('quantity_raw', '')}"
            )

        if not args.apply:
            print("MODE: DRY-RUN")
            print("Database diubah: TIDAK")
            print("Impor dijalankan: TIDAK")
            return

        # Backup dibuat hanya pada mode --apply.
        from datetime import datetime
        import shutil
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = BACKUP_DIR / f"garment-before-bas311hn-page35-{stamp}.db"
        shutil.copy2(DB, backup)
        print("Cadangan:", backup)

        con.execute("BEGIN IMMEDIATE")
        # Ulangi validasi di dalam transaksi sebelum menulis.
        validate_database(con)

        cur = con.execute(
            """INSERT INTO components (machine_id, component_name, notes, source_url, diagram_page)
               VALUES (?, ?, ?, ?, ?)""",
            (
                MACHINE_ID, CATEGORY,
                "Bagian G katalog resmi Brother BAS-311HN-03S, halaman tercetak 35. "
                "Hanya baris VERIFIED yang dimasukkan; baris varian/opsi/review ditahan.",
                SOURCE_URL, PAGE,
            ),
        )
        component_id = cur.lastrowid

        inserted = 0
        for r in eligible:
            qty_raw = r.get("quantity_raw", "").strip()
            try:
                qty = int(qty_raw) if qty_raw else None
            except ValueError:
                qty = None

            note_parts = []
            for key in ("review_note",):
                val = r.get(key, "").strip()
                if val:
                    note_parts.append(val)
            notes = " | ".join(note_parts) or None

            cur = con.execute(
                """INSERT INTO parts
                   (machine_id, source_document_id, part_number, part_name,
                    quantity, catalog_ref, diagram_page, note, source_url,
                    notes, quantity_raw)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    MACHINE_ID, DOCUMENT_ID,
                    r["part_number"].strip(), r["part_name"].strip(),
                    qty, int(r["catalog_ref"]), PAGE,
                    r.get("note", "").strip() or None,
                    SOURCE_URL, notes, qty_raw or None,
                ),
            )
            part_id = cur.lastrowid
            con.execute(
                """INSERT INTO component_parts
                   (component_id, part_id, relation_type, notes)
                   VALUES (?, ?, ?, ?)""",
                (component_id, part_id, "catalog_section",
                 f"Bagian G, ref. {r['catalog_ref']}"),
            )
            inserted += 1

        if inserted != 38:
            stop(f"Jumlah insert tidak sesuai: {inserted}, seharusnya 38.")

        con.commit()
        print("IMPOR BERHASIL")
        print("Component ID:", component_id)
        print("Part ditambahkan:", inserted)
        print("Relasi ditambahkan:", inserted)
        print("Backup:", backup)
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("BERHENTI:", exc, file=sys.stderr)
        sys.exit(1)
