import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db").resolve()
BACKUP = DB.with_name(
    DB.name + ".backup-before-pegasus-parts-urls-"
    + datetime.now().strftime("%Y%m%d-%H%M%S")
)

# document_id: (model, URL lama, URL baru)
CHANGES = {
    477: (
        "M922",
        "https://www.pegasus.co.jp/webcatalog/series.php?catalogid=ses00002&filter_lang=en&lang=en",
        "https://www.pegasus.co.jp/webcatalog/view.php?itemcd=9B6101000009&rev=00",
    ),
    473: (
        "M932",
        "https://www.pegasus.co.jp/webcatalog/series.php?catalogid=ses00002&filter_lang=en&lang=en",
        "https://www.pegasus.co.jp/webcatalog/view.php?itemcd=9B6096000009&rev=00",
    ),
    475: (
        "M952",
        "https://www.pegasus.co.jp/webcatalog/series.php?catalogid=ses00002&filter_lang=en&lang=en",
        "https://www.pegasus.co.jp/webcatalog/view.php?itemcd=9B6096000009&rev=00",
    ),
    541: (
        "MX3200",
        "https://www.pegasus.co.jp/webcatalog/index.php?lang=en",
        "https://www.pegasus.co.jp/webcatalog/view.php?itemcd=9B9002000019&rev=01",
    ),
    543: (
        "MX5200",
        "https://www.pegasus.co.jp/webcatalog/index.php?lang=en",
        "https://www.pegasus.co.jp/webcatalog/view.php?itemcd=9B9002000019&rev=01",
    ),
    483: (
        "W3664P",
        "https://www.pegasus.co.jp/webcatalog/series.php?catalogid=ses00014&filter_lang=all",
        "https://www.pegasus.co.jp/webcatalog/view.php?itemcd=9B6045000009&rev=01",
    ),
}

con = None

try:
    if not DB.is_file():
        raise RuntimeError(f"Database tidak ditemukan: {DB}")

    con = sqlite3.connect(DB, timeout=30)
    con.execute("PRAGMA busy_timeout = 30000")

    # Validasi SEMUA record sebelum membuat perubahan.
    print("===== VALIDASI SEBELUM MIGRASI =====")
    for doc_id, (expected_model, old_url, new_url) in CHANGES.items():
        row = con.execute("""
            SELECT m.model, d.document_type, d.source_url, b.name
            FROM documents d
            JOIN machines m ON m.id = d.machine_id
            JOIN brands b ON b.id = m.brand_id
            WHERE d.id = ?
        """, (doc_id,)).fetchone()

        if row is None:
            raise RuntimeError(f"Document ID {doc_id} tidak ditemukan")

        model, doc_type, source_url, brand = row

        if "PEGASUS" not in brand.upper():
            raise RuntimeError(
                f"ID {doc_id}: merek tidak sesuai: {brand}"
            )
        if model.upper() != expected_model.upper():
            raise RuntimeError(
                f"ID {doc_id}: model berubah: {model}"
            )
        if doc_type != "Parts List":
            raise RuntimeError(
                f"ID {doc_id}: jenis dokumen berubah: {doc_type}"
            )
        if source_url != old_url:
            raise RuntimeError(
                f"ID {doc_id}: URL lama tidak cocok.\n"
                f"  Aktual: {source_url}\n"
                f"  Harap: {old_url}"
            )

        print(f"LOLOS ID {doc_id}: {model} / {doc_type}")

    # Backup konsisten menggunakan SQLite Backup API.
    if BACKUP.exists():
        raise RuntimeError(f"File backup sudah ada: {BACKUP}")

    backup_con = sqlite3.connect(BACKUP)
    try:
        con.backup(backup_con)
        check = backup_con.execute("PRAGMA integrity_check").fetchone()[0]
        if check != "ok":
            raise RuntimeError(f"Backup gagal pemeriksaan: {check}")
    finally:
        backup_con.close()

    print("\nBackup terverifikasi:", BACKUP)

    # Perubahan hanya pada source_url dan hanya untuk enam ID ini.
    con.execute("BEGIN IMMEDIATE")

    for doc_id, (model, old_url, new_url) in CHANGES.items():
        cur = con.execute("""
            UPDATE documents
            SET source_url = ?
            WHERE id = ?
              AND document_type = 'Parts List'
              AND source_url = ?
              AND machine_id = (
                  SELECT m.id
                  FROM machines m
                  JOIN brands b ON b.id = m.brand_id
                  WHERE m.model = ?
                    AND UPPER(b.name) LIKE '%PEGASUS%'
              )
        """, (new_url, doc_id, old_url, model))

        if cur.rowcount != 1:
            raise RuntimeError(
                f"Update ID {doc_id} tidak tepat satu baris"
            )

    # Verifikasi perubahan sebelum commit.
    print("\n===== VERIFIKASI PERUBAHAN =====")
    for doc_id, (expected_model, old_url, new_url) in CHANGES.items():
        row = con.execute("""
            SELECT m.model, d.document_type, d.source_url
            FROM documents d
            JOIN machines m ON m.id = d.machine_id
            WHERE d.id = ?
        """, (doc_id,)).fetchone()

        if row != (expected_model, "Parts List", new_url):
            raise RuntimeError(
                f"Verifikasi gagal ID {doc_id}: {row}"
            )

        print(f"OK ID {doc_id}: {row[0]} -> URL katalog baru")

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"Integrity check gagal: {integrity}")

    con.commit()

    print("\nHASIL: MIGRASI BERHASIL")
    print("Jumlah record diperbarui:", len(CHANGES))
    print("SQLite integrity_check:", integrity)
    print("Backup:", BACKUP)

except Exception as e:
    if con is not None and con.in_transaction:
        con.rollback()
    print("\nMIGRASI DIBATALKAN / ROLLBACK")
    print(type(e).__name__ + ":", e)
    print("Database tidak menyimpan perubahan transaksi ini.")
    raise SystemExit(1)

finally:
    if con is not None:
        con.close()
