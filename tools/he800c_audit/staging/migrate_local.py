import csv
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
CSV_FILE = Path(
    "tools/he800c_audit/staging/"
    "he800c_troubleshooting_revision_candidates.csv"
)
BACKUP_DIR = Path("backups")
MACHINE_ID = 102
EXPECTED = {
    672: "Benang sering putus",
    674: "Jarum patah",
    675: "Pemotongan lubang kancing tidak sempurna",
}
UNTOUCHED = (671, 673, 676)

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

if not DB.is_file() or not CSV_FILE.is_file():
    raise SystemExit("GAGAL: database atau CSV kandidat tidak ditemukan.")

with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
    candidates = list(csv.DictReader(f))

try:
    candidate_ids = [int(r["existing_id"]) for r in candidates]
except (KeyError, ValueError) as e:
    raise SystemExit(f"GAGAL: kolom CSV tidak sesuai: {e}")

if len(candidates) != 3 or set(candidate_ids) != set(EXPECTED):
    raise SystemExit(f"GAGAL: kandidat harus tepat {sorted(EXPECTED)}.")

by_id = {int(r["existing_id"]): r for r in candidates}
for row_id, old_title in EXPECTED.items():
    r = by_id[row_id]
    if int(r["machine_id"]) != MACHINE_ID:
        raise SystemExit(f"GAGAL: machine_id ID {row_id} tidak sesuai.")
    if r["status"].strip() != "KANDIDAT BELUM DISETUJUI":
        raise SystemExit(f"GAGAL: status kandidat ID {row_id} berubah.")
    for key in (
        "proposed_title", "symptoms", "possible_causes",
        "operator_actions", "technician_actions", "source",
        "manual_section", "manual_pages"
    ):
        if not r.get(key, "").strip():
            raise SystemExit(f"GAGAL: kolom {key} kosong untuk ID {row_id}.")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = BACKUP_DIR / f"garment.db.before-he800c-write-{stamp}.db"
if BACKUP.exists():
    raise SystemExit(f"GAGAL: file backup sudah ada: {BACKUP}")

con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row

try:
    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("Integritas database sumber tidak lolos.")

    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone()
    if not machine or machine["model"] != "HE-800C":
        raise RuntimeError("Identitas mesin ID 102 tidak sesuai.")

    # Backup SQLite konsisten tepat sebelum penulisan.
    backup_con = sqlite3.connect(BACKUP)
    try:
        con.backup(backup_con)
        backup_con.commit()
        result = backup_con.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"Integritas backup gagal: {result}")
    finally:
        backup_con.close()

    print("Backup pra-migrasi:", BACKUP)
    print("SHA-256 backup:", sha256(BACKUP))
    print("Integritas backup: ok")

    columns = (
        "id", "machine_id", "problem", "symptoms",
        "possible_cause", "solution", "safety_notes", "source"
    )
    select_cols = ", ".join(columns)

    # Snapshot data yang wajib tetap tidak berubah.
    untouched_before = {}
    for row_id in UNTOUCHED:
        row = con.execute(
            f"SELECT {select_cols} FROM troubleshooting "
            "WHERE id=? AND machine_id=?",
            (row_id, MACHINE_ID)
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Data yang dilindungi ID {row_id} tidak ada.")
        untouched_before[row_id] = tuple(row[c] for c in columns)

    # Pastikan judul lama masih persis seperti saat audit.
    for row_id, old_title in EXPECTED.items():
        row = con.execute(
            "SELECT problem FROM troubleshooting WHERE id=? AND machine_id=?",
            (row_id, MACHINE_ID)
        ).fetchone()
        if row is None or row["problem"] != old_title:
            raise RuntimeError(
                f"Data ID {row_id} berubah sejak simulasi. Migrasi dibatalkan."
            )

    con.execute("BEGIN IMMEDIATE")
    try:
        for row_id in sorted(EXPECTED):
            r = by_id[row_id]
            solution = (
                "Tindakan operator:\n"
                + r["operator_actions"].strip()
                + "\n\nTindakan teknisi berkualifikasi:\n"
                + r["technician_actions"].strip()
            )
            safety = (
                "Matikan sakelar dan cabut kabel daya sebelum pemeriksaan. "
                "Pekerjaan atau penyetelan bertanda * pada manual hanya "
                "untuk teknisi berkualifikasi."
            )

            cur = con.execute("""
                UPDATE troubleshooting
                SET problem=?, symptoms=?, possible_cause=?, solution=?,
                    safety_notes=?, source=?
                WHERE id=? AND machine_id=? AND problem=?
            """, (
                r["proposed_title"].strip(),
                r["symptoms"].strip(),
                r["possible_causes"].strip(),
                solution,
                safety,
                r["source"].strip(),
                row_id, MACHINE_ID, EXPECTED[row_id]
            ))

            if cur.rowcount != 1:
                raise RuntimeError(
                    f"Update ID {row_id} tidak tepat satu baris."
                )

        # Validasi isi kandidat masih di dalam transaksi.
        for row_id in sorted(EXPECTED):
            r = by_id[row_id]
            row = con.execute(
                "SELECT problem, symptoms, possible_cause, source "
                "FROM troubleshooting WHERE id=? AND machine_id=?",
                (row_id, MACHINE_ID)
            ).fetchone()
            if (
                row is None
                or row["problem"] != r["proposed_title"].strip()
                or row["symptoms"] != r["symptoms"].strip()
                or row["possible_cause"] != r["possible_causes"].strip()
                or row["source"] != r["source"].strip()
            ):
                raise RuntimeError(f"Validasi kandidat ID {row_id} gagal.")

        # Pastikan baris di luar ruang lingkup tidak berubah.
        for row_id, before in untouched_before.items():
            row = con.execute(
                f"SELECT {select_cols} FROM troubleshooting "
                "WHERE id=? AND machine_id=?",
                (row_id, MACHINE_ID)
            ).fetchone()
            if row is None or tuple(row[c] for c in columns) != before:
                raise RuntimeError(f"Data ID {row_id} berubah tanpa izin.")

        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Integritas gagal sebelum commit.")

        con.commit()

    except Exception:
        con.rollback()
        raise

    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError(
            "PERINGATAN: pemeriksaan pascacommit gagal. "
            "Jangan lanjutkan pekerjaan lain; backup pra-migrasi tersedia."
        )

    print("\nMIGRASI BERHASIL")
    print("Mesin: HE-800C (ID 102)")
    for row_id in sorted(EXPECTED):
        row = con.execute(
            "SELECT problem, source FROM troubleshooting WHERE id=?",
            (row_id,)
        ).fetchone()
        print(f"ID {row_id}: {row['problem']}")
        print(f"  Sumber: {row['source']}")

    print("ID yang tidak diubah:", ", ".join(map(str, UNTOUCHED)))
    print("Integritas database: ok")
    print("Jumlah troubleshooting HE-800C:",
          con.execute(
              "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=?",
              (MACHINE_ID,)
          ).fetchone()[0])
    print("SHA-256 database pascamigrasi:", sha256(DB))
    print("Backup pra-migrasi tetap tersedia:", BACKUP)

except Exception as e:
    if con.in_transaction:
        con.rollback()
    raise SystemExit(f"MIGRASI DIBATALKAN / GAGAL: {e}")
finally:
    con.close()
