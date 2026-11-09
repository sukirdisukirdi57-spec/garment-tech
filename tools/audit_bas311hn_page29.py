import csv
import re
import sqlite3
from pathlib import Path
from collections import Counter

CSV_FILE = Path("tmp/bas311hn/e_staging_review.csv")
TEXT_FILE = Path("tmp/bas311hn/full_catalog_layout.txt")
DB_FILE = Path("database/garment.db")

def normalize_code(value):
    return (value or "").strip().upper()

def main():
    for path in (CSV_FILE, TEXT_FILE, DB_FILE):
        if not path.is_file():
            raise SystemExit(f"File tidak ditemukan: {path}")

    with CSV_FILE.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    text = TEXT_FILE.read_text(encoding="utf-8", errors="replace")

    # Indeks katalog: kode, seksi E, ref, halaman cetak 30.
    index_entries = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        match = re.search(
            r"\b([A-Z0-9]{6,12})\s+E\s*-\s*(\d{1,2})\s+30\b",
            line
        )
        if match:
            code = normalize_code(match.group(1))
            ref = int(match.group(2))
            index_entries.setdefault((ref, code), []).append(line_no)

    print("=== AUDIT CSV VS INDEKS KATALOG ===")
    print(f"Jumlah baris CSV: {len(rows)}")
    print(f"Entri indeks seksi E ditemukan: {len(index_entries)}")

    counts = Counter(r["verification"] for r in rows)
    print("\nStatus CSV:")
    for status, total in sorted(counts.items()):
        print(f"  {status}: {total}")

    print("\n=== HASIL PER REF ===")
    for row in rows:
        ref = int(row["catalog_ref"])
        code = normalize_code(row["part_number"])
        status = row["verification"]

        if not code:
            result = "KODE KOSONG — perlu pemeriksaan varian"
        elif (ref, code) in index_entries:
            result = "KODE + REF ditemukan pada indeks"
        else:
            result = "BELUM COCOK pada indeks — periksa manual"

        print(
            f'Ref {ref:02d} | {code or "(kosong)":12} | '
            f'{status:22} | {result}'
        )

    print("\n=== VALIDASI DATABASE BACA-SAJА ===")
    con = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    try:
        machine = con.execute(
            "SELECT model FROM machines WHERE id = 227"
        ).fetchone()
        document = con.execute(
            "SELECT machine_id, document_type FROM documents WHERE id = 582"
        ).fetchone()
        part_count = con.execute(
            "SELECT COUNT(*) FROM parts "
            "WHERE machine_id = 227 AND diagram_page = 29"
        ).fetchone()[0]

        print("Mesin ID 227:", machine)
        print("Dokumen ID 582:", document)
        print("Jumlah part halaman 29 saat ini:", part_count)
    finally:
        con.close()

    print("\nAUDIT SELESAI — CSV dan database tidak diubah.")
    print("Hasil indeks hanya petunjuk; bukan bukti penerapan varian -03S.")

if __name__ == "__main__":
    main()
