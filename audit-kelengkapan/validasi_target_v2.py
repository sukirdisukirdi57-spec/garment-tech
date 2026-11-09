import csv
import sqlite3
from pathlib import Path

db = Path("database/garment.db")
csv_path = Path("audit-kelengkapan/draf_perbaikan_isi_ddl8700_v2.csv")
out_path = Path("audit-kelengkapan/validasi_target_v2.csv")

ids = {1, 2, 3, 4, 247, 248, 249, 250}
fields = ("possible_cause", "solution", "safety_notes")

if not db.is_file() or not csv_path.is_file():
    raise SystemExit("GAGAL: database atau CSV V2 tidak ditemukan.")

with csv_path.open(encoding="utf-8-sig", newline="") as f:
    csv_rows = list(csv.DictReader(f))

by_id = {}
for row in csv_rows:
    try:
        rid = int(row["id"])
    except (KeyError, ValueError, TypeError):
        continue
    if rid in by_id:
        raise SystemExit(f"GAGAL: ID {rid} duplikat dalam CSV.")
    by_id[rid] = row

if set(by_id) != ids:
    raise SystemExit(
        f"GAGAL: ID CSV tidak sesuai. "
        f"Kurang={sorted(ids-set(by_id))}, "
        f"lebih={sorted(set(by_id)-ids)}"
    )

con = sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_rows = con.execute("""
        SELECT id, machine_id, problem, possible_cause, solution,
               safety_notes, source
        FROM troubleshooting
        WHERE id IN (1,2,3,4,247,248,249,250)
    """).fetchall()
finally:
    con.close()

db_by_id = {r["id"]: dict(r) for r in db_rows}

if set(db_by_id) != ids:
    raise SystemExit(
        "GAGAL: ID database tidak tepat. "
        f"Ditemukan={sorted(db_by_id)}"
    )

results = []
all_ok = integrity == "ok"

for rid in sorted(ids):
    d = db_by_id[rid]
    c = by_id[rid]
    checks = []

    if d["machine_id"] != 3:
        checks.append("machine_id bukan 3")

    for field in fields:
        old_value = c.get(f"{field}_lama")
        proposed = c.get(f"{field}_usulan")

        if old_value is None:
            checks.append(f"{field}: kolom teks lama tidak ditemukan")
        elif (d[field] or "") != old_value:
            checks.append(f"{field}: teks lama tidak cocok dengan DB")

        if not proposed or not proposed.strip():
            checks.append(f"{field}: usulan kosong")

    # Jika kolom source_tidak_diubah tersedia, cocokkan dengan DB.
    expected_source = c.get("source_tidak_diubah")
    if expected_source is not None and d["source"] != expected_source:
        checks.append("source berbeda dari CSV V2")

    ok = not checks
    all_ok = all_ok and ok

    results.append({
        "id": rid,
        "problem": d["problem"],
        "machine_id": d["machine_id"],
        "teks_lama_cocok": "YA" if ok else "PERIKSA",
        "detail": "; ".join(checks),
        "integrity_check": integrity,
        "database_diubah": "TIDAK - hanya-baca"
    })

with out_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

print(f"Integrity check: {integrity}")
for r in results:
    print(f"ID {r['id']}: {r['teks_lama_cocok']}"
          + (f" — {r['detail']}" if r["detail"] else ""))

print(f"HASIL VALIDASI: {'LULUS' if all_ok else 'PERLU DIPERIKSA'}")
print(f"Laporan: {out_path}")
print("Database tidak diubah.")
