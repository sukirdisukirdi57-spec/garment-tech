import csv
import re
import subprocess
from pathlib import Path

PDF = Path("tmp/lbh1790an/partslist.pdf")
OUT = Path("tmp/lbh1790an/parts_staging_v2.csv")

# PDF page 7 = diagram page 1
# PDF page 9 = diagram page 3
# Numerical index mulai setelah diagram page 39.
PDF_FIRST = 7
PDF_LAST = 45

# Diagram pages yang berlaku untuk LBH-1790AN.
# Section 6 (LBH-1795ANS) dan section 12 (LBH-1790ANB) dikeluarkan.
EXCLUDE_DIAGRAM = set(range(11, 13)) | {23}

pattern = re.compile(
    r'^\s*(\d+)\s+'
    r'(?:(☆|◎|\*|#\d+)\s+)?'
    r'([A-Z0-9][A-Z0-9._/-]*)\s+'
    r'(.+?)\s+'
    r'(\(?\d+(?:\.\d+)?\)?)\s*$'
)

rows = []
page_counts = {}
bad_lines = 0

for pdf_page in range(PDF_FIRST, PDF_LAST + 1):
    diagram_page = pdf_page - 6

    if diagram_page in EXCLUDE_DIAGRAM:
        continue

    result = subprocess.run(
        [
            "pdftotext",
            "-f", str(pdf_page),
            "-l", str(pdf_page),
            "-layout",
            str(PDF),
            "-"
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    count = 0

    for line in result.stdout.splitlines():
        m = pattern.match(line)
        if not m:
            continue

        ref, note, part_no, part_name, qty_raw = m.groups()

        # Abaikan baris yang jelas bukan nomor part.
        if len(part_no) < 3:
            continue

        # Integer biasa masuk quantity.
        # Decimal / parenthesized quantity tetap disimpan di quantity_raw.
        quantity = ""
        if re.fullmatch(r'\d+', qty_raw):
            quantity = qty_raw

        rows.append({
            "machine_id": 6,
            "source_document_id": 119,
            "part_number": part_no,
            "part_name": part_name.strip(),
            "quantity": quantity,
            "catalog_ref": ref,
            "diagram_page": diagram_page,
            "note": note or "",
            "quantity_raw": qty_raw,
        })

        count += 1

    page_counts[diagram_page] = count

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "machine_id",
            "source_document_id",
            "part_number",
            "part_name",
            "quantity",
            "catalog_ref",
            "diagram_page",
            "note",
            "quantity_raw",
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"CSV dibuat : {OUT}")
print(f"Total rows : {len(rows)}")
print(f"Unique part numbers : {len(set(r['part_number'] for r in rows))}")
print()
print("Per diagram page:")
for page, count in sorted(page_counts.items()):
    if count:
        print(f"  {page:2} : {count}")
