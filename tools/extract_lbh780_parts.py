import csv
import re
from pathlib import Path

SRC = Path("tmp/lbh780/partslist.txt")
OUT = Path("tmp/lbh780/parts_staging_v1.csv")

text = SRC.read_text(encoding="utf-8")
lines = text.splitlines()

# Diagram/parts-list pages yang memang berisi tabel parts.
# Section 11 (change list) dan numerical index tidak diambil.
section_pages = {
    1: 1,
    2: 3,
    3: 5,
    4: 7,
    5: 8,
    6: 9,
    7: 11,
    8: 12,
    9: 13,
    10: 15,
}

headers = [i for i, line in enumerate(lines) if "REF.NO" in line and "PART NO" in line]

rows = []

pattern = re.compile(
    r'^\s*(\d+)\s+'
    r'(?:(#\d+|\*|☆|◎)\s+)?'
    r'([A-Z0-9][A-Z0-9._/-]*)\s+'
    r'(.+?)\s+'
    r'(\(?\d+(?:\.\d+)?\)?)\s*$'
)

for idx, header_line in enumerate(headers):
    section = idx + 1

    if section not in section_pages:
        continue

    start = header_line + 1
    end = headers[idx + 1] if idx + 1 < len(headers) else len(lines)

    diagram_page = section_pages[section]

    for line in lines[start:end]:
        m = pattern.match(line)
        if not m:
            continue

        ref_no, marker, part_no, description, qty_raw = m.groups()
        if part_no.isdigit():
            continue

        note = marker or ""
        quantity = None
        quantity_raw = None

        if qty_raw.startswith("(") and qty_raw.endswith(")"):
            quantity_raw = qty_raw
        elif "." in qty_raw:
            quantity_raw = qty_raw
        else:
            quantity = int(qty_raw)

        rows.append({
            "machine_model": "LBH-780",
            "section": section,
            "catalog_ref": int(ref_no),
            "diagram_page": diagram_page,
            "part_number": part_no,
            "part_name": description.strip(),
            "quantity": quantity,
            "quantity_raw": quantity_raw,
            "note": note,
        })

OUT.parent.mkdir(parents=True, exist_ok=True)

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "machine_model",
            "section",
            "catalog_ref",
            "diagram_page",
            "part_number",
            "part_name",
            "quantity",
            "quantity_raw",
            "note",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"STAGING OK: {len(rows)} rows")
print(f"OUTPUT: {OUT}")
