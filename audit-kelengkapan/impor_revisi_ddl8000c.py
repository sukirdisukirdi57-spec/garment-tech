import re
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MATRIX = Path("audit-kelengkapan/matriks_revisi_teknis_ddl8000c.md")
BACKUP_DIR = Path("audit-kelengkapan/backup")

# Baca dan parsing matriks tanpa mengubah database.
text = MATRIX.read_text(encoding="utf-8")

pattern = re.compile(
    r"\|\s*(\d{4})\s*\|\s*([A-Z0-9_]+)\s*\|"
    r"\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|"
    r"\s*([^|]*)\|\s*([^|]*)\|\s*(\d+)\s*\|"
)

revisions = {}
for m in pattern.finditer(text):
    row_id = int(m.group(1))
    code = m.group(2).strip()
    solution = m.group(5).strip()
    safety = m.group(7).strip()

    if row_id in revisions:
        raise SystemExit(f"ABORT: ID {row_id} muncul lebih dari sekali.")
    if not solution or not safety:
        raise SystemExit(f"ABORT: solusi/keselamatan kosong untuk ID {row_id}.")

    revisions[row_id] = (code, solution, safety)

expected_ids = set(range(1382, 1415))
if set(revisions) != expected_ids:
    missing = sorted(expected_ids - set(revisions))
    extra = sorted(set(revisions) - expected_ids)
    raise SystemExit(
        f"ABORT: matriks tidak cocok. Terbaca {len(revisions)} baris; "
        f"ID hilang={missing}; ID tambahan={extra}"
    )

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = BACKUP_DIR / f"garment_sebelum_update_ddl8000c_{stamp}.db"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    current = con.execute("""
        SELECT id, machine_id, code, source, solution, safety_notes
        FROM troubleshooting
        WHERE machine_id = 16
        ORDER BY id
    """).fetchall()

    if len(current) != 33:
        raise RuntimeError(f"Database memiliki {len(current)} baris, bukan 33.")

    current_by_id = {r["id"]: r for r in current}
    if set(current_by_id) != expected_ids:
        raise RuntimeError("ID database tidak sama dengan ID target 1382–1414.")

    for row_id, (code, solution, safety) in revisions.items():
        row = current_by_id[row_id]
        if row["code"] != code:
            raise RuntimeError(
                f"Kode tidak cocok pada ID {row_id}: "
                f"database={row['code']!r}, matriks={code!r}"
            )
        if not row["source"] or "DRAF_PERLU_VERIFIKASI_TEKNIS" not in row["source"]:
            raise RuntimeError(
                f"Status draf tidak terdeteksi pada ID {row_id}; impor dibatalkan."
            )

    SOURCE_NOTE = 'Catatan verifikasi wajib: cocokkan kode dan halaman dengan manual resmi JUKI; pastikan submodel, panel/kotak kontrol, serta konfigurasi listrik unit target sebelum instruksi disahkan.'

    changed = sum(
        1 for row_id, (_, solution, safety) in revisions.items()
        if current_by_id[row_id]["solution"] != solution
        or current_by_id[row_id]["safety_notes"] != safety
        or SOURCE_NOTE not in (current_by_id[row_id]["source"] or "")
    )

    print("===== PRA-VALIDASI =====")
    print("Baris database cocok :", len(current))
    print("Baris matriks cocok  :", len(revisions))
    print("Baris yang berubah   :", changed)
    print("Kolom yang diperbarui: solution, safety_notes, source")
    print("Kolom lain           : dipertahankan")
    print("Status draf          : akan dipertahankan")
    print("Backup tujuan        :", backup)

    confirm = input("\nKetik YA untuk membuat backup dan menjalankan UPDATE: ")
    if confirm != "YA":
        print("DIBATALKAN. Database tidak diubah.")
        raise SystemExit(0)

    # Backup penuh sebelum perubahan.
    dest = sqlite3.connect(backup)
    try:
        con.backup(dest)
    finally:
        dest.close()

    if not backup.exists() or backup.stat().st_size == 0:
        raise RuntimeError("Backup tidak valid; impor dibatalkan.")

    con.execute("BEGIN IMMEDIATE")

    for row_id, (code, solution, safety) in revisions.items():
        cur = con.execute("""
            UPDATE troubleshooting
            SET solution = ?,
                safety_notes = ?,
                source = CASE
                    WHEN instr(COALESCE(source, ''), ?) > 0 THEN source
                    ELSE trim(COALESCE(source, '') || ' ' || ?)
                END
            WHERE id = ? AND machine_id = 16 AND code = ?
        """, (solution, safety, SOURCE_NOTE, SOURCE_NOTE, row_id, code))

        if cur.rowcount != 1:
            raise RuntimeError(
                f"UPDATE ID {row_id} memengaruhi {cur.rowcount} baris; dibatalkan."
            )

    # Validasi sebelum commit.
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()

    after = con.execute("""
        SELECT id, machine_id, code, source
        FROM troubleshooting
        WHERE machine_id = 16
        ORDER BY id
    """).fetchall()

    if integrity != "ok":
        raise RuntimeError(f"Integritas SQLite gagal: {integrity}")
    if fk_errors:
        raise RuntimeError(f"Ditemukan {len(fk_errors)} masalah foreign key.")
    if len(after) != 33 or {r["id"] for r in after} != expected_ids:
        raise RuntimeError("Validasi jumlah/ID setelah UPDATE gagal.")
    if any(
        r["source"] is None
        or "DRAF_PERLU_VERIFIKASI_TEKNIS" not in r["source"]
        for r in after
    ):
        raise RuntimeError("Status draf berubah atau hilang; dibatalkan.")

    con.commit()

    print("\n===== IMPOR BERHASIL =====")
    print("Baris diperiksa      :", len(after))
    print("Baris baru           : 0")
    print("Baris diperbarui     :", changed)
    print("Integritas SQLite    :", integrity)
    print("Foreign key errors   :", len(fk_errors))
    print("Status               : tetap DRAF_PERLU_VERIFIKASI_TEKNIS")
    print("Backup               :", backup)

except SystemExit:
    if con.in_transaction:
        con.rollback()
    raise
except Exception as e:
    if con.in_transaction:
        con.rollback()
    print("\nIMPor DIBATALKAN:", e)
    print("Jika backup sudah dibuat, file backup tetap tersedia.")
    raise SystemExit(1)
finally:
    con.close()
