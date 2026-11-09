import sqlite3
from pathlib import Path
from datetime import datetime
import sys

DB = Path("database/garment.db")

TARGETS = {
    215: ("10007", "Tekanan udara pneumatik tidak mencukupi"),
    216: ("10004", "Sistem vacuum tidak bekerja dengan baik"),
}

SOURCE = (
    "MAICA UAM 04 Use and Maintenance Manual, versi 07/15, "
    "bab 11 Troubleshooting, halaman 49. "
    "Salinan PDF di-host oleh Silmaq."
)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        sys.exit("GAGAL: Database tidak sehat.")

    for row_id, (code, expected_problem) in TARGETS.items():
        row = con.execute("""
            SELECT t.id, t.problem, t.code, m.model, b.name AS brand
            FROM troubleshooting t
            JOIN machines m ON m.id = t.machine_id
            JOIN brands b ON b.id = m.brand_id
            WHERE t.id = ?
        """, (row_id,)).fetchone()

        if not row:
            sys.exit(f"GAGAL: ID {row_id} tidak ditemukan.")

        if row["model"] != "UAM-04" or row["brand"].upper() != "MAICA":
            sys.exit(f"GAGAL: ID {row_id} bukan MAICA UAM-04.")

        if row["problem"] != expected_problem:
            sys.exit(f"GAGAL: Masalah ID {row_id} tidak cocok.")

        if row["code"]:
            sys.exit(f"DIBATALKAN: ID {row_id} sudah memiliki kode.")

    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)

    backup = backup_dir / (
        "garment-before-MAICA-codes-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".db"
    )

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()

    check = sqlite3.connect(backup)
    result = check.execute("PRAGMA integrity_check").fetchone()[0]
    check.close()

    if result != "ok":
        sys.exit("GAGAL: Backup tidak lolos pemeriksaan.")

    with con:
        for row_id, (code, _) in TARGETS.items():
            con.execute("""
                UPDATE troubleshooting
                SET code = ?, source = ?
                WHERE id = ? AND code IS NULL
            """, (code, SOURCE, row_id))

    print("BERHASIL")
    print("Backup:", backup)

    for row_id in TARGETS:
        row = con.execute("""
            SELECT id, problem, code, source
            FROM troubleshooting WHERE id = ?
        """, (row_id,)).fetchone()
        print(f'\nID {row["id"]}: {row["problem"]}')
        print("Kode:", row["code"])

    print("\nIntegritas:", con.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0])

except Exception as e:
    con.rollback()
    sys.exit("GAGAL: " + str(e))
finally:
    con.close()
