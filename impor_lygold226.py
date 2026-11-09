import csv
import sqlite3
from pathlib import Path
from datetime import datetime

db = Path("database/garment.db")
csv_path = Path("audit-kelengkapan/draf_lygold_lga105e_but.csv")
backup_dir = Path("audit-kelengkapan/backup")
status = "DRAF_PERLU_VERIFIKASI_TEKNIS"

if not db.is_file() or not csv_path.is_file():
    raise SystemExit("BATAL: database atau CSV tidak ditemukan.")

required = {
    "machine_id", "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source", "code"
}

with csv_path.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    if not required.issubset(reader.fieldnames or []):
        raise SystemExit("BATAL: kolom CSV tidak sesuai.")
    rows = list(reader)

if len(rows) != 8:
    raise SystemExit(f"BATAL: seharusnya 8 baris, ditemukan {len(rows)}.")

if any(r["machine_id"].strip() != "226" for r in rows):
    raise SystemExit("BATAL: ada machine_id selain 226.")

if any(not r["problem"].strip() or not r["source"].strip()
       for r in rows):
    raise SystemExit("BATAL: problem/source kosong.")

if any(status not in r["source"] for r in rows):
    raise SystemExit("BATAL: ada baris tanpa penanda draf.")

if any(r["code"].strip() for r in rows):
    raise SystemExit("BATAL: ditemukan kode yang belum terverifikasi.")

problems = [r["problem"].strip().casefold() for r in rows]
if len(set(problems)) != 8:
    raise SystemExit("BATAL: ada masalah duplikat.")

backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = backup_dir / f"garment_sebelum_impor_lygold226_{stamp}.db"

con = None
backup_created = False

try:
    # Periksa target dan skema sebelum membuat backup.
    con = sqlite3.connect(db, timeout=30)
    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=226"
    ).fetchone()

    if not machine or machine[1] != "LGA105E-BUT":
        raise RuntimeError("ID 226 tidak cocok dengan LGA105E-BUT.")

    existing = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=226"
    ).fetchone()[0]

    if existing != 0:
        raise RuntimeError(
            f"ID 226 sudah memiliki {existing} baris; impor dibatalkan."
        )

    db_columns = {
        r[1] for r in con.execute(
            "PRAGMA table_info(troubleshooting)"
        ).fetchall()
    }
    if not required.issubset(db_columns):
        raise RuntimeError("Skema tabel tidak cocok.")

    # Backup melalui SQLite agar konsisten.
    backup_con = sqlite3.connect(backup_path)
    try:
        con.backup(backup_con)
        check = backup_con.execute("PRAGMA integrity_check").fetchone()[0]
        if check != "ok":
            raise RuntimeError(f"Integritas backup gagal: {check}")
    finally:
        backup_con.close()

    backup_created = True
    con.close()
    con = None

    # Buka kembali dan mulai transaksi impor.
    con = sqlite3.connect(db, timeout=30)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("BEGIN IMMEDIATE")

    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=226"
    ).fetchone()
    if not machine or machine[1] != "LGA105E-BUT":
        raise RuntimeError("Target mesin berubah; impor dibatalkan.")

    existing = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=226"
    ).fetchone()[0]
    if existing != 0:
        raise RuntimeError("Data ID 226 berubah; impor dibatalkan.")

    before = con.execute(
        "SELECT COUNT(*) FROM troubleshooting"
    ).fetchone()[0]

    payload = [
        (
            226,
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
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=226"
    ).fetchone()[0]

    draft_count = con.execute("""
        SELECT COUNT(*) FROM troubleshooting
        WHERE machine_id=226 AND source LIKE ?
    """, (f"%{status}%",)).fetchone()[0]

    total = con.execute(
        "SELECT COUNT(*) FROM troubleshooting"
    ).fetchone()[0]

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()

    if (inserted != 8 or draft_count != 8
            or total != before + 8
            or integrity != "ok" or fk_errors):
        raise RuntimeError(
            f"Validasi gagal: ID226={inserted}, draf={draft_count}, "
            f"total={total}, integritas={integrity}, "
            f"foreign_key_errors={len(fk_errors)}"
        )

    con.commit()

    print("IMPOR BERHASIL")
    print("Mesin:", machine[1], "(ID 226)")
    print("Baris diimpor:", inserted)
    print("Baris bertanda draf:", draft_count)
    print("Kode alarm kosong:", con.execute("""
        SELECT COUNT(*) FROM troubleshooting
        WHERE machine_id=226 AND (code IS NULL OR TRIM(code)='')
    """).fetchone()[0])
    print("Total troubleshooting sebelum:", before)
    print("Total troubleshooting sesudah:", total)
    print("Integritas:", integrity)
    print("Pemeriksaan foreign key: OK")
    print("Backup:", backup_path)
    print("Status: semua baris masih draf, perlu verifikasi teknis.")

except Exception as e:
    if con is not None:
        con.rollback()
    print("IMPOR DIBATALKAN:", e)
    if backup_created:
        print("Backup tersedia:", backup_path)
    raise SystemExit(1)
finally:
    if con is not None:
        con.close()
