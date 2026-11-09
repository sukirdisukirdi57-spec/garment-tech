import re
from collections import Counter
from pathlib import Path

FILE = Path("tmp/ams224en6030-section8/page21.txt")

pattern = re.compile(
    r'^\s*(\d{1,2})\s+'
    r'(?:(#01|☆)\s+)?'
    r'([A-Z0-9][A-Z0-9-]+)\s+'
    r'(.+?)\s+'
    r'(\(?\d+(?:\.\d+)?\)?)\s*$'
)

records = []

for line in FILE.read_text(errors="replace").splitlines():
    m = pattern.match(line)
    if m:
        ref, marker, number, name, qty = m.groups()
        records.append({
            "ref": int(ref),
            "marker": marker or "",
            "number": number,
            "name": name.strip(),
            "qty": qty
        })

refs = [r["ref"] for r in records]
numbers = Counter(r["number"] for r in records)

print("=== AUDIT SECTION 8 ===")
print("Jumlah REF terbaca:", len(records))
print("REF berurutan:", refs == list(range(1, 50)))
print("REF hilang:", sorted(set(range(1, 50)) - set(refs)))
print("REF duplikat:", sorted(
    ref for ref, count in Counter(refs).items() if count > 1
))
print("Nomor part unik:", len(numbers))

print("\n=== NOMOR PART BERULANG ===")
for number, count in numbers.items():
    if count > 1:
        print(number, ":", count, "kali")

print("\n=== PENANDA KATALOG ===")
for r in records:
    if r["marker"]:
        print(
            f"REF {r['ref']:02d} | {r['marker']} | "
            f"{r['number']} | {r['name']}"
        )

print("\n=== KUANTITAS DESIMAL ===")
for r in records:
    if "." in r["qty"]:
        print(f"REF {r['ref']:02d} | {r['number']} | {r['qty']}")

print("\n=== HASIL AKHIR ===")
if len(records) == 49 and refs == list(range(1, 50)):
    print("AUDIT STRUKTUR LULUS — 49 REF")
else:
    print("AUDIT BELUM LULUS — periksa hasil ekstraksi")
