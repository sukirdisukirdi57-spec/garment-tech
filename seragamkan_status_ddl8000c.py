import sqlite3
from pathlib import Path
from datetime import datetime

db = Path("database/garment.db")
backup_dir = Path("audit-kelengkapan/backup")
old_marker = "DRAF"
new_marker = "DRAF_PERLU_VERIFIKASI_TEKNIS"

if not db.is_file():
    raise SystemExit("BATAL: database tidak ditemukan.")

backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = backup_dir / f"garment_sebelum_seragamkan_ddl8000c_{stamp}.db"

con = sqlite3.connect(db, timeout=30)
backup_con = None

try:
    # Validasi kondisi awal.
    machine = con.execute(
        "SELECT model FROM machines WHERE id=16"
    ).fetchone()
    if not machine or machine[0] != "DDL-8000C":
        raise RuntimeError("ID 16 bukan DDL-8000C.")

    rows = con.execute("""
        SELECT id, source
        FROM troubleshooting
        WHERE machine_id=16
        ORDER BY id
    """).fetchall()

    if len(rows) != 33:
        raise RuntimeError(f"Harus ada 33 baris; ditemukan {len(rows)}.")

    if any(not source or old_marker not in source
           for _, source in rows):
        raise RuntimeError("Ada sumber yang tidak sesuai pola lama.")

    if any(new_marker in source for _, source in rows):
        raise RuntimeError("Penanda standar sudah ditemukan; batal agar aman.")

    # Backup konsisten sebelum perubahan.
    backup_con = sqlite3.connect(backup_path)
    con.backup(backup_con)
    backup_integrity = backup_con.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]
    backup_con.close()
    backup_con = None

    if backup_integrity != "ok":
        raise RuntimeError("Integritas backup tidak OK.")

    # Ubah hanya penanda status pada kolom source.
    con.execute("BEGIN IMMEDIATE")

    current_ids = con.execute("""
        SELECT id, source FROM troubleshooting
        WHERE machine_id=16 ORDER BY id
    """).fetchall()

    if current_ids != rows:
        raise RuntimeError("Data berubah setelah pemeriksaan awal.")

    for row_id, source in rows:
        updated_source = source.replace(
            old_marker, new_marker, 1
        )
        con.execute("""
            UPDATE troubleshooting
            SET source=?
            WHERE id=? AND machine_id=16
        """, (updated_source, row_id))

    updated = con.execute("""
        SELECT COUNT(*) FROM troubleshooting
        WHERE machine_id=16
          AND source LIKE ?
    """, (f"%{new_marker}%",)).fetchone()[0]

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()

    if updated != 33 or integrity != "ok" or fk_errors:
        raise RuntimeError(
            f"Validasi gagal: penanda={updated}, "
            f"integritas={integrity}, foreign_key={len(fk_errors)}"
        )

    con.commit()

    print("PERBAIKAN BERHASIL")
    print("Mesin: DDL-8000C (ID 16)")
    print("Sumber diperbarui:", updated)
    print("Isi selain penanda status: tidak diubah")
    print("Integritas:", integrity)
    print("Pemeriksaan foreign key: OK")
    print("Backup:", backup_path)

except Exception as e:
    con.rollback()
    print("PERBAIKAN DIBATALKAN:", e)
    print("Jika sudah dibuat, backup tersedia:", backup_path)
    raise SystemExit(1)
finally:
    if backup_con is not None:
        backup_con.close()
    con.close()
