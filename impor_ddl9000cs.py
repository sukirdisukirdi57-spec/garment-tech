import csv
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

db_path = Path("database/garment.db")
csv_path = Path("audit-kelengkapan/draf_ddl9000cs_audit2.csv")
backup_dir = Path("audit-kelengkapan/backup")
machine_id = 17
expected_model = "DDL-9000CS"
draft_status = "DRAF_PERLU_VERIFIKASI_TEKNIS"

if not db_path.exists() or not csv_path.exists():
    raise SystemExit("BATAL: database atau CSV tidak ditemukan.")

with csv_path.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

if len(rows) != 43:
    raise SystemExit(f"BATAL: jumlah baris bukan 43 ({len(rows)}).")

codes = [r["code"].strip() for r in rows]
if any(not c for c in codes) or len(set(codes)) != len(codes):
    raise SystemExit("BATAL: kode kosong atau duplikat.")

required = [
    "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source", "review_status"
]
for i, r in enumerate(rows, 1):
    if any(not (r.get(k) or "").strip() for k in required):
        raise SystemExit(f"BATAL: kolom wajib kosong pada baris {i}.")
    if r["review_status"].strip() != draft_status:
        raise SystemExit(f"BATAL: status draf tidak sesuai pada baris {i}.")
    if int(r["target_machine_id"]) != machine_id:
        raise SystemExit(f"BATAL: target machine ID salah pada baris {i}.")
    if r["target_model"].strip() != expected_model:
        raise SystemExit(f"BATAL: model target salah pada baris {i}.")

con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

try:
    machine = con.execute(
        "SELECT model FROM machines WHERE id = ?", (machine_id,)
    ).fetchone()

    if not machine or machine["model"] != expected_model:
        raise RuntimeError("Model mesin di database tidak cocok.")

    existing = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
        (machine_id,)
    ).fetchone()[0]

    if existing != 0:
        raise RuntimeError(
            f"Mesin ID {machine_id} sudah punya {existing} baris; impor dibatalkan."
        )

    columns = {
        r["name"] for r in con.execute("PRAGMA table_info(troubleshooting)")
    }
    needed = {
        "machine_id", "problem", "symptoms", "possible_cause",
        "solution", "safety_notes", "source", "code"
    }
    if not needed.issubset(columns):
        raise RuntimeError("Struktur tabel troubleshooting tidak sesuai.")

    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"garment_sebelum_impor_ddl9000cs_{stamp}.db"

    # Backup database sebelum perubahan.
    backup = sqlite3.connect(backup_path)
    con.backup(backup)
    backup.close()

    con.execute("BEGIN IMMEDIATE")

    for r in rows:
        source = r["source"].strip()
        marker = f"[{draft_status}]"
        if marker not in source:
            source = f"{source} | {marker}"

        con.execute("""
            INSERT INTO troubleshooting
            (machine_id, problem, symptoms, possible_cause,
             solution, safety_notes, source, code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            machine_id,
            r["problem"].strip(),
            r["symptoms"].strip(),
            r["possible_cause"].strip(),
            r["solution"].strip(),
            r["safety_notes"].strip(),
            source,
            r["code"].strip()
        ))

    actual = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = ?",
        (machine_id,)
    ).fetchone()[0]

    imported_codes = {
        r["code"] for r in con.execute(
            "SELECT code FROM troubleshooting WHERE machine_id = ?",
            (machine_id,)
        )
    }

    if actual != 43 or imported_codes != set(codes):
        raise RuntimeError("Validasi pasca-impor gagal; perubahan dibatalkan.")

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"Integritas database gagal: {integrity}")

    con.commit()

    print("IMpor BERHASIL")
    print("Mesin:", machine_id, expected_model)
    print("Baris terimpor:", actual)
    print("Kode unik:", len(imported_codes))
    print("Status:", draft_status, "(ditandai pada source)")
    print("Integritas database:", integrity)
    print("Backup:", backup_path)

except Exception as e:
    con.rollback()
    print("IMpor DIBATALKAN:", e)
    print("Jika backup telah dibuat, file backup tetap tersedia.")
    raise
finally:
    con.close()
