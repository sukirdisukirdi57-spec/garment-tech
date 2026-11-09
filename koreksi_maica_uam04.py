import sqlite3
from pathlib import Path
from datetime import datetime
import sys

DB = Path("database/garment.db")
ROW_ID = 218

if not DB.exists():
    sys.exit("GAGAL: Database tidak ditemukan.")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        sys.exit(f"GAGAL: Integritas database: {integrity}")

    row = con.execute("""
        SELECT t.id, m.model, t.problem, t.solution, t.source
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        JOIN brands b ON b.id = m.brand_id
        WHERE t.id = ? AND UPPER(b.name) = 'MAICA'
    """, (ROW_ID,)).fetchone()

    if not row or row["model"] != "UAM-04":
        sys.exit("GAGAL: ID 218 bukan data MAICA UAM-04.")

    if "180 mm" not in (row["solution"] or ""):
        sys.exit("DIBATALKAN: Klaim 180 mm tidak ditemukan. Tidak ada perubahan.")

    print("Data ditemukan:")
    print("ID:", row["id"])
    print("Model:", row["model"])
    print("Masalah:", row["problem"])
    print("Solusi lama:", row["solution"])

    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / (
        "garment-before-MAICA-UAM04-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".db"
    )

    backup_con = sqlite3.connect(backup)
    con.backup(backup_con)
    backup_con.close()

    check = sqlite3.connect(backup)
    backup_integrity = check.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]
    check.close()

    if backup_integrity != "ok":
        sys.exit("GAGAL: Backup tidak lolos pemeriksaan integritas.")

    new_solution = (
        "Periksa program dan parameter ukuran, pastikan lebar "
        "sleeve placket berada dalam rentang 15–30 mm, kemudian "
        "lakukan sampel uji. Panjang sleeve placket dapat "
        "disesuaikan menggunakan jig yang sesuai. Katalog resmi "
        "tidak mencantumkan batas panjang maksimum."
    )

    new_source = (
        "Katalog resmi MAICA UAM-04 (lebar 15–30 mm dan panjang "
        "dapat disesuaikan dengan jig); panduan pemeriksaan umum. "
        "Batas panjang maksimum tidak dicantumkan."
    )

    with con:
        cur = con.execute("""
            UPDATE troubleshooting
            SET solution = ?, source = ?
            WHERE id = ? AND solution = ?
        """, (
            new_solution,
            new_source,
            ROW_ID,
            row["solution"]
        ))

        if cur.rowcount != 1:
            raise RuntimeError("Jumlah baris berubah; koreksi dibatalkan.")

    print("\nKOREKSI BERHASIL")
    print("Backup:", backup)
    print("Solusi baru:", new_solution)
    print("Source baru:", new_source)
    print("Integritas database:",
          con.execute("PRAGMA integrity_check").fetchone()[0])

except Exception as e:
    con.rollback()
    sys.exit(f"PROSES GAGAL: {e}")
finally:
    con.close()
