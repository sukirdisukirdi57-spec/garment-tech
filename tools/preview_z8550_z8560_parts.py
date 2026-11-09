import csv
import re
from pathlib import Path

txt_path = Path("tools/z8550b_z8560b_parts_layout.txt")
out_path = Path("tools/z8550b_z8560b_parts_candidates.csv")

text = txt_path.read_text(encoding="utf-8", errors="replace").splitlines()

sections = {
    "A": "Machine body",
    "B": "Needle bar and thread take-up mechanism",
    "C": "Zigzag mechanism",
    "D": "Presser foot mechanism",
    "E": "Feed mechanism",
    "F": "Knee lifter mechanism",
    "G": "Reverse mechanism",
    "H": "Rotary hook mechanism",
    "J": "Lubrication",
    "K": "Threading mechanism",
    "L": "Bobbin winder mechanism",
    "M1": "Thread trimmer mechanism",
    "M2": "Thread trimmer mechanism",
    "N": "Thread tension mechanism",
    "P": "Thread wiper mechanism",
    "Q1": "Control box",
    "Q2": "Control box",
    "R": "Reverse switch mechanism",
    "S": "Electrical parts",
    "T": "Operation panel",
    "U": "Motor mechanism",
    "Z": "Accessories",
    "Ga1": "Gauge parts list",
    "Ga2": "Gauge parts list",
    "Ga3": "Gauge parts list",
}

current_section = ""
rows = []

for line_no, line in enumerate(text, 1):
    # Heading examples: "A. / Machine body" or "Ga1. / Gauge parts list"
    heading = re.match(
        r"^\s*(Ga[123]|M[12]|Q[12]|[A-Z])\.\s+.*?/+\s*(.*?)\s*$",
        line
    )
    if heading:
        current_section = heading.group(1)
        continue

    # Candidate row: ref, part code, quantity, Japanese text, English name
    m = re.match(
        r"^\s*(\d+\+?)\s+([A-Z0-9]{6,12})\s+(\d+)\s+(.+?)\s{2,}([A-Z][A-Z0-9 /().,+&'-]{2,})\s*$",
        line
    )
    if not m:
        continue

    ref, code, qty, name_jp, name_en = m.groups()
    rows.append({
        "source_line": line_no,
        "section_code": current_section,
        "section_name": sections.get(current_section, ""),
        "catalog_ref_raw": ref,
        "catalog_ref_numeric": re.sub(r"\+$", "", ref),
        "has_plus_variant": "yes" if ref.endswith("+") else "no",
        "part_number": code,
        "quantity": int(qty),
        "part_name_en": name_en.strip(),
        "part_name_jp": name_jp.strip(),
        "review_status": "REVIEW_REQUIRED",
    })

fields = [
    "source_line", "section_code", "section_name",
    "catalog_ref_raw", "catalog_ref_numeric", "has_plus_variant",
    "part_number", "quantity", "part_name_en", "part_name_jp",
    "review_status",
]

with out_path.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("Sumber:", txt_path)
print("Kandidat hasil ekstraksi:", len(rows))
print("Referensi bertanda +:", sum(r["has_plus_variant"] == "yes" for r in rows))
print("CSV:", out_path)

print("\n=== Ringkasan per bagian ===")
counts = {}
for row in rows:
    key = (row["section_code"], row["section_name"])
    counts[key] = counts.get(key, 0) + 1

for (code, name), count in counts.items():
    print(f"{code:3} | {name:40} | {count:4} baris")

print("\n=== 20 kandidat pertama ===")
for row in rows[:20]:
    print(
        f"Baris {row['source_line']:4} | {row['section_code']:3} "
        f"| Ref {row['catalog_ref_raw']:4} | {row['part_number']:12} "
        f"| Qty {row['quantity']:2} | {row['part_name_en']}"
    )

print("\nCatatan: hasil ekstraksi otomatis adalah kandidat, bukan data siap impor.")
