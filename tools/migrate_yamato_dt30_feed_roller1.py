import argparse
import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "database" / "garment.db"
CSV_FILE = ROOT / "tmp" / "yamato-dt30" / "feed_roller_mechanism_1_staging.csv"

MACHINE_ID = 159
DOCUMENT_ID = 182
EXPECTED_ROWS = 26
EXPECTED_QUANTITY = 30
EXPECTED_URL = (
    "https://www.yamato-sewing.com/en/product/support/"
    "dt-series/dt-30-partsbook-je/"
)

FIELDS = [
    "machine_id", "source_document_id", "part_number", "part_name",
    "quantity", "catalog_ref", "diagram_page", "source_url", "notes"
]

def load_and_validate(con):
    if not DB.is_file() or not CSV_FILE.is_file():
        raise RuntimeError("Database atau CSV staging tidak ditemukan.")

    with CSV_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            raise RuntimeError(
                f"Kolom CSV tidak sesuai: {reader.fieldnames}"
            )
        rows = list(reader)

    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(f"Jumlah kandidat salah: {len(rows)}")

    if sum(int(r["quantity"]) for r in rows) != EXPECTED_QUANTITY:
        raise RuntimeError("Total kuantitas bukan 30.")

    part_numbers = [r["part_number"].strip() for r in rows]
    refs = [r["catalog_ref"].strip() for r in rows]

    if any(not p for p in part_numbers) or len(set(part_numbers)) != len(part_numbers):
        raise RuntimeError("Nomor part kosong atau duplikat.")
    if any(not r for r in refs) or len(set(refs)) != len(refs):
        raise RuntimeError("Referensi katalog kosong atau duplikat.")

    for r in rows:
        if int(r["machine_id"]) != MACHINE_ID:
            raise RuntimeError("Machine ID tidak sesuai.")
        if int(r["source_document_id"]) != DOCUMENT_ID:
            raise RuntimeError("Document ID tidak sesuai.")
        if r["source_url"].strip() != EXPECTED_URL:
            raise RuntimeError("URL sumber tidak sesuai.")
        if not r["part_name"].strip() or int(r["quantity"]) < 1:
            raise RuntimeError("Nama part kosong atau kuantitas tidak valid.")
        if int(r["diagram_page"]) < 1:
            raise RuntimeError("Halaman diagram tidak valid.")

    machine = con.execute("""
        SELECT m.id, m.model, b.name AS brand
        FROM machines m
        JOIN brands b ON b.id = m.brand_id
        WHERE m.id = ?
    """, (MACHINE_ID,)).fetchone()

    if not machine or machine[1].strip().upper() != "DT-30":
        raise RuntimeError("Identitas mesin DT-30 tidak cocok.")
    if "YAMATO" not in machine[2].upper():
        raise RuntimeError("Merek mesin bukan YAMATO.")

    doc = con.execute("""
        SELECT machine_id, document_type, title, source_url
        FROM documents WHERE id = ?
    """, (DOCUMENT_ID,)).fetchone()

    if not doc or doc[0] != MACHINE_ID:
        raise RuntimeError("Dokumen sumber tidak cocok dengan mesin.")
    if doc[1] != "Parts Book" or doc[3] != EXPECTED_URL:
        raise RuntimeError("Jenis atau URL dokumen sumber tidak cocok.")

    existing = con.execute("""
        SELECT COUNT(*) FROM parts
        WHERE machine_id = ? OR source_document_id = ?
    """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Ditemukan {existing} baris part terkait DT-30/dokumen 182; "
            "migrasi dihentikan untuk pemeriksaan manual."
        )

    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true",
        help="Tulis ke database setelah semua validasi lolos"
    )
    args = parser.parse_args()

    if not DB.is_file() or not CSV_FILE.is_file():
        raise SystemExit("Database atau CSV staging tidak ditemukan.")

    # Validasi awal dalam mode read-only.
    ro = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
    integrity = ro.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        ro.close()
        raise SystemExit(f"Integritas database gagal: {integrity}")

    try:
        rows = load_and_validate(ro)
    finally:
        ro.close()

    print("MODE:", "APPLY" if args.apply else "SIMULASI READ-ONLY")
    print("Integritas awal:", integrity)
    print("Mesin: YAMATO DT-30 | ID 159")
    print("Dokumen: Yamato DT-30 Official Parts Book | ID 182")
    print("Kandidat:", len(rows))
    print("Total kuantitas:", sum(int(r["quantity"]) for r in rows))
    print("Nomor part dan referensi katalog unik: OK")
    print("Baris terkait yang sudah ada: 0")

    for r in rows:
        print(
            f"[SIAP] Ref {r['catalog_ref']} | "
            f"Part {r['part_number']} | Qty {r['quantity']} | "
            f"{r['part_name']}"
        )

    if not args.apply:
        print("\nDatabase diubah: TIDAK")
        print("Simulasi selesai. Tinjau hasil sebelum menggunakan --apply.")
        return

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB.with_name(f"garment.db.backup-before-dt30-{stamp}")
    if backup.exists():
        raise SystemExit(f"Backup sudah ada: {backup}")

    # Buat backup sebelum transaksi penulisan.
    shutil.copy2(DB, backup)

    # Verifikasi backup sebelum menyentuh database aktif.
    check = sqlite3.connect(f"file:{backup.resolve()}?mode=ro", uri=True)
    backup_integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
    check.close()

    if backup_integrity != "ok":
        backup.unlink(missing_ok=True)
        raise SystemExit("Backup gagal verifikasi; database tidak diubah.")

    print("\nBackup terverifikasi:", backup)
    con = sqlite3.connect(DB)

    try:
        con.execute("BEGIN IMMEDIATE")

        # Validasi ulang untuk mencegah perubahan sejak simulasi.
        current_rows = load_and_validate(con)

        for r in current_rows:
            con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number, part_name,
                    quantity, catalog_ref, diagram_page, note, source_url,
                    notes, quantity_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(r["machine_id"]),
                int(r["source_document_id"]),
                r["part_number"].strip(),
                r["part_name"].strip(),
                int(r["quantity"]),
                int(r["catalog_ref"]),
                int(r["diagram_page"]),
                None,
                r["source_url"].strip(),
                r["notes"].strip(),
                r["quantity"].strip()
            ))

        count = con.execute("""
            SELECT COUNT(*) FROM parts
            WHERE machine_id = ? AND source_document_id = ?
        """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

        qty = con.execute("""
            SELECT COALESCE(SUM(quantity), 0) FROM parts
            WHERE machine_id = ? AND source_document_id = ?
        """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

        after_integrity = con.execute("PRAGMA integrity_check").fetchone()[0]

        if count != EXPECTED_ROWS:
            raise RuntimeError(f"Jumlah baris hasil salah: {count}")
        if qty != EXPECTED_QUANTITY:
            raise RuntimeError(f"Total kuantitas hasil salah: {qty}")
        if after_integrity != "ok":
            raise RuntimeError(f"Integritas setelah penulisan: {after_integrity}")

        con.commit()
        print("\nMIGRASI BERHASIL")
        print("Baris ditambahkan:", count)
        print("Total kuantitas:", qty)
        print("Integritas setelah migrasi:", after_integrity)
        print("Backup:", backup)

    except Exception:
        con.rollback()
        print("TRANSAKSI DIBATALKAN — perubahan di-rollback.")
        print("Backup tetap tersedia:", backup)
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
