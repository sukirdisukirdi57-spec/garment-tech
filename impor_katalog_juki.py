import argparse
import csv
import re
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
CSV_FILE = Path("staging_kemunculan_katalog_juki.csv")
BACKUP_DIR = Path("backups")

MACHINE_ID = 43
SOURCE_DOCUMENT_ID = 154

PAGES = [6, 8, 10, 12, 14, 16, 20, 22, 23, 28, 30, 32]


def parse_row(row):
    original = row["catalog_line_original"].rstrip()
    pn = row["part_number"].strip()

    positions = [
        m.start()
        for m in re.finditer(re.escape(pn), original, flags=re.IGNORECASE)
    ]
    if len(positions) != 1:
        raise ValueError(f"Nomor part tidak unik pada baris: {original}")

    start = positions[0]
    prefix = original[:start].strip()
    suffix = original[start + len(pn):].strip()

    ref_match = re.match(r"^(\d+)\b", prefix)
    if not ref_match:
        raise ValueError(f"Ref tidak terbaca: {original}")

    ref = ref_match.group(1)
    if ref != row["catalog_ref"]:
        raise ValueError(f"Ref berbeda: {original}")

    markers = re.findall(r"#\d+|☆", prefix)
    marker = " ".join(markers)

    qty_match = re.search(
        r"(\(\s*\d+(?:\.\d+)?\s*\)|\d+(?:\.\d+)?)\s*$",
        suffix
    )
    if not qty_match:
        raise ValueError(f"Kuantitas tidak terbaca: {original}")

    qty = qty_match.group(1)
    name = suffix[:qty_match.start()].strip()
    if not name:
        raise ValueError(f"Nama part kosong: {original}")

    return {
        "machine_id": MACHINE_ID,
        "source_document_id": SOURCE_DOCUMENT_ID,
        "pdf_page": int(row["pdf_page"]),
        "catalog_ref": ref,
        "marker": marker,
        "part_number": pn,
        "part_name": name,
        "quantity_raw": qty,
        "catalog_line_original": original,
        "source_url": None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Backup dan tulis data ke database"
    )
    args = parser.parse_args()

    if not DB.exists():
        raise SystemExit(f"Database tidak ditemukan: {DB}")
    if not CSV_FILE.exists():
        raise SystemExit(f"CSV staging tidak ditemukan: {CSV_FILE}")

    with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
        source_rows = list(csv.DictReader(f))

    rows = [parse_row(r) for r in source_rows]

    if len(rows) != 691:
        raise SystemExit(f"Jumlah baris bukan 691: {len(rows)}")

    if {r["pdf_page"] for r in rows} != set(PAGES):
        raise SystemExit("Daftar halaman tidak sesuai dengan target.")

    keys = [
        (r["machine_id"], r["pdf_page"], r["catalog_ref"])
        for r in rows
    ]
    if len(keys) != len(set(keys)):
        raise SystemExit("Ada Ref duplikat dalam halaman yang sama.")

    print("=== PREVIEW IMPOR KATALOG JUKI ===")
    print("Database:", DB)
    print("Machine ID:", MACHINE_ID)
    print("Source document ID:", SOURCE_DOCUMENT_ID)
    print("Jumlah baris tervalidasi:", len(rows))
    print("Jumlah halaman:", len(PAGES))
    print("\nJumlah baris per halaman:")
    for page in PAGES:
        count = sum(r["pdf_page"] == page for r in rows)
        print(f"  PDF {page:02}: {count}")

    print("\nContoh data yang akan diimpor:")
    for r in rows[:5]:
        print(
            f'  PDF {r["pdf_page"]} | Ref {r["catalog_ref"]} | '
            f'{r["part_number"]} | {r["part_name"]} | '
            f'Qty {r["quantity_raw"]}'
        )

    with sqlite3.connect(DB) as con:
        tables = {
            x[0] for x in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "machines" not in tables or "documents" not in tables:
            raise SystemExit("Tabel mesin atau dokumen sumber tidak ditemukan.")

        machine = con.execute(
            "SELECT id FROM machines WHERE id=?", (MACHINE_ID,)
        ).fetchone()
        source = con.execute(
            "SELECT id FROM documents WHERE id=?",
            (SOURCE_DOCUMENT_ID,)
        ).fetchone()

        if not machine or not source:
            raise SystemExit("Machine ID atau source document ID tidak valid.")

        if "catalog_occurrences" in tables:
            print("\nTabel catalog_occurrences sudah ada.")
            existing = con.execute(
                "SELECT COUNT(*) FROM catalog_occurrences "
                "WHERE machine_id=? AND pdf_page IN "
                "(6,8,10,12,14,16,20,22,23,28,30,32)",
                (MACHINE_ID,)
            ).fetchone()[0]
            print("Baris target yang sudah ada:", existing)

    if not args.apply:
        print("\nMODE PREVIEW: database tidak diubah.")
        print("Jika preview benar, jalankan: python impor_katalog_juki.py --apply")
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"garment_before_juki_occurrences_{stamp}.db"

    # Backup SQLite konsisten sebelum perubahan.
    src = sqlite3.connect(DB)
    try:
        dst = sqlite3.connect(backup)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()

    sql = """
    CREATE TABLE IF NOT EXISTS catalog_occurrences (
        id INTEGER PRIMARY KEY,
        machine_id INTEGER NOT NULL,
        source_document_id INTEGER NOT NULL,
        pdf_page INTEGER NOT NULL,
        catalog_ref TEXT NOT NULL,
        marker TEXT NOT NULL DEFAULT '',
        part_number TEXT NOT NULL,
        part_name TEXT NOT NULL,
        quantity_raw TEXT NOT NULL,
        catalog_line_original TEXT NOT NULL,
        source_url TEXT,
        UNIQUE(machine_id, pdf_page, catalog_ref),
        FOREIGN KEY(machine_id) REFERENCES machines(id),
        FOREIGN KEY(source_document_id) REFERENCES documents(id)
    )
    """

    upsert = """
    INSERT INTO catalog_occurrences (
        machine_id, source_document_id, pdf_page, catalog_ref,
        marker, part_number, part_name, quantity_raw,
        catalog_line_original, source_url
    ) VALUES (
        :machine_id, :source_document_id, :pdf_page, :catalog_ref,
        :marker, :part_number, :part_name, :quantity_raw,
        :catalog_line_original, :source_url
    )
    ON CONFLICT(machine_id, pdf_page, catalog_ref) DO UPDATE SET
        source_document_id=excluded.source_document_id,
        marker=excluded.marker,
        part_number=excluded.part_number,
        part_name=excluded.part_name,
        quantity_raw=excluded.quantity_raw,
        catalog_line_original=excluded.catalog_line_original,
        source_url=excluded.source_url
    """

    con = sqlite3.connect(DB)
    try:
        con.execute("PRAGMA foreign_keys=ON")
        with con:
            con.execute(sql)
            con.executemany(upsert, rows)

            total = con.execute(
                "SELECT COUNT(*) FROM catalog_occurrences "
                "WHERE machine_id=? AND pdf_page IN "
                "(6,8,10,12,14,16,20,22,23,28,30,32)",
                (MACHINE_ID,)
            ).fetchone()[0]

            if total != 691:
                raise RuntimeError(
                    f"Verifikasi gagal: ditemukan {total}, bukan 691."
                )

            bad = con.execute("""
                SELECT pdf_page, COUNT(*)
                FROM catalog_occurrences
                WHERE machine_id=?
                  AND pdf_page IN (6,8,10,12,14,16,20,22,23,28,30,32)
                GROUP BY pdf_page
            """, (MACHINE_ID,)).fetchall()

        print("\nIMPOR BERHASIL.")
        print("Backup:", backup)
        print("Total kemunculan terverifikasi:", total)
        print("Ringkasan halaman:", bad)
    except Exception:
        con.rollback()
        print("\nIMPOR GAGAL; transaksi dibatalkan.")
        print("Backup tetap tersedia:", backup)
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
