import re
import sqlite3
from pathlib import Path
from collections import Counter

TXT = Path("tmp/ams224en6030-section6/page17.txt")
DB = "database/garment.db"

pattern = re.compile(
    r"^\s*(\d+)\s+"
    r"(?:(?:☆|\*)\s*)?"
    r"(?:#\d+\s+)?"
    r"([A-Z0-9][A-Z0-9-]+)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)

if not TXT.exists():
    raise SystemExit("File page17.txt tidak ditemukan.")

rows = []
for line_no, line in enumerate(TXT.read_text(errors="replace").splitlines(), 1):
    match = pattern.match(line)
    if match:
        ref, number, name, qty_raw = match.groups()
        rows.append({
            "ref": int(ref),
            "number": number,
            "name": name.strip(),
            "qty_raw": qty_raw,
            "line": line_no,
        })

refs = [r["ref"] for r in rows]
expected = list(range(1, 67))

print("=== AUDIT SECTION 6 ===")
print("Nama: PRESSER MECHANISM & PRESSER VARIABLE COMPONENTS (1)")
print("Diagram page: 16")
print("Parts page: 17")
print("REF terbaca:", len(rows))
print("REF berurutan:", refs == expected)

print("\n=== DAFTAR REF ===")
for r in rows:
    print(
        f"REF {r['ref']:02d} | {r['number']:<17} | "
        f"{r['name']} | QTY {r['qty_raw']}"
    )

print("\n=== NOMOR PART GANDA ===")
counts = Counter(r["number"] for r in rows)
duplicates = {
    number: [r["ref"] for r in rows if r["number"] == number]
    for number, count in counts.items() if count > 1
}
if duplicates:
    for number, ref_list in duplicates.items():
        print(number, ref_list)
else:
    print("Tidak ada")

print("\n=== QTY DESIMAL ===")
for r in rows:
    if "." in r["qty_raw"]:
        print(f"REF {r['ref']:02d}: {r['qty_raw']}")

print("\n=== PEMERIKSAAN DATABASE ===")
con = sqlite3.connect(DB)
for r in rows:
    found = con.execute("""
        SELECT id, catalog_ref, part_name
        FROM parts
        WHERE machine_id=47
          AND source_document_id=583
          AND part_number=?
    """, (r["number"],)).fetchall()

    if found:
        print(
            f"REF {r['ref']:02d} | {r['number']} | "
            f"Sudah ada di mesin: YA ({len(found)} occurrence)"
        )
con.close()

print("\n=== VALIDASI ===")
print("Total REF:", len(rows))
print("REF hilang:", sorted(set(expected) - set(refs)))
print("REF duplikat:", sorted(
    ref for ref, count in Counter(refs).items() if count > 1
))
print("Nomor part unik:", len(counts))

if refs == expected and len(rows) == 66:
    print("STATUS: 66 REF LENGKAP")
else:
    print("STATUS: PERLU PEMERIKSAAN")
