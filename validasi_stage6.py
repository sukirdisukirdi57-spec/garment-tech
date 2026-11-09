import csv
import sqlite3
from pathlib import Path

csv_path = Path("tmp/lbh1790an/proposal_error_codes_stage6.csv")
db_path = Path("database/garment.db")

expected = [
    "E905", "E907", "E908", "E909", "E910", "E911",
    "E915", "E916", "E918", "E943", "E946", "E999"
]
required = [
    "machine_id", "code", "problem", "symptoms",
    "possible_cause", "solution", "safety_notes", "source"
]

errors = []

with csv_path.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames or []
    rows = list(reader)

if fields != required:
    errors.append(f"Kolom tidak sesuai: {fields}")

codes = [r.get("code", "").strip() for r in rows]

if len(rows) != 12:
    errors.append(f"Jumlah baris seharusnya 12, ditemukan {len(rows)}")
if len(codes) != len(set(codes)):
    errors.append("Ada kode duplikat dalam proposal")
if set(codes) != set(expected):
    errors.append("Daftar kode tidak sama dengan daftar Stage 6")
if any(r.get("machine_id", "").strip() != "6" for r in rows):
    errors.append("Ada machine_id yang bukan 6")

for i, row in enumerate(rows, start=2):
    for field in required:
        if not row.get(field, "").strip():
            errors.append(f"Baris CSV {i}: kolom {field} kosong")
    if row.get("source", "").strip() != (
        "JUKI LBH-1790AN/1795AN Instruction Manual, "
        "VIII. Error Code List, hlm. cetak 79"
    ):
        errors.append(f"Baris CSV {i}: sumber belum seragam/terverifikasi")

print("=== VALIDASI PROPOSAL STAGE 6 ===")
print("Jumlah baris:", len(rows))
print("Jumlah kode unik:", len(set(codes)))
print("Kode:", ", ".join(codes))
print("Pemeriksaan kolom, machine_id, isi, dan sumber:",
      "LULUS" if not errors else "PERLU DIPERIKSA")

# Koneksi read-only: tidak dapat menulis ke database.
uri = db_path.resolve().as_uri() + "?mode=ro"
con = sqlite3.connect(uri, uri=True)
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    total = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id = 6"
    ).fetchone()[0]
    coded = con.execute(
        """SELECT COUNT(*) FROM troubleshooting
           WHERE machine_id = 6 AND code IS NOT NULL
           AND TRIM(code) != ''"""
    ).fetchone()[0]
    uncoded = total - coded

    existing = {
        row[0] for row in con.execute(
            """SELECT code FROM troubleshooting
               WHERE machine_id = 6 AND code IS NOT NULL
               AND TRIM(code) != ''"""
        )
    }
    collisions = sorted(set(codes) & existing)

    print("\n=== DATABASE (BACA-SAJA) ===")
    print("Total entri mesin ID 6:", total)
    print("Entri berkode:", coded)
    print("Entri tanpa kode:", uncoded)
    print("Integritas SQLite:", integrity)
    print("Benturan kode:", ", ".join(collisions) if collisions else "0")

    if integrity != "ok":
        errors.append("Integritas SQLite tidak ok")
    if total != 73 or coded != 65 or uncoded != 8:
        errors.append("Jumlah database berbeda dari kondisi awal")
    if collisions:
        errors.append("Ada kode proposal yang sudah ada di database")
finally:
    con.close()

print("\n=== HASIL AKHIR ===")
if errors:
    print("BELUM LULUS:")
    for e in errors:
        print("-", e)
else:
    print("LULUS — proposal siap ditinjau untuk persetujuan impor.")
print("Database tidak diubah oleh skrip validasi ini.")
