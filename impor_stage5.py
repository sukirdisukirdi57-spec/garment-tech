import csv
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

db = Path("database/garment.db")
proposal = Path("tmp/lbh1790an/proposal_error_codes_stage5.csv")
expected_codes = [
    "E733", "E798", "E799", "E801", "E802", "E811",
    "E813", "E820", "E901", "E902", "E903", "E904"
]
columns = [
    "machine_id", "code", "problem", "symptoms",
    "possible_cause", "solution", "safety_notes", "source"
]

def stop(message):
    raise RuntimeError(message)

if not db.is_file() or not proposal.is_file():
    stop("Database atau proposal tidak ditemukan.")

with proposal.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != columns:
        stop("Struktur kolom proposal tidak sesuai.")
    rows = list(reader)

if len(rows) != 12:
    stop(f"Jumlah baris proposal salah: {len(rows)}")
if [r["code"] for r in rows] != expected_codes:
    stop("Daftar atau urutan kode tidak sesuai.")
if len({r["code"] for r in rows}) != 12:
    stop("Ada kode duplikat dalam proposal.")
for r in rows:
    if r["machine_id"] != "6":
        stop(f"Machine ID salah pada kode {r['code']}.")
    if any(not (r.get(c) or "").strip() for c in columns):
        stop(f"Ada kolom kosong pada kode {r['code']}.")

con = sqlite3.connect(str(db), timeout=30)
backup = None

try:
    con.execute("PRAGMA busy_timeout=30000")
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        stop(f"Integritas awal gagal: {integrity}")

    schema = {
        row[1] for row in con.execute("PRAGMA table_info(troubleshooting)")
    }
    if not set(columns).issubset(schema):
        stop("Tabel troubleshooting tidak memiliki kolom yang dibutuhkan.")

    def counts():
        total = con.execute(
            "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=6"
        ).fetchone()[0]
        coded = con.execute(
            """SELECT COUNT(*) FROM troubleshooting
               WHERE machine_id=6 AND code IS NOT NULL
               AND TRIM(code) <> ''"""
        ).fetchone()[0]
        uncoded = con.execute(
            """SELECT COUNT(*) FROM troubleshooting
               WHERE machine_id=6 AND (code IS NULL OR TRIM(code)='')"""
        ).fetchone()[0]
        return total, coded, uncoded

    before = counts()
    if before != (61, 53, 8):
        stop(f"Kondisi awal tidak sesuai target: {before}")

    existing = {
        row[0] for row in con.execute(
            "SELECT code FROM troubleshooting WHERE machine_id=6 AND code IS NOT NULL"
        )
    }
    collisions = existing.intersection(expected_codes)
    if collisions:
        stop(f"Kode sudah ada, impor dibatalkan: {sorted(collisions)}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = db.with_name(f"garment-stage5-{stamp}.db.bak")
    with sqlite3.connect(str(backup)) as bcon:
        con.backup(bcon)

    if not backup.is_file() or backup.stat().st_size == 0:
        stop("Cadangan database gagal dibuat.")

    con.execute("BEGIN IMMEDIATE")
    sql = """INSERT INTO troubleshooting
        (machine_id, code, problem, symptoms, possible_cause,
         solution, safety_notes, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    for r in rows:
        con.execute(sql, tuple(r[c] for c in columns))

    after = counts()
    if after != (73, 65, 8):
        stop(f"Jumlah akhir tidak sesuai target: {after}")

    inserted = {
        row[0] for row in con.execute(
            "SELECT code FROM troubleshooting WHERE machine_id=6"
        )
    }
    if not set(expected_codes).issubset(inserted):
        stop("Verifikasi kode baru gagal.")

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        stop(f"Integritas akhir gagal: {integrity}")

    con.commit()

    print("IMPOR TAHAP 5 BERHASIL")
    print("Database:", db)
    print("Cadangan:", backup)
    print("Kode baru:", ", ".join(expected_codes))
    print("Entri mesin ID 6:", after[0])
    print("Entri berkode:", after[1])
    print("Entri tanpa kode:", after[2])
    print("Kode Tahap 5 terverifikasi:", len(expected_codes))
    print("Integritas SQLite:", integrity)

except Exception as e:
    if con.in_transaction:
        con.rollback()
    print("IMPOR DIBATALKAN / GAGAL")
    print("Alasan:", str(e))
    if backup:
        print("Cadangan yang dibuat:", backup)
    raise
finally:
    con.close()
