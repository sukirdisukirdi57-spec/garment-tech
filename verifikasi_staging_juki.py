import csv
from pathlib import Path
from collections import Counter, defaultdict

FILE = Path("staging_kemunculan_katalog_juki.csv")

with FILE.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

# Cek duplikat Ref + nomor part pada halaman yang sama.
seen = defaultdict(list)
for r in rows:
    key = (
        r["pdf_page"],
        r["catalog_ref"],
        r["part_number"].upper().strip()
    )
    seen[key].append(r)

duplicates = {
    k: v for k, v in seen.items()
    if len(v) > 1
}

# Nomor part assembly yang menjadi patokan halaman.
targets = {
    6:  "400-29632",
    8:  "400-28338",
    10: "400-06836",
    12: "400-52937",
    14: "131-22452",
    16: "401-02213",
    20: "400-72009",
    22: "400-86363",
    23: "400-10503",
    28: "400-78001",
    30: "401-03969",
    32: "400-23638",
}

print("=== STATUS STAGING ===")
print("Total baris:", len(rows))
print("Jumlah halaman:", len(set(r["pdf_page"] for r in rows)))

print("\n=== DUPLIKAT REF + NOMOR PART DI HALAMAN SAMA ===")
print("Jumlah kelompok duplikat:", len(duplicates))
for (page, ref, pn), items in duplicates.items():
    print(f"PDF {page} | Ref {ref} | PN {pn} | {len(items)} baris")
    for item in items:
        print(" ", item["catalog_line_original"])

print("\n=== CEK NOMOR PART ASSEMBLY ===")
for page, pn in targets.items():
    found = [
        r for r in rows
        if r["pdf_page"] == str(page)
        and r["part_number"].upper().strip() == pn
    ]
    print(f"PDF {page}: {pn} -> {len(found)} baris")
    for r in found:
        print(" ", r["catalog_line_original"])

print("\n=== CONTOH BARIS PER HALAMAN ===")
for page in sorted(set(int(r["pdf_page"]) for r in rows)):
    page_rows = [r for r in rows if int(r["pdf_page"]) == page]
    print(f"\nPDF {page} — total {len(page_rows)} baris")
    for r in page_rows[:2] + page_rows[-2:]:
        print(" ", r["catalog_line_original"])

print("\nSelesai. File staging dan database tidak diubah.")
