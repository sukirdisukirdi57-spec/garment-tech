import csv
import sqlite3
from pathlib import Path

DB = Path("database/garment.db")
CSV_FILE = Path("audit-kelengkapan/draf_ddl8000c_revisi_manual.csv")
BACKUP = Path(
    "audit-kelengkapan/backup/"
    "garment_sebelum_impor_ddl8000c_20261021_152920.db"
)

EXPECTED_COUNT = 33
TARGET_ID = 16
TARGET_MODEL = "DDL-8000C"

required = [
    "target_machine_id", "target_model", "code", "problem",
    "symptoms", "possible_cause", "solution", "safety_notes",
    "source", "review_status"
]

if not DB.is_file() or not CSV_FILE.is_file() or not BACKUP.is_file():
    raise SystemExit("BATAL: database, CSV, atau backup tidak ditemukan.")

with BACKUP.open("rb") as f:
    if not f.read(16).startswith(b"SQLite format 3"):
        raise SystemExit("BATAL: file backup bukan database SQLite.")

with CSV_FILE.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    if not set(required).issubset(reader.fieldnames or []):
        raise SystemExit("BATAL: kolom CSV tidak lengkap.")
    rows = list(reader)

if len(rows) != EXPECTED_COUNT:
    raise SystemExit(f"BATAL: jumlah baris bukan {EXPECTED_COUNT}.")

codes = [r["code"].strip() for r in rows]
if any(not code for code in codes) or len(set(codes)) != EXPECTED_COUNT:
    raise SystemExit("BATAL: kode kosong atau duplikat.")

for r in rows:
    if r["target_machine_id"].strip() != str(TARGET_ID):
        raise SystemExit("BATAL: ada target mesin selain ID 16.")
    if r["target_model"].strip() != TARGET_MODEL:
        raise SystemExit("BATAL: model target tidak cocok.")
    for col in required:
        if not (r.get(col) or "").strip():
            raise SystemExit(f"BATAL: kolom {col} kosong.")
    if r["review_status"].strip() != "DRAF_REVISI_PERLU_VERIFIKASI_TEKNIS":
        raise SystemExit("BATAL: status draf tidak sesuai.")

con = sqlite3.connect(DB)
try:
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("BEGIN IMMEDIATE")

    machine = con.execute(
        "SELECT model FROM machines WHERE id = ?", (TARGET_ID,)
    ).fetchone()
    if not machine or machine[0] != TARGET_MODEL:
        raise RuntimeError("Mesin ID 16 tidak cocok.")

    existing = {
        row[0] for row in con.execute(
            "SELECT code FROM troubleshooting WHERE machine_id = ?",
            (TARGET_ID,)
        ) if row[0] is not None
    }
    duplicates = existing.intersection(codes)
    if duplicates:
        raise RuntimeError(f"Kode sudah ada: {sorted(duplicates)}")

    for r in rows:
        source = (
            r["source"].strip()
            + " Status: DRAF; referensi manual seri resmi JUKI; "
              "varian fisik belum terkonfirmasi; "
              "perlu verifikasi teknis."
        )
        con.execute("""
            INSERT INTO troubleshooting (
                machine_id, problem, symptoms, possible_cause,
                solution, safety_notes, source, code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            TARGET_ID,
            r["problem"].strip(),
            r["symptoms"].strip(),
            r["possible_cause"].strip(),
            r["solution"].strip(),
            r["safety_notes"].strip(),
            source,
            r["code"].strip()
        ))

    inserted = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
        (TARGET_ID,)
    ).fetchone()[0]
    actual_codes = {
        row[0] for row in con.execute(
            "SELECT code FROM troubleshooting WHERE machine_id = ?",
            (TARGET_ID,)
        )
    }

    if inserted != EXPECTED_COUNT or actual_codes != set(codes):
        raise RuntimeError("Verifikasi hasil gagal; transaksi dibatalkan.")

    con.commit()
    print("IMPOR BERHASIL")
    print("Mesin:", TARGET_ID, TARGET_MODEL)
    print("Jumlah baris:", inserted)
    print("Jumlah kode unik:", len(actual_codes))
    print("Status: draf referensi manual; varian belum terkonfirmasi.")
    print("Database telah diubah untuk mesin ID 16 saja.")

except Exception as e:
    con.rollback()
    print("IMPOR DIBATALKAN; transaksi di-rollback.")
    print("Alasan:", e)
    raise SystemExit(1)
finally:
    con.close()
