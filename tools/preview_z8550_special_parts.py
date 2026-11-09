import csv
import re
from pathlib import Path

src = Path("tools/z8550b_z8560b_parts_layout.txt")
out = Path("tools/z8550b_z8560b_special_parts_review.csv")
lines = src.read_text(encoding="utf-8", errors="replace").splitlines()

sections = [
    ("Ga1", 2623, 2692, "Gauge parts list"),
    ("Ga2", 2693, 2779, "Gauge parts list"),
    ("Ga3", 2780, 2849, "Gauge parts list"),
    ("Wa1", 2850, 2898, "Warning labels"),
    ("Wa2", 2899, 2921, "Warning labels"),
]

# Ambil kode dengan format resmi seperti S48065-001 atau SB8096-001.
code_re = re.compile(r"\b[A-Z]{1,3}\d{4,6}-\d{3}\b")
rows = []
seen = set()

for section, start, end, section_name in sections:
    for line_no in range(start, min(end, len(lines)) + 1):
        line = lines[line_no - 1]
        codes = code_re.findall(line)
        if not codes:
            continue

        for code in codes:
            # Kode yang muncul pada gambar dapat berulang.
            # Deduplicasi hanya dalam bagian yang sama, bukan antarbagian.
            key = (section, code)
            if key in seen:
                continue
            seen.add(key)

            rows.append({
                "source_line": line_no,
                "section_code": section,
                "section_name": section_name,
                "part_number": code,
                "source_text": line.strip(),
                "review_status": "REVIEW_REQUIRED",
            })

fields = [
    "source_line", "section_code", "section_name",
    "part_number", "source_text", "review_status"
]
with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("Sumber:", src)
print("CSV tambahan:", out)
print("Jumlah kandidat kode unik per bagian:")
for section, _, _, _ in sections:
    subset = [r for r in rows if r["section_code"] == section]
    print(f"  {section}: {len(subset)}")
    for r in subset:
        print(f"    baris {r['source_line']}: {r['part_number']}")

print("\nCatatan:")
print("- Ini kandidat kode saja, belum inventaris final.")
print("- Ukuran gambar dan kuantitas belum ditafsirkan.")
print("- Database dan CSV kandidat utama tidak diubah.")
