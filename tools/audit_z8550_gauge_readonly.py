import csv
import re
from pathlib import Path
from collections import Counter

staging_path = Path("tools/z8550b_z8560b_gauge_staging.csv")
main_path = Path("tools/z8550b_z8560b_parts_candidates.csv")

with staging_path.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print("Total baris staging:", len(rows))
print("Ringkasan status:", dict(Counter(
    r["review_status"] for r in rows
)))

print("\n=== STATUS YANG PERLU DITINJAU ===")
for r in rows:
    if r["review_status"] != "EXISTS_IN_MAIN_CANDIDATES":
        print(
            f"Hal. {r['printed_catalog_page']} | "
            f"{r['section_code']} | {r['zigzag_width']} | "
            f"{r['part_role']} | {r['part_number']} | "
            f"{r['variant_description']} | {r['review_status']}"
        )

with main_path.open(newline="", encoding="utf-8-sig") as f:
    main = list(csv.DictReader(f))

normalize = lambda s: re.sub(r"[^A-Z0-9]", "", (s or "").upper())
codes = {normalize(r.get("part_number", "")) for r in main}

print("\n=== PEMERIKSAAN KODE DI CSV UTAMA ===")
targets = [
    "S48143-101", "S48305-201", "S58950-201",
    "S06166-001", "S06170-101", "S53410-001",
    "S52068-001", "S54937-001", "S50686-001",
    "S50685-001", "S54929-001", "S54945-001",
    "S54957-201"
]

for code in targets:
    print(f"{code:14} {'ADA' if normalize(code) in codes else 'TIDAK ADA'}")

print("\nAudit selesai. Database tidak diubah.")
