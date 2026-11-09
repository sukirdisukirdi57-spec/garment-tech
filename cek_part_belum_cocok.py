import sqlite3
import csv
import re
from pathlib import Path
from collections import Counter

DB = Path("database/garment.db")
SOURCE = Path("baris_belum_cocok_juki.csv")
OUT = Path("audit_status_118_part.csv")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

results = []

with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    source_rows = list(csv.DictReader(f))

for row in source_rows:
    line = row["catalog_line"].strip()

    # Ref. katalog adalah angka pertama pada baris.
    mref = re.match(r"^(\d+)\s+", line)
    ref = mref.group(1) if mref else ""

    # Nomor part adalah token berkode yang mengandung tanda hubung.
    tokens = re.findall(r"(?<![A-Z0-9])[A-Z0-9]+(?:-[A-Z0-9]+)+(?![A-Z0-9])", line)
    pn = tokens[0] if tokens else ""

    found = con.execute("""
        SELECT id, catalog_ref, part_number, part_name, quantity
        FROM parts
        WHERE machine_id = 43
          AND UPPER(TRIM(part_number)) = UPPER(TRIM(?))
        ORDER BY id
    """, (pn,)).fetchall() if pn else []

    if not pn:
        status = "NOMOR PART GAGAL DIBACA"
        db_info = ""
    elif not found:
        status = "PN TIDAK ADA DI DATABASE"
        db_info = ""
    elif any(str(x["catalog_ref"]).strip() == ref for x in found):
        status = "PN DAN REF ADA — CEK FORMAT BARIS"
        db_info = "; ".join(
            f"ID{x['id']} Ref{x['catalog_ref']} Qty{x['quantity']}"
            for x in found
        )
    else:
        status = "PN ADA, REF BERBEDA"
        db_info = "; ".join(
            f"ID{x['id']} Ref{x['catalog_ref']} Qty{x['quantity']}"
            for x in found
        )

    results.append({
        "pdf_page": row["pdf_page"],
        "catalog_ref": ref,
        "part_number": pn,
        "catalog_line": line,
        "status": status,
        "database_matches": db_info,
    })

with OUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "pdf_page", "catalog_ref", "part_number",
        "catalog_line", "status", "database_matches"
    ])
    writer.writeheader()
    writer.writerows(results)

counts = Counter(x["status"] for x in results)

print("=== STATUS 118 BARIS ===")
for status, count in counts.items():
    print(f"{status}: {count}")

print("\n=== 30 BARIS PERTAMA ===")
for x in results[:30]:
    print(
        f"PDF {x['pdf_page']} | Ref {x['catalog_ref']} | "
        f"{x['part_number']} | {x['status']}"
    )
    if x["database_matches"]:
        print("  DB:", x["database_matches"])

print("\nFile laporan:", OUT)
print("DATABASE TIDAK DIUBAH.")
con.close()
