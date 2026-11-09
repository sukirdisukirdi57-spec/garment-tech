import re
from pathlib import Path
from collections import Counter

source = Path("tmp/ams224en6030-section7/page19.txt")

if not source.is_file():
    raise SystemExit("File halaman 19 tidak ditemukan.")

text = source.read_text(errors="replace")

records = []

for line in text.splitlines():
    m = re.match(
        r'^\s*(\d{1,2})\s+'
        r'([A-Z0-9][A-Z0-9-]+)\s+'
        r'(.+?)\s+'
        r'(\(?\d+(?:\.\d+)?\)?)\s*$',
        line
    )

    if not m:
        continue

    ref = int(m.group(1))
    part_no = m.group(2)
    description = re.sub(r'\s+', ' ', m.group(3)).strip()
    qty = m.group(4)

    records.append({
        "ref": ref,
        "part_no": part_no,
        "description": description,
        "qty": qty,
    })

refs = [r["ref"] for r in records]
part_numbers = [r["part_no"] for r in records]

missing = sorted(set(range(1, 55)) - set(refs))
duplicates = sorted(
    ref for ref, count in Counter(refs).items() if count > 1
)

duplicate_parts = {
    part: count
    for part, count in Counter(part_numbers).items()
    if count > 1
}

print("=== AUDIT SECTION 7 ===")
print("Judul: PRESSER MECHANISM & PRESSER VARIABLE COMPONENTS (2)")
print("Jumlah record:", len(records))
print("Part number unik:", len(set(part_numbers)))
print("REF pertama:", min(refs) if refs else None)
print("REF terakhir:", max(refs) if refs else None)
print("REF hilang:", missing)
print("REF duplikat:", duplicates)

print("\n=== PART NUMBER BERULANG ===")
for part, count in duplicate_parts.items():
    print(part, ":", count, "occurrence")

print("\n=== HASIL PEMBACAAN ===")
for r in records:
    print(
        f'{r["ref"]:02d}|{r["part_no"]}|'
        f'{r["description"]}|{r["qty"]}'
    )

valid = (
    len(records) == 54
    and refs == list(range(1, 55))
    and not missing
    and not duplicates
    and all(r["description"] for r in records)
)

print("\n=== STATUS ===")
print("AUDIT LULUS" if valid else "AUDIT PERLU DIPERIKSA")
