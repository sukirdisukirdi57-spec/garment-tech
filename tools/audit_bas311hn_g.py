import csv
from pathlib import Path
from collections import Counter

source = Path("tmp/bas311hn/g_staging_review.csv")
target = Path("tmp/bas311hn/g_staging_audited.csv")

if target.exists():
    raise SystemExit(
        f"BERHENTI: {target} sudah ada. "
        "Tidak ada file yang ditimpa."
    )

with source.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 54:
    raise SystemExit(f"BERHENTI: jumlah baris tidak sesuai: {len(rows)}")

refs = [int(r["catalog_ref"]) for r in rows]
if sorted(refs) != list(range(1, 55)):
    raise SystemExit("BERHENTI: ref katalog hilang atau duplikat.")

for r in rows:
    ref = int(r["catalog_ref"])

    if ref in (23, *range(40, 49)):
        r["verification"] = "VERIFIED_NOT_APPLICABLE"
        if ref == 23:
            r["review_note"] = (
                "Tabel variasi halaman 73 tidak mencantumkan "
                "kode washer yang berlaku untuk -03S."
            )
        elif ref == 40:
            r["review_note"] = (
                "Kelompok -07A; kuantitas kosong pada katalog. "
                "Tidak diterapkan ke -03S."
            )
        elif ref == 48:
            r["review_note"] = (
                "Tension spring kelompok -07A; kode 107606-101 "
                "tercantum hanya pada kolom -07A halaman 73."
            )
        else:
            r["review_note"] = (
                "Termasuk kelompok For -07A pada halaman 35; "
                "tidak diterapkan ke -03S."
            )

    elif ref in (19, 22, 24):
        r["verification"] = "VERIFIED"
        r["review_note"] = (
            "Kode diverifikasi melalui Different parts list "
            "halaman 73 untuk varian -03S/-03A."
        )

    elif 25 <= ref <= 39:
        r["verification"] = "VERIFIED"
        r["review_note"] = (
            "Kode dan kuantitas cocok dengan katalog halaman 35; "
            "kelompok For -03[],-05[] mencakup -03S."
        )

    elif 50 <= ref <= 54:
        r["verification"] = "VERIFIED"
        r["review_note"] = (
            "Kode, kuantitas, dan nama cocok dengan halaman 35. "
            "Katalog menandai kelompok ini sebagai Option parts, "
            "bukan komponen standar."
        )

    else:
        r["verification"] = "VERIFIED"
        r["review_note"] = (
            "Kode, kuantitas, dan nama cocok dengan daftar "
            "resmi halaman 35."
        )

with target.open("x", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

counts = Counter(r["verification"] for r in rows)
print("FILE AUDIT:", target)
print("TOTAL BARIS:", len(rows))
print("STATUS:", dict(counts))
print("REF UNIK:", len(set(refs)))
print("DATABASE DIUBAH: TIDAK")
print("IMPORT DIJALANKAN: TIDAK")
