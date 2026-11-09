#!/usr/bin/env python3
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "bas311hn_extract.txt"
OUTPUT = ROOT / "tmp/bas311hn/page3_staging.csv"

start_marker = "B. 上軸 ・針棒関係 / Upper shaft and needle bar mechanism"
end_marker = "BAS-311HN/326H-123"

with SOURCE.open(encoding="utf-8", errors="replace") as f:
    text = f.read()

start = text.find(start_marker)
if start < 0:
    raise SystemExit("GAGAL: bagian B tidak ditemukan.")

end = text.find(end_marker, start)
if end < 0:
    raise SystemExit("GAGAL: akhir bagian B tidak ditemukan.")

section = text[start:end]
pattern = re.compile(
    r"^\s*(\d+\+?)\s+"
    r"([A-Z0-9][A-Z0-9-]*)\s+"
    r"(\d+)\s+"
    r".*?\s{2,}([A-Z][A-Z0-9 ,()/.-]+?)\s*$"
)

rows = []
for line in section.splitlines():
    match = pattern.match(line)
    if not match:
        continue

    ref, code, qty, name = match.groups()
    rows.append({
        "catalog_ref": ref,
        "part_number": code,
        "quantity_raw": qty,
        "part_name": name.strip(),
        "diagram_page": 3,
        "mechanism": "B. Upper shaft and needle bar mechanism",
        "verification": "REVIEW_REQUIRED",
    })

if not rows:
    raise SystemExit(
        "GAGAL: tidak ada baris yang cocok; format ekstraksi perlu diperiksa."
    )

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print("STAGING dibuat:", OUTPUT.relative_to(ROOT))
print("Baris hasil ekstraksi:", len(rows))
print("Semua baris ditandai REVIEW_REQUIRED.")
print("Database tidak diubah.")
