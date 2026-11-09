import csv
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

db = Path("database/garment.db")
csv_path = Path("audit-kelengkapan/draf_brother_bas311hn_03s.csv")
backup_dir = Path("audit-kelengkapan/backup")

if not db.is_file() or not csv_path.is_file():
    raise SystemExit("BATAL: database atau CSV tidak ditemukan.")

with csv_path.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

required = {
    "machine_id", "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source", "code"
}
if not rows or not required.issubset(rows[0].keys()):
    raise SystemExit("BATAL: kolom CSV tidak sesuai.")

codes = [r["code"].strip() for r in rows if r["code"].strip()]
if len(rows) != 93 or len(codes) != 74 or len(set(codes)) != 74:
    raise SystemExit("BATAL: jumlah baris/kode tidak sesuai hasil audit.")
if any(r["machine_id"].strip() != "227" for r in rows):
    raise SystemExit("BATAL: ditemukan machine_id selain 227.")
if any(not r["problem"].strip() or not r["source"].strip()
       for r in rows):
    raise SystemExit("BATAL: problem/source kosong.")
if any("DRAF_PERLU_VERIFIKASI_TEKNIS" not in r["source"]
       for r in rows):
    raise SystemExit("BATAL: ada baris tanpa penanda draf.")

backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = backup_dir / f"garment_sebelum_impor_brother227_{stamp}.db"

con = sqlite3.connect(db, timeout=30)
try:
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("BEGIN IMMEDIATE")

    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=227"
    ).fetchone()
    if not machine or machine[1] != "BAS-311HN-03S":
        raise RuntimeError("ID 227 tidak cocok dengan BAS-311HN-03S.")

    existing = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=227"
    ).fetchone()[0]
    if existing:
        raise RuntimeError(
            f"ID 227 sudah punya {existing} baris; impor dibatalkan."
        )

    cols = {r[1] for r in con.execute(
        "PRAGMA table_info(troubleshooting)"
    )}
    needed = required
    if not needed.issubset(cols):
        raise RuntimeError("Skema tabel tidak cocok dengan kolom CSV.")

    # Pastikan backup konsisten dan selesai sebelum perubahan data.
    con.rollback()
    con.close()
    con = None
    shutil.copy2(db, backup)

    # Buka ulang setelah backup, lalu periksa kondisi sebelum impor.
    con = sqlite3.connect(db, timeout=30)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("BEGIN IMMEDIATE")

    if con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=227"
    ).fetchone()[0]:
        raise RuntimeError("Data ID 227 berubah; impor dibatalkan.")

    before = con.execute(
        "SELECT COUNT(*) FROM troubleshooting"
    ).fetchone()[0]

    payload = [
        (
            227,
            r["problem"].strip(),
            r["symptoms"].strip(),
            r["possible_cause"].strip(),
            r["solution"].strip(),
            r["safety_notes"].strip(),
            r["source"].strip(),
            r["code"].strip(),
        )
        for r in rows
    ]

    con.executemany("""
        INSERT INTO troubleshooting
        (machine_id, problem, symptoms, possible_cause, solution,
         safety_notes, source, code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, payload)

    inserted = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=227"
    ).fetchone()[0]
    total = con.execute(
        "SELECT COUNT(*) FROM troubleshooting"
    ).fetchone()[0]
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]

    if inserted != 93 or total != before + 93 or integrity != "ok":
        raise RuntimeError(
            f"Validasi gagal: ID227={inserted}, total={total}, "
            f"integrity={integrity}"
        )

    con.commit()
    print("IMPOR BERHASIL")
    print("Mesin:", machine[1], "(ID 227)")
    print("Baris diimpor:", inserted)
    print("Kode unik:", len(set(codes)))
    print("Baris bertanda draf:", con.execute(
        """SELECT COUNT(*) FROM troubleshooting
           WHERE machine_id=227
           AND source LIKE '%DRAF_PERLU_VERIFIKASI_TEKNIS%'"""
    ).fetchone()[0])
    print("Total troubleshooting sebelum:", before)
    print("Total troubleshooting sesudah:", total)
    print("Integritas:", integrity)
    print("Backup:", backup)

except Exception as e:
    if con is not None:
        con.rollback()
    print("IMPOR DIBATALKAN:", e)
    print("Jika backup sudah dibuat, file tetap tersedia di:", backup)
    raise SystemExit(1)
finally:
    if con is not None:
        con.close()
