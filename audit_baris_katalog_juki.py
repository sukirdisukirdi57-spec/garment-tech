import csv
import re
from pathlib import Path
from collections import Counter

TXT = Path("assets/documents/juki/ams210en-parts.txt")
CSV_FILE = Path("preview_daftar_part_juki.csv")

PAGE_CHUNK = {
    6: 7, 8: 9, 10: 11, 12: 13, 14: 15, 16: 17,
    20: 21, 22: 22, 23: 23, 28: 29, 30: 31, 32: 33
}

chunks = TXT.read_text(errors="replace").split("\f")

with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
    matched = list(csv.DictReader(f))

matched_keys = {
    (int(r["pdf_page"]), int(r["line_no"]))
    for r in matched
}

print("=== AUDIT BARIS KATALOG YANG BELUM TERCOCOK ===")
total_catalog = 0
total_unmatched = 0

for page, chunk_no in PAGE_CHUNK.items():
    lines = chunks[chunk_no - 1].splitlines()
    catalog_rows = []

    for line_no, line in enumerate(lines, start=1):
        s = line.strip()

        # Baris katalog biasanya diawali Ref. lalu nomor part.
        # Abaikan header, tanda pemisah, dan teks indeks.
        if not re.match(r"^\d+\s+", s):
            continue

        if not re.search(r"\b(?:[A-Z0-9]{2,}-[A-Z0-9-]+)\b", s):
            continue

        catalog_rows.append((line_no, s))

    unmatched = [
        (line_no, s)
        for line_no, s in catalog_rows
        if (page, line_no) not in matched_keys
    ]

    total_catalog += len(catalog_rows)
    total_unmatched += len(unmatched)

    print(
        f"\nPDF halaman {page}: "
        f"{len(catalog_rows)} baris katalog, "
        f"{len(unmatched)} belum cocok"
    )

    for line_no, line in unmatched[:12]:
        print(f"  Baris {line_no}: {line}")

    if len(unmatched) > 12:
        print(f"  ... dan {len(unmatched) - 12} baris lainnya")

print("\n=== TOTAL ===")
print("Baris kandidat katalog:", total_catalog)
print("Baris belum cocok:", total_unmatched)
print("CSV pratinjau tetap tidak diubah.")
