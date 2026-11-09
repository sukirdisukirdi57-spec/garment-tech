import sqlite3
import subprocess
import re
from collections import defaultdict

PDF = "audit-kelengkapan/ams224en6030/partslist.pdf"
DB = "database/garment.db"

result = subprocess.run(
    ["pdftotext", "-f", "15", "-l", "15", "-layout", PDF, "-"],
    capture_output=True,
    text=True,
    check=True
)

pattern = re.compile(
    r"^\s*(\d+)\s+"
    r"(?:(?:☆|\*)\s*)?"
    r"(?:#\d+\s+)?"
    r"([A-Z0-9][A-Z0-9-]+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)

catalog = []

for line in result.stdout.splitlines():
    m = pattern.match(line)
    if not m:
        continue

    ref, number, name, qty = m.groups()

    catalog.append({
        "ref": int(ref),
        "number": number,
        "name": name.strip(),
        "qty": qty
    })

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

parts = con.execute("""
    SELECT id, part_number, part_name, catalog_ref,
           source_document_id, notes
    FROM parts
    WHERE machine_id=47
      AND source_document_id=583
    ORDER BY id
""").fetchall()

by_number = defaultdict(list)

for p in parts:
    by_number[p["part_number"]].append(p)

print("=== AUDIT MAIN SHAFT & NEEDLE BAR ===")
print("REF terbaca:", len(catalog))
print("REF berurutan:", [x["ref"] for x in catalog] ==
      list(range(1, 68)))
print("Part database:", len(parts))

print("\n=== DAFTAR 67 REF ===")

for x in catalog:
    matches = by_number[x["number"]]

    print(
        f"REF {x['ref']:02d} | {x['number']:18s} | "
        f"{x['name']} | QTY {x['qty']} | "
        f"Sudah ada di mesin: {'YA' if matches else 'TIDAK'}"
    )

    for p in matches:
        print(
            f"    DB ID={p['id']} "
            f"REF_DB={p['catalog_ref']} "
            f"NAME={p['part_name']}"
        )

print("\n=== REF GANDA ===")

duplicates = defaultdict(list)

for x in catalog:
    duplicates[x["number"]].append(x["ref"])

for number, refs in duplicates.items():
    if len(refs) > 1:
        print(number, refs)

print("\n=== VALIDASI ===")
print("Total REF:", len(catalog))
print("Total nomor unik:", len(set(x["number"] for x in catalog)))
print("REF hilang:", sorted(
    set(range(1, 68)) - {x["ref"] for x in catalog}
))
print("REF duplikat:", sorted(
    ref for ref in {x["ref"] for x in catalog}
    if sum(y["ref"] == ref for y in catalog) > 1
))

if len(catalog) == 67 and [x["ref"] for x in catalog] == list(range(1, 68)):
    print("STATUS: 67 REF LENGKAP")
else:
    print("STATUS: AUDIT BELUM LULUS")

con.close()
