import csv
import sqlite3
from pathlib import Path

db = Path("database/garment.db")
v1 = Path("audit-kelengkapan/draf_perbaikan_isi_ddl8700.csv")
v2 = Path("audit-kelengkapan/draf_perbaikan_isi_ddl8700_v2.csv")
report = Path("audit-kelengkapan/verifikasi_draf_v2.csv")
ids = {1, 2, 3, 4, 247, 248, 249, 250}
content_fields = ("possible_cause", "solution", "safety_notes")

for p in (db, v1, v2):
    if not p.exists():
        raise SystemExit(f"File tidak ditemukan: {p}")

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {int(r["id"]): r for r in csv.DictReader(f)}

old = read_csv(v1)
new = read_csv(v2)

if not ids.issubset(old) or not ids.issubset(new):
    raise SystemExit("GAGAL: satu atau lebih ID target tidak ada di CSV.")

# Pastikan sumber tidak berubah dari draf sebelumnya.
source_ok = all(old[i].get("source_tidak_diubah", old[i].get("source", ""))
                == new[i].get("source_tidak_diubah", new[i].get("source", ""))
                for i in ids)

# Snapshot isi DB target dan integrity check, seluruh koneksi read-only.
uri = f"file:{db.resolve()}?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.row_factory = sqlite3.Row
integrity = con.execute("PRAGMA integrity_check").fetchone()[0]

db_rows = con.execute("""
    SELECT id, machine_id, problem, possible_cause, solution, safety_notes, source
    FROM troubleshooting
    WHERE machine_id = 3 AND id IN (1,2,3,4,247,248,249,250)
""").fetchall()
con.close()

db_by_id = {r["id"]: dict(r) for r in db_rows}
db_ids_ok = set(db_by_id) == ids

out = []
for i in sorted(ids):
    row = new[i]
    missing = [
        f for f in content_fields
        if not row.get(f"{f}_usulan", "").strip()
    ]
    status = "LULUS" if not missing else "GAGAL: usulan kosong"
    out.append({
        "id": i,
        "problem": row.get("problem", ""),
        "kelengkapan_usulan": status,
        "kolom_kosong": ", ".join(missing),
        "source_v1_v2_cocok": "YA" if source_ok else "PERIKSA",
        "integrity_database": integrity,
        "database_tidak_diubah": "YA - koneksi hanya-baca",
        "status_penerapan": "BELUM DITERAPKAN"
    })

with report.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(out[0]))
    writer.writeheader()
    writer.writerows(out)

print(f"Jumlah ID target di database: {len(db_by_id)} dari {len(ids)}")
print(f"ID database lengkap: {'YA' if db_ids_ok else 'TIDAK'}")
print(f"Integrity check: {integrity}")
print(f"Source V1 dan V2 cocok: {'YA' if source_ok else 'TIDAK - periksa CSV'}")
print("Kelengkapan usulan:")
for r in out:
    print(f"ID {r['id']}: {r['kelengkapan_usulan']}")
print(f"Laporan: {report}")
print("Database dibuka hanya-baca; tidak ada perubahan database.")
