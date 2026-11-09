import csv
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
CSV = Path("audit-kelengkapan/draf_perbaikan_isi_ddl8700_v2.csv")
TARGETS = {1, 2, 3, 4, 247, 248, 249, 250}

def stop(msg):
    raise RuntimeError(msg)

if not DB.is_file() or not CSV.is_file():
    stop("Database atau CSV tidak ditemukan.")

with CSV.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    headers = set(reader.fieldnames or [])
    rows = list(reader)

required = {
    "id", "machine_id", "problem",
    "possible_cause_lama", "possible_cause_usulan",
    "solution_lama", "solution_usulan",
    "safety_notes_lama", "safety_notes_usulan",
    "source_tidak_diubah", "status"
}
if not required.issubset(headers):
    stop("Header CSV tidak sesuai. Kolom hilang: " +
         ", ".join(sorted(required - headers)))

draft = {}
for r in rows:
    try:
        rid = int(r["id"])
    except (ValueError, TypeError):
        stop(f"ID CSV tidak valid: {r.get('id')!r}")
    if rid in draft:
        stop(f"ID duplikat di CSV: {rid}")
    draft[rid] = r

if set(draft) != TARGETS:
    stop(
        f"ID CSV tidak sesuai. Kurang: {sorted(TARGETS-set(draft))}; "
        f"tambahan: {sorted(set(draft)-TARGETS)}"
    )

new_fields = {
    "possible_cause": "possible_cause_usulan",
    "solution": "solution_usulan",
    "safety_notes": "safety_notes_usulan",
}
old_fields = {
    "problem": "problem",
    "possible_cause": "possible_cause_lama",
    "solution": "solution_lama",
    "safety_notes": "safety_notes_lama",
    "source": "source_tidak_diubah",
}

for rid, r in draft.items():
    for field in new_fields.values():
        if not r[field].strip():
            stop(f"Usulan kosong: ID {rid}, kolom {field}")
    if not r["source_tidak_diubah"].strip():
        stop(f"Nilai source kosong di CSV: ID {rid}")

con = sqlite3.connect(str(DB), timeout=30)
backup_path = None

try:
    con.execute("PRAGMA busy_timeout=30000")

    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        stop("Integritas database awal tidak lolos.")

    info = list(con.execute("PRAGMA table_info(troubleshooting)"))
    cols = [x[1] for x in info]
    required_db = {
        "id", "machine_id", "problem", "possible_cause",
        "solution", "safety_notes", "source"
    }
    if not required_db.issubset(cols):
        stop("Struktur tabel troubleshooting tidak sesuai.")

    # Simpan semua kolom untuk pemeriksaan sebelum/sesudah.
    def get_all(rid):
        return con.execute(
            "SELECT * FROM troubleshooting WHERE id=?", (rid,)
        ).fetchone()

    def check_expected_old():
        for rid in sorted(TARGETS):
            r = draft[rid]
            current = get_all(rid)
            if current is None:
                stop(f"ID {rid} tidak ditemukan.")

            d = dict(zip(cols, current))
            if d["machine_id"] != int(r["machine_id"]):
                stop(f"machine_id tidak cocok pada ID {rid}.")
            if d["machine_id"] != 3:
                stop(f"ID {rid} bukan entri mesin yang diharapkan.")

            for dbcol, csvcol in old_fields.items():
                if d[dbcol] != r[csvcol]:
                    stop(
                        f"Data lama berbeda: ID {rid}, kolom {dbcol}. "
                        "Penerapan dibatalkan."
                    )

    # Pemeriksaan sebelum membuat backup.
    check_expected_old()

    backup_path = DB.with_name(
        f"{DB.name}.bak-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    if backup_path.exists():
        stop(f"Backup sudah ada: {backup_path}")

    backup = sqlite3.connect(str(backup_path))
    try:
        con.backup(backup)
    finally:
        backup.close()

    check = sqlite3.connect(
        f"file:{backup_path.resolve()}?mode=ro", uri=True
    )
    try:
        if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            stop("Backup tidak lolos pemeriksaan integritas.")
    finally:
        check.close()

    con.execute("BEGIN IMMEDIATE")
    check_expected_old()

    before = {rid: get_all(rid) for rid in sorted(TARGETS)}

    for rid in sorted(TARGETS):
        r = draft[rid]
        con.execute(
            """UPDATE troubleshooting
               SET possible_cause=?, solution=?, safety_notes=?
               WHERE id=? AND machine_id=3""",
            (
                r["possible_cause_usulan"],
                r["solution_usulan"],
                r["safety_notes_usulan"],
                rid,
            ),
        )
        if con.execute("SELECT changes()").fetchone()[0] != 1:
            stop(f"Jumlah baris yang diubah tidak tepat untuk ID {rid}.")

    # Pastikan isi usulan tepat dan seluruh kolom lain tidak berubah.
    allowed = set(new_fields)
    for rid in sorted(TARGETS):
        after = get_all(rid)
        old_map = dict(zip(cols, before[rid]))
        new_map = dict(zip(cols, after))
        r = draft[rid]

        for dbcol, csvcol in new_fields.items():
            if new_map[dbcol] != r[csvcol]:
                stop(f"Verifikasi gagal: ID {rid}, kolom {dbcol}.")

        for col in cols:
            if col not in allowed and new_map[col] != old_map[col]:
                stop(f"Kolom di luar izin berubah: ID {rid}, kolom {col}.")

    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        stop("Integritas setelah update tidak lolos.")

    con.execute("COMMIT")

    print("PENERAPAN V2: BERHASIL")
    print("ID:", ", ".join(map(str, sorted(TARGETS))))
    print("Kolom diubah: possible_cause, solution, safety_notes")
    print("Kolom source dan semua kolom lain: tidak berubah")
    print("Verifikasi hasil: LULUS")
    print("Integrity check: ok")
    print("Backup:", backup_path)

except Exception as e:
    if con.in_transaction:
        con.execute("ROLLBACK")
    print("PENERAPAN DIBATALKAN:", str(e))
    if backup_path and backup_path.exists():
        print("Backup yang dibuat:", backup_path)
    sys.exit(1)
finally:
    con.close()
