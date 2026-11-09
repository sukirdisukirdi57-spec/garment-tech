#!/usr/bin/env python3
import csv
from pathlib import Path

root = Path(__file__).resolve().parent.parent
source = root / "tmp/bas311hn/page3_staging.csv"
output = root / "tmp/bas311hn/page3_staging_review.csv"

if not source.is_file():
    raise SystemExit(f"STOP: CSV sumber tidak ditemukan: {source}")

with source.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if len(rows) != 51:
    raise SystemExit(
        f"STOP: jumlah baris sumber {len(rows)}, diharapkan 51."
    )

required = {
    "catalog_ref", "part_number", "quantity_raw",
    "part_name", "diagram_page", "mechanism", "verification"
}
if not fields or not required.issubset(fields):
    raise SystemExit(f"STOP: kolom CSV tidak sesuai: {fields}")

# Pilihan jarum ditambahkan sebagai opsi katalog untuk ditinjau,
# bukan dianggap otomatis terpasang pada mesin.
rows.extend([
    {
        "catalog_ref": "40+",
        "part_number": "",
        "quantity_raw": "",
        "part_name": "NEEDLE, DPX5 (#16)",
        "diagram_page": "3",
        "mechanism": "B. Upper shaft and needle bar mechanism",
        "verification": "VARIANT_OPTION: For -03[]; verify applicability",
    },
    {
        "catalog_ref": "40+",
        "part_number": "",
        "quantity_raw": "",
        "part_name": "NEEDLE, DPX17 (#19)",
        "diagram_page": "3",
        "mechanism": "B. Upper shaft and needle bar mechanism",
        "verification": "VARIANT_OPTION: For -05[]; not selected",
    },
    {
        "catalog_ref": "40+",
        "part_number": "",
        "quantity_raw": "",
        "part_name": "NEEDLE, DPX17 (#25)",
        "diagram_page": "3",
        "mechanism": "B. Upper shaft and needle bar mechanism",
        "verification": "VARIANT_OPTION: For -07[]; not selected",
    },
])

with output.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("CSV tinjauan:", output.relative_to(root))
print("Baris sumber:", len(rows) - 3)
print("Baris setelah opsi jarum ditambahkan:", len(rows))
print("Pilihan jarum REF 40+:", sum(r["catalog_ref"] == "40+" for r in rows))
print("Database diubah: TIDAK")
print("Status: BELUM SIAP IMPOR")
