import csv
import re
import subprocess
from collections import Counter
from pathlib import Path

pdf = Path(
    "assets/documents/brother/t8421d/"
    "t8421d_t8422d_parts_en.pdf"
)
out = Path("tools/preview_brother_t8422d_j2_all_rows.csv")

if not pdf.is_file():
    raise SystemExit(f"STOP: PDF tidak ditemukan: {pdf}")

result = subprocess.run(
    ["pdftotext", "-layout", str(pdf), "-"],
    capture_output=True,
    text=True,
    check=True,
)
lines = result.stdout.splitlines()

start, end = 1138, 1329
pattern = re.compile(
    r"^\s*(\d+\+?)\s+([A-Z0-9-]{6,})\s+(\d+)\s+(.+?)\s*$"
)

rows = []
for line_no in range(start, min(end, len(lines)) + 1):
    match = pattern.match(lines[line_no - 1])
    if not match:
        continue

    ref, code, qty, description = match.groups()
    rows.append({
        "machine_id": 85,
        "source_document_id": 263,
        "component_name": "J2 - Rotary hook mechanism",
        "catalog_ref_raw": ref,
        "catalog_ref_numeric": ref.rstrip("+"),
        "catalog_ref_has_plus": "yes" if ref.endswith("+") else "no",
        "part_number": code,
        "quantity": qty,
        "part_name": description.strip(),
        "source_pdf": str(pdf),
        "source_line": line_no,
    })

counts = Counter(row["part_number"] for row in rows)
unique_count = len(counts)
duplicate_rows = sum(n - 1 for n in counts.values() if n > 1)

if len(rows) != 66 or unique_count != 62 or duplicate_rows != 4:
    raise SystemExit(
        f"STOP: hasil tidak sesuai harapan. "
        f"Baris={len(rows)}, unik={unique_count}, "
        f"kemunculan tambahan={duplicate_rows}. CSV tidak dibuat."
    )

with out.open("x", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print("DRY-RUN LENGKAP BERHASIL")
print("Database diubah: TIDAK")
print("Jumlah baris katalog:", len(rows))
print("Nomor part unik:", unique_count)
print("Kemunculan nomor part tambahan:", duplicate_rows)
print("Referensi bertanda +:", sum(
    row["catalog_ref_has_plus"] == "yes" for row in rows
))
print("CSV:", out)
print("\nBaris nomor part yang berulang:")
for code, count in sorted(counts.items()):
    if count > 1:
        print(f"  {code}: {count} kemunculan")
