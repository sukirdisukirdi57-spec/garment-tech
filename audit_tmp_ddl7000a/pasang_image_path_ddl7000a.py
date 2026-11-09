import csv
import sqlite3
from pathlib import Path

# MODE AMAN: ubah menjadi True hanya setelah skrip ditinjau dan disetujui.
APPLY = True

ROOT = Path.cwd()
CSV_FILE = ROOT / "audit_tmp_ddl7000a/proposal_image_path_ddl7000a_30.csv"
DB_FILE = ROOT / "database/garment.db"
BACKUP = ROOT / "database/garment_before_ddl7000a_imagepath_20261105.db"

with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 30:
    raise SystemExit(f"BATAL: proposal harus 30 baris, ditemukan {len(rows)}")

ids = [int(r["component_id"]) for r in rows]
if len(set(ids)) != 30:
    raise SystemExit("BATAL: ditemukan ID komponen duplikat")

# Validasi seluruh file gambar tujuan.
for r in rows:
    target = (ROOT / "static" / r["target_image_path"]).resolve()
    if not target.is_relative_to((ROOT / "static").resolve()):
        raise SystemExit("BATAL: path gambar di luar folder static")
    if not target.is_file():
        raise SystemExit(f"BATAL: gambar tidak ditemukan: {target}")

db = sqlite3.connect(DB_FILE)
try:
    # Pastikan semua komponen benar dan image_path masih kosong.
    for r in rows:
        found = db.execute("""
            SELECT image_path FROM components
            WHERE id=? AND machine_id=4
        """, (int(r["component_id"]),)).fetchone()

        if found is None:
            raise SystemExit(f"BATAL: komponen {r['component_id']} tidak ditemukan")
        if found[0]:
            raise SystemExit(f"BATAL: image_path komponen {r['component_id']} sudah terisi")

    print("VALIDASI: LULUS")
    print("Komponen akan diperbarui:", len(rows))
    print("Semua gambar tersedia:", True)
    print("Semua image_path masih kosong:", True)
    print("Mode APPLY:", APPLY)

    if not APPLY:
        print("SIMULASI SAJA — database tidak diubah.")
    else:
        if BACKUP.exists():
            raise SystemExit(f"BATAL: file backup sudah ada: {BACKUP}")

        # Backup database sebelum perubahan.
        backup_db = sqlite3.connect(BACKUP)
        db.backup(backup_db)
        backup_db.close()

        try:
            db.execute("BEGIN IMMEDIATE")

            for r in rows:
                cur = db.execute("""
                    UPDATE components
                    SET image_path=?
                    WHERE id=? AND machine_id=4
                      AND (image_path IS NULL OR TRIM(image_path)='')
                """, (
                    r["target_image_path"],
                    int(r["component_id"])
                ))
                if cur.rowcount != 1:
                    raise RuntimeError(
                        f"Gagal memperbarui komponen {r['component_id']}"
                    )

            # Verifikasi sebelum commit.
            for r in rows:
                actual = db.execute("""
                    SELECT image_path FROM components
                    WHERE id=? AND machine_id=4
                """, (int(r["component_id"]),)).fetchone()

                if actual is None or actual[0] != r["target_image_path"]:
                    raise RuntimeError(
                        f"Verifikasi gagal pada komponen {r['component_id']}"
                    )

            db.commit()
            print("UPDATE BERHASIL:", len(rows))
            print("Backup:", BACKUP)

        except Exception:
            db.rollback()
            raise

finally:
    db.close()

print("Selesai.")
