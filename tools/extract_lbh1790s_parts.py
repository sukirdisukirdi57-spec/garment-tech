import csv
import re
from pathlib import Path

src = Path("tmp/lbh1790s/partslist.txt")
out = Path("tmp/lbh1790s/parts_staging_v1.csv")

text = src.read_text(errors="replace").splitlines()

# PDF table pages containing normal parts:
# section 1-12, 14-17
table_pages = {
    1: 4, 3: 7, 5: 9, 7: 11, 9: 13, 11: 15,
    13: 17, 15: 19, 17: 21, 19: 23, 21: 25, 23: 27,
    27: 31, 29: 33, 31: 35, 33: 37
}

pattern = re.compile(
    r'^\s*(\d+)\s+'
    r'(?:(☆|◎|\*|＊)\s+)?'
    r'(?:(#\d+)\s+)?'
    r'([A-Z0-9][A-Z0-9._/-]*)\s+'
    r'(.+?)\s+'
    r'(\(?\d+(?:\.\d+)?\)?)\s*$'
)

# Find each REF.NO header and associate it with the next table section.
headers = []
for i, line in enumerate(text):
    if "REF.NO" in line and "PART NO" in line and "DESCRIPTION" in line:
        headers.append(i)

rows = []

# Printed diagram pages for the 17 standard parts sections.
diagram_pages = [
    1, 3, 5, 7, 9, 11, 13, 15, 17,
    19, 21, 23, 27, 29, 31, 33
]

for idx, header_pos in enumerate(headers):
    if idx >= len(diagram_pages):
        break

    start = header_pos + 1
    end = headers[idx + 1] if idx + 1 < len(headers) else len(text)

    diagram_page = diagram_pages[idx]

    for line in text[start:end]:
        m = pattern.match(line)
        if not m:
            continue

        ref_no, marker, note_code, part_no, description, qty_raw = m.groups()

        note_parts = []
        if marker:
            note_parts.append(marker)
        if note_code:
            note_parts.append(note_code)

        note = " ".join(note_parts) if note_parts else None

        if qty_raw.startswith("(") and qty_raw.endswith(")"):
            quantity = None
            quantity_raw = qty_raw
        elif "." in qty_raw:
            quantity = None
            quantity_raw = qty_raw
        else:
            quantity = int(qty_raw)
            quantity_raw = None

        rows.append({
            "diagram_page": diagram_page,
            "catalog_ref": int(ref_no),
            "note": note,
            "part_number": part_no,
            "part_name": description.strip(),
            "quantity": quantity,
            "quantity_raw": quantity_raw,
        })

fields = [
    "diagram_page",
    "catalog_ref",
    "note",
    "part_number",
    "part_name",
    "quantity",
    "quantity_raw",
]

with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"Created: {out}")
print(f"Rows: {len(rows)}")
print(f"Unique part numbers: {len(set(r['part_number'] for r in rows))}")
