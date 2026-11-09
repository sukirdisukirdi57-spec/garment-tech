import csv
from pathlib import Path

csv_path = Path("ps800-error-codes-review.csv")
sql_path = Path("ps800-error-codes-proposal.sql")

if not csv_path.exists():
    raise SystemExit("GAGAL: CSV audit tidak ditemukan.")

with csv_path.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

expected = (
    [f"E{i:03d}" for i in range(1, 8)]
    + [f"E{i:03d}" for i in range(20, 112)]
    + [f"E{i:03d}" for i in range(200, 251)]
)

codes = [r["code"].strip() for r in rows]
if len(rows) != 150 or set(codes) != set(expected) or len(set(codes)) != 150:
    raise SystemExit(
        f"GAGAL: data harus berisi tepat 150 kode unik. Ditemukan {len(rows)} baris."
    )

def q(value):
    return "'" + (value or "").replace("'", "''") + "'"

lines = [
    "-- USULAN SAJA: JUKI PS-800-12080, machine_id=11",
    "-- Dibuat dari ps800-error-codes-review.csv",
    "-- Belum dijalankan; periksa dan setujui terlebih dahulu.",
    "-- Hanya menambah kode yang belum ada untuk machine_id=11.",
    "-- Tidak menggunakan UPDATE atau DELETE.",
    "",
    "BEGIN TRANSACTION;",
    ""
]

for r in rows:
    code = r["code"].strip()
    problem = f"Kode error {code} — {r['problem'].strip()}"
    values = [
        "11",
        q(problem),
        q(r["symptoms"]),
        q(r["possible_cause"]),
        q(r["solution"]),
        q(r["safety_notes"]),
        q(r["source"]),
        q(code),
    ]

    lines.extend([
        "INSERT INTO troubleshooting",
        "(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)",
        "SELECT " + ", ".join(values),
        f"WHERE NOT EXISTS (SELECT 1 FROM troubleshooting "
        f"WHERE machine_id = 11 AND TRIM(code) = {q(code)});",
        ""
    ])

lines.extend([
    "-- COMMIT sengaja belum ditambahkan.",
    "-- Tinjau isi file sebelum memutuskan menjalankan SQL.",
    ""
])

sql_path.write_text("\n".join(lines), encoding="utf-8")
print("File usulan dibuat:", sql_path)
print("Jumlah kode dalam usulan:", len(rows))
print("Database tidak diubah.")
