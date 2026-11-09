import csv
import re
import subprocess
from pathlib import Path

pdf = Path(
    "assets/documents/brother/t8421d/"
    "t8421d_t8422d_parts_en.pdf"
)
out = Path("tools/preview_brother_t8422d_j2.csv")

if not pdf.is_file():
    raise SystemExit(f"PDF tidak ditemukan: {pdf}")

result = subprocess.run(
    ["pdftotext", "-layout", str(pdf), "-"],
    capture_output=True,
    text=True,
    check=True,
)
lines = result.stdout.splitlines()

# Batas J2 yang sebelumnya sudah menghasilkan 62 nomor part unik.
start, end = 1138, 1329
pattern = re.compile(
    r"^\s*(\d+\+?)\s+([A-Z0-9-]{6,})\s+(\d+)\s+(.+?)\s*$"
)

found = {}
duplicates = []

for line_no in range(start, min(end, len(lines)) + 1):
    match = pattern.match(lines[line_no - 1])
    if not match:
        continue

    ref, code, qty, description = match.groups()
    row = {
        "machine_id": 85,
        "source_document_id": 263,
        "component_name": "J2 - Rotary hook mechanism",
        "catalog_ref_raw": ref,
        "part_number": code,
        "quantity": qty,
        "part_name": description.strip(),
        "source_pdf": str(pdf),
        "source_line": line_no,
    }

    if code in found:
        duplicates.append((code, found[code]["source_line"], line_no))
    else:
        found[code] = row

if len(found) != 62:
    raise SystemExit(
        f"STOP: terbaca {len(found)} nomor part unik, bukan 62. "
        "CSV tidak dibuat."
    )

with out.open("x", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(next(iter(found.values()))))
    writer.writeheader()
    writer.writerows(found.values())

print("DRY-RUN J2 BERHASIL")
print("Database diubah: TIDAK")
print("Mesin target: T-8422D (ID 85)")
print("Dokumen sumber: 263")
print("Part unik dalam pratinjau:", len(found))
print("Referensi dengan tanda +:",
      sum("+" in row["catalog_ref_raw"] for row in found.values()))
print("Nomor part berulang pada ekstraksi:", len(duplicates))
for item in duplicates:
    print("  DUPLIKAT:", item)
print("CSV pratinjau:", out)
print("\nLima baris pertama:")
for row in list(found.values())[:5]:
    print(
        row["catalog_ref_raw"],
        row["part_number"],
        row["quantity"],
        row["part_name"],
    )
