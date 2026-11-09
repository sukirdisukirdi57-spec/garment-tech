import csv
import sqlite3
from pathlib import Path

CSV_FILE = Path("audit_organ_dpx17sk_20261027_rev8_status_review.csv")
DB_FILE = Path("database/garment.db")

# PENGAMAN: jangan impor sebelum pemeriksaan dan persetujuan akhir.
APPLY = True

EXPECTED = {
    "NM 90": "No. 14",
    "NM 100": "No. 16",
    "NM 110": "No. 18",
    "NM 120": "No. 19",
    "NM 125": "No. 20",
    "NM 130": "No. 21",
    "NM 140": "No. 22",
    "NM 160": "No. 23",
    "NM 180": "No. 24",
}

FIELDS = [
    "brand", "needle_system", "size_nm", "point_code",
    "point_description", "material_application", "product_code",
    "description", "source_url", "verification_status",
    "size_nm_value", "manufacturer_size", "verification_notes",
]

def stop(message):
    raise SystemExit(f"\nDIBATALKAN: {message}")

if not CSV_FILE.is_file():
    stop(f"CSV tidak ditemukan: {CSV_FILE}")

if not DB_FILE.is_file():
    stop(f"Database tidak ditemukan: {DB_FILE}")

with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
        stop("Kolom CSV tidak sesuai dengan skema yang diharapkan.")
    rows = list(reader)

if len(rows) != 9:
    stop(f"Harus ada 9 baris data; ditemukan {len(rows)}.")

seen = set()
for row in rows:
    if any(row.get(k) is None for k in FIELDS):
        stop("Ada kolom yang hilang pada baris CSV.")

    size = row["size_nm"].strip()
    if size in seen:
        stop(f"Ukuran ganda di CSV: NM {size}")
    seen.add(size)

    if row["brand"].strip().upper() != "ORGAN":
        stop(f"Brand tidak sesuai pada NM {size}.")
    if row["needle_system"].strip() != "DP×17-SK":
        stop(f"Sistem jarum tidak sesuai pada NM {size}.")
    if row["point_code"].strip().upper() != "R":
        stop(f"Point code tidak sesuai pada NM {size}.")
    if row["manufacturer_size"].strip() != EXPECTED.get(size):
        stop(f"Pasangan ukuran pabrikan tidak sesuai pada NM {size}.")
    if row["product_code"].strip():
        stop(f"product_code seharusnya kosong pada NM {size}.")
    if not row["source_url"].strip():
        stop(f"Sumber kosong pada NM {size}.")
    if not row["verification_status"].strip():
        stop(f"Status verifikasi kosong pada NM {size}.")

if seen != set(EXPECTED):
    stop("Daftar ukuran tidak sama dengan sembilan ukuran yang diaudit.")

# Pemeriksaan awal selalu READ-ONLY.
uri = DB_FILE.resolve().as_uri() + "?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.row_factory = sqlite3.Row

try:
    existing = []
    for row in rows:
        found = con.execute(
            """SELECT id, size_nm, product_code, verification_status
               FROM needles
               WHERE UPPER(TRIM(brand)) = 'ORGAN'
                 AND TRIM(needle_system) = ?
                 AND TRIM(size_nm) = ?""",
            (row["needle_system"].strip(), row["size_nm"].strip()),
        ).fetchall()
        if found:
            existing.append((row["size_nm"], [dict(x) for x in found]))
finally:
    con.close()

print("=== AUDIT IMPOR ORGAN DP×17-SK REV8 ===")
print("Mode:", "APPLY AKTIF" if APPLY else "SIMULASI / READ-ONLY")
print("Jumlah baris CSV:", len(rows))
print("Validasi CSV: LULUS")
print("Data yang sudah ditemukan:", len(existing))

if existing:
    for size, records in existing:
        print(f"PERLU TINJAU NM {size}: {records}")
    stop("Ada data yang sudah ada. Tidak ada baris yang diimpor.")

print("\n=== CALON PERUBAHAN ===")
for row in rows:
    print(
        f"ORGAN | DP×17-SK | {row['size_nm']} | "
        f"{row['manufacturer_size']} | POINT {row['point_code']} | "
        f"product_code tetap kosong"
    )

if not APPLY:
    print("\nSTATUS: SIAP DITINJAU.")
    print("Database hanya dibaca; tidak ada perubahan.")
    raise SystemExit(0)

# Jika APPLY diaktifkan kemudian, buka database tulis dan
# periksa ulang seluruh calon data di dalam transaksi.
con = sqlite3.connect(DB_FILE)
try:
    con.execute("BEGIN IMMEDIATE")

    for row in rows:
        found = con.execute(
            """SELECT id FROM needles
               WHERE UPPER(TRIM(brand)) = 'ORGAN'
                 AND TRIM(needle_system) = ?
                 AND TRIM(size_nm) = ?""",
            (row["needle_system"].strip(), row["size_nm"].strip()),
        ).fetchall()
        if found:
            stop("Data muncul sebelum impor. Transaksi dibatalkan.")

    sql = (
        "INSERT INTO needles (" + ", ".join(FIELDS) + ") VALUES ("
        + ", ".join("?" for _ in FIELDS) + ")"
    )
    for row in rows:
        values = [row[field].strip() for field in FIELDS]
        values[FIELDS.index("size_nm_value")] = (
            float(values[FIELDS.index("size_nm_value")])
        )
        con.execute(sql, values)

    con.commit()
    print(f"\nIMPOR SELESAI: {len(rows)} baris ditambahkan.")
except Exception:
    con.rollback()
    raise
finally:
    con.close()
