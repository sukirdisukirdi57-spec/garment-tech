import re
import csv

PDF_TEXT = "tmp/lbh1790an/partslist.txt"
OUTPUT = "tmp/lbh1790an/parts_staging.csv"

rows = []
current_page = 1

part_pattern = re.compile(
    r"^\s*(\d+)\s+"
    r"(.*?)\s+"
    r"([A-Z0-9][A-Z0-9-]*-\d[A-Z0-9-]*)\s+"
    r"(.+?)\s+"
    r"(\(?\d+\)?)\s*$"
)

with open(PDF_TEXT, encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.rstrip()

        if "\f" in line:
            current_page += line.count("\f")
            line = line.replace("\f", "")

        m = part_pattern.match(line)

        if not m:
            continue

        ref_no, note, part_no, description, qty = m.groups()

        rows.append({
            "catalog_ref": ref_no,
            "note": note.strip(),
            "part_number": part_no.strip(),
            "part_name": description.strip(),
            "quantity_raw": qty.strip(),
            "diagram_page": current_page,
        })

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "catalog_ref",
            "note",
            "part_number",
            "part_name",
            "quantity_raw",
            "diagram_page",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Extracted: {len(rows)} rows")
print(f"Output: {OUTPUT}")
