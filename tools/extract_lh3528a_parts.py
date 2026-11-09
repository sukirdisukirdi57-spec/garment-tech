import csv
import re
import subprocess
from pathlib import Path

PDF = Path("tmp/lh3528a/partslist.pdf")
OUT = Path("tmp/lh3528a/parts_staging_v1.csv")

# section -> (pdf page, diagram page)
PAGES = {
    1:  (7, 1),
    2:  (9, 3),
    3:  (11, 5),
    5:  (15, 9),
    6:  (17, 11),
    8:  (21, 15),
    10: (25, 19),
    11: (27, 21),
    12: (29, 23),
    14: (33, 27),
    16: (37, 31),
    18: (41, 35),
    19: (42, 37),
    20: (43, 38),
    21: (45, 39),
    22: (47, 41),
}

pattern = re.compile(
    r'^\s*(\d+)\s+'
    r'(?:(☆|＊)\s+)?'
    r'(?:(#\d+)\s+)?'
    r'([A-Z0-9][A-Z0-9._/-]*)\s+'
    r'(.+?)\s+'
    r'(\(?\d+(?:\.\d+)?\)?)\s*$'
)

rows = []

for section, (pdf_page, diagram_page) in PAGES.items():
    result = subprocess.run(
        [
            "pdftotext", "-f", str(pdf_page), "-l", str(pdf_page),
            "-layout", str(PDF), "-"
        ],
        capture_output=True,
        text=True,
        errors="replace",
        check=True,
    )

    for line in result.stdout.splitlines():
        if line.strip().startswith("REF.NO"):
            continue

        m = pattern.match(line)
        if not m:
            continue

        ref_no, symbol, note_code, part_no, description, qty_raw = m.groups()

        quantity = None
        quantity_raw = None

        if qty_raw.startswith("("):
            quantity_raw = qty_raw
        elif "." in qty_raw:
            quantity_raw = qty_raw
        else:
            quantity = int(qty_raw)

        notes = []
        if symbol:
            notes.append(symbol)
        if note_code:
            notes.append(note_code)

        rows.append({
            "machine_id": 18,
            "source_document_id": 16,
            "part_number": part_no,
            "part_name": description.strip(),
            "quantity": quantity,
            "catalog_ref": int(ref_no),
            "diagram_page": diagram_page,
            "note": " ".join(notes) if notes else None,
            "source_url": None,
            "notes": None,
            "quantity_raw": quantity_raw,
            "pdf_page": pdf_page,
            "section": section,
        })

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Rows: {len(rows)}")
print(f"Output: {OUT}")
