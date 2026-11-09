import csv
import sqlite3
import sys
from pathlib import Path

CSV_PATH = Path("audit_organ_dpx17sk_20261026_rev7.csv")
DB_PATH = Path("database/garment.db")

EXPECTED = {
    "90": "No. 14",
    "100": "No. 16",
    "110": "No. 18",
    "120": "No. 19",
    "125": "No. 20",
    "130": "No. 21",
    "140": "No. 22",
    "160": "No. 23",
    "180": "No. 24",
}

REQUIRED_COLUMNS = {
    "brand", "needle_system", "size_nm", "point_code",
    "point_description", "material_application", "product_code",
    "description", "source_url", "verification_status",
    "size_nm_value", "manufacturer_size", "verification_notes",
}

def stop(message):
    print("GAGAL:", message)
    sys.exit(1)

def norm(value):
    return (value or "").strip().upper().replace(" ", "")

if not CSV_PATH.is_file():
    stop(f"CSV tidak ditemukan: {CSV_PATH}")

if not DB_PATH.is_file():
    stop(f"Database tidak ditemukan: {DB_PATH}")

with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        stop("Header CSV kosong.")
    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        stop(f"Kolom wajib tidak ada: {sorted(missing)}")
    rows = list(reader)

print("=== SIMULASI IMPOR ORGAN DP×17-SK ===")
print("Mode: SIMULASI / READ-ONLY")
print("CSV:", CSV_PATH)
print("Jumlah baris:", len(rows))

errors = []
seen = set()

if len(rows) != 9:
    errors.append(f"Seharusnya 9 baris, ditemukan {len(rows)}.")

for line, row in enumerate(rows, start=2):
    size = (row.get("size_nm_value") or "").strip()
    key = (norm(row.get("brand")),
           norm(row.get("needle_system")), size)

    if key in seen:
        errors.append(f"Baris {line}: duplikat dalam CSV: {key}")
    seen.add(key)

    if norm(row.get("brand")) != "ORGAN":
        errors.append(f"Baris {line}: brand bukan ORGAN.")
    if norm(row.get("needle_system")) != norm("DP×17-SK"):
        errors.append(f"Baris {line}: sistem jarum tidak sesuai.")
    if size not in EXPECTED:
        errors.append(f"Baris {line}: ukuran NM tidak dikenal: {size}")
    elif (row.get("manufacturer_size") or "").strip() != EXPECTED[size]:
        errors.append(
            f"Baris {line}: pasangan ukuran {size} tidak sesuai "
            f"(seharusnya {EXPECTED[size]})."
        )
    if (row.get("point_code") or "").strip() != "R":
        errors.append(f"Baris {line}: POINT bukan R.")
    if (row.get("product_code") or "").strip():
        errors.append(
            f"Baris {line}: product_code terisi tetapi belum diverifikasi."
        )
    if not (row.get("source_url") or "").strip():
        errors.append(f"Baris {line}: source_url kosong.")

if { (r.get("size_nm_value") or "").strip() for r in rows } != set(EXPECTED):
    errors.append("Daftar ukuran tidak sama dengan sembilan ukuran yang diharapkan.")

con = sqlite3.connect(
    f"file:{DB_PATH.resolve()}?mode=ro",
    uri=True
)
con.row_factory = sqlite3.Row

existing = []
try:
    columns = {
        r["name"] for r in
        con.execute("PRAGMA table_info('needles')").fetchall()
    }
    needed = {
        "id", "brand", "needle_system", "size_nm",
        "point_code", "product_code"
    }
    if not needed.issubset(columns):
        stop("Struktur tabel needles tidak sesuai harapan.")

    print("\n=== PEMERIKSAAN DATABASE ===")
    for row in rows:
        matches = con.execute("""
            SELECT id, brand, needle_system, size_nm,
                   point_code, product_code
            FROM needles
            WHERE UPPER(TRIM(brand)) = UPPER(TRIM(?))
              AND REPLACE(needle_system, ' ', '') =
                  REPLACE(?, ' ', '')
              AND UPPER(TRIM(size_nm)) = UPPER(TRIM(?))
        """, (
            row["brand"], row["needle_system"], row["size_nm"]
        )).fetchall()

        if matches:
            existing.extend(matches)
            print(
                "SUDAH ADA / PERLU TINJAU:",
                row["needle_system"], row["size_nm"],
                "| ID database:", [m["id"] for m in matches]
            )
        else:
            print(
                "CALON TAMBAH:",
                row["brand"], row["needle_system"],
                row["size_nm"], row["manufacturer_size"],
                "| POINT:", row["point_code"]
            )
finally:
    con.close()

print("\n=== HASIL SIMULASI ===")
if errors:
    print("STATUS: GAGAL VALIDASI")
    for error in errors:
        print("-", error)
else:
    print("Validasi dasar CSV: LULUS")

print("Jumlah baris proposal:", len(rows))
print("Jumlah baris yang sudah ditemukan:", len(existing))
print("Jumlah baris calon tambah:", len(rows) - len(existing))

if errors or existing:
    print("STATUS AKHIR: JANGAN IMPOR; perlu ditinjau.")
else:
    print("STATUS AKHIR: SIAP DITINJAU UNTUK PERSETUJUAN IMPOR.")

print("\nPENTING: Simulasi selesai.")
print("Database hanya dibaca; tidak ada perubahan.")
