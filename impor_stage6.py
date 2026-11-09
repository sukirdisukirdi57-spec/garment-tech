import csv
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
CSV_FILE = Path("tmp/lbh1790an/proposal_error_codes_stage6.csv")
TABLE = "troubleshooting"

EXPECTED = [
    "E905", "E907", "E908", "E909", "E910", "E911",
    "E915", "E916", "E918", "E943", "E946", "E999"
]
FIELDS = [
    "machine_id", "code", "problem", "symptoms",
    "possible_cause", "solution", "safety_notes", "source"
]
EXPECTED_SOURCE = (
    "JUKI LBH-1790AN/1795AN Instruction Manual, "
    "VIII. Error Code List, hlm. cetak 79"
)

def fail(message):
    raise RuntimeError(message)

def get_counts(con):
    total = con.execute(
        f"SELECT COUNT(*) FROM {TABLE} WHERE machine_id=6"
    ).fetchone()[0]
    coded = con.execute(
        f"""SELECT COUNT(*) FROM {TABLE}
            WHERE machine_id=6 AND code IS NOT NULL
            AND TRIM(code) != ''"""
    ).fetchone()[0]
    uncoded = total - coded
    return total, coded, uncoded

def integrity(con):
    return con.execute("PRAGMA integrity_check").fetchone()[0]

def main():
    if not DB.is_file() or not CSV_FILE.is_file():
        fail("Database atau CSV proposal tidak ditemukan.")

    # Validasi CSV sebelum menyentuh database.
    with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            fail(f"Kolom CSV tidak sesuai: {reader.fieldnames}")
        rows = list(reader)

    codes = [r["code"].strip() for r in rows]
    if len(rows) != 12 or len(set(codes)) != 12:
        fail("CSV harus berisi tepat 12 kode unik.")
    if set(codes) != set(EXPECTED):
        fail("Daftar kode CSV tidak sesuai dengan Stage 6.")

    for i, row in enumerate(rows, start=2):
        if any(not row.get(k, "").strip() for k in FIELDS):
            fail(f"Ada kolom kosong pada baris CSV {i}.")
        if row["machine_id"].strip() != "6":
            fail(f"machine_id salah pada baris CSV {i}.")
        if row["source"].strip() != EXPECTED_SOURCE:
            fail(f"Sumber tidak sesuai pada baris CSV {i}.")

    # Hindari membuka database melalui symlink yang tidak diharapkan.
    if DB.is_symlink():
        fail("Path database adalah symlink; pemeriksaan manual diperlukan.")

    con = sqlite3.connect(str(DB), timeout=30)
    backup_path = None
    committed = False

    try:
        con.execute("PRAGMA busy_timeout=30000")

        # Pastikan database berada dalam kondisi awal yang disepakati.
        if integrity(con) != "ok":
            fail("Integritas database sebelum impor bukan 'ok'.")

        before = get_counts(con)
        if before != (73, 65, 8):
            fail(f"Kondisi awal berubah: total/berkode/tanpa kode={before}")

        columns = {
            row[1] for row in con.execute(f"PRAGMA table_info({TABLE})")
        }
        required = set(FIELDS)
        if not required.issubset(columns):
            fail(f"Kolom tabel kurang: {sorted(required - columns)}")

        # Backup konsisten memakai SQLite Backup API.
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = DB.with_name(f"garment-stage6-{stamp}.db.bak")
        if backup_path.exists():
            fail(f"File backup sudah ada: {backup_path}")

        backup_con = sqlite3.connect(str(backup_path))
        try:
            con.backup(backup_con)
        finally:
            backup_con.close()

        # Validasi backup dapat dibuka dan jumlahnya sesuai.
        check_backup = sqlite3.connect(str(backup_path))
        try:
            if integrity(check_backup) != "ok":
                fail("Integritas backup gagal.")
            if get_counts(check_backup) != (73, 65, 8):
                fail("Jumlah data pada backup tidak sesuai.")
        finally:
            check_backup.close()

        # Mulai transaksi; periksa ulang setelah memperoleh write lock.
        con.execute("BEGIN IMMEDIATE")

        if integrity(con) != "ok" or get_counts(con) != (73, 65, 8):
            fail("Kondisi database berubah sebelum transaksi.")

        existing = {
            row[0] for row in con.execute(
                f"""SELECT code FROM {TABLE}
                    WHERE machine_id=6 AND code IS NOT NULL
                    AND TRIM(code) != ''"""
            )
        }
        collisions = sorted(existing & set(codes))
        if collisions:
            fail(f"Benturan kode terdeteksi: {collisions}")

        placeholders = ", ".join("?" for _ in FIELDS)
        sql = (
            f"INSERT INTO {TABLE} ({', '.join(FIELDS)}) "
            f"VALUES ({placeholders})"
        )

        # Jangan gunakan INSERT OR IGNORE: setiap kegagalan harus terlihat.
        for row in rows:
            con.execute(sql, tuple(row[k].strip() for k in FIELDS))

        # Validasi sebelum commit agar kegagalan masih dapat di-rollback.
        after = get_counts(con)
        if after != (85, 77, 8):
            fail(f"Jumlah setelah insert tidak sesuai: {after}")

        inserted = {
            row[0] for row in con.execute(
                f"""SELECT code FROM {TABLE}
                    WHERE machine_id=6 AND code IN
                    ({', '.join('?' for _ in EXPECTED)})""",
                EXPECTED
            )
        }
        if inserted != set(EXPECTED):
            fail("Tidak semua kode Stage 6 ditemukan setelah insert.")

        if integrity(con) != "ok":
            fail("Integritas gagal sebelum commit.")

        con.commit()
        committed = True

        # Verifikasi lagi setelah commit.
        final_counts = get_counts(con)
        final_integrity = integrity(con)
        final_codes = {
            row[0] for row in con.execute(
                f"""SELECT code FROM {TABLE}
                    WHERE machine_id=6 AND code IN
                    ({', '.join('?' for _ in EXPECTED)})""",
                EXPECTED
            )
        }

        print("\n=== HASIL IMPOR STAGE 6 ===")
        print("Backup:", backup_path)
        print("Total entri mesin ID 6:", final_counts[0])
        print("Entri berkode:", final_counts[1])
        print("Entri tanpa kode:", final_counts[2])
        print("Kode Stage 6 ditemukan:", len(final_codes), "/ 12")
        print("Integritas SQLite:", final_integrity)

        if (final_counts == (85, 77, 8)
                and final_codes == set(EXPECTED)
                and final_integrity == "ok"):
            print("HASIL: IMPOR DAN VALIDASI PASCAIMPOR BERHASIL")
        else:
            print("PERINGATAN: HASIL PASCAIMPOR TIDAK SESUAI.")
            print("Backup tersedia:", backup_path)
            sys.exit(2)

    except Exception as exc:
        if con.in_transaction:
            con.rollback()
        print("IMPOR GAGAL:", exc)
        if backup_path and backup_path.exists():
            print("Backup yang dibuat:", backup_path)
        print("Transaksi yang belum commit telah dibatalkan.")
        if committed:
            print("PERHATIAN: commit sudah terjadi; periksa database dan backup.")
        sys.exit(1)
    finally:
        con.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("DIBATALKAN SEBELUM IMPOR:", exc)
        sys.exit(1)
