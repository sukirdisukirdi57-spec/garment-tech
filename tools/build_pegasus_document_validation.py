import csv
from pathlib import Path

out = Path("tools/pegasus_document_validation_results.csv")

manual_catalog = (
    "https://www.pegasus.co.jp/webcatalog/?filter=manual&lang=en"
)
parts_catalog = (
    "https://www.pegasus.co.jp/webcatalog/?filter=parts&lang=en"
)
ex5400_manual = (
    "https://www.pegasus.co.jp/webcatalog/file.php"
    "?docflg=1&itemcd=9B2057000009&pageseq=1&rev=00"
)

records = [
    [532, "E22L", "Manual", manual_catalog,
     "TERCANTUM_DI_KATALOG", "Cari tautan langsung; belum diubah"],
    [533, "E22L", "Parts List", parts_catalog,
     "TERCANTUM_DI_KATALOG_PARTS", "Verifikasi katalog khusus model"],
    [526, "E256", "Manual", manual_catalog,
     "TERCANTUM_DI_KATALOG", "Cari tautan langsung; belum diubah"],
    [527, "E256", "Parts List", parts_catalog,
     "TERCANTUM_DI_KATALOG_PARTS", "Verifikasi katalog khusus model"],
    [528, "EX5400", "Manual", ex5400_manual,
     "MANUAL_LANGSUNG_TERVERIFIKASI",
     "Cat. No. 9B2057000009; September 2019"],
    [529, "EX5400", "Parts List", parts_catalog,
     "TERCANTUM_DI_KATALOG_PARTS", "Cari tautan parts langsung"],
    [530, "TML326", "Manual", manual_catalog,
     "BELUM_TERVERIFIKASI", "Jangan ganti URL sebelum ada bukti"],
    [531, "TML326", "Parts List", parts_catalog,
     "BELUM_TERVERIFIKASI", "Jangan ganti URL sebelum ada bukti"],
]

fields = [
    "document_id", "model", "document_type",
    "verified_or_current_url", "validation_status",
    "review_note", "database_action"
]

out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(fields)
    for row in records:
        w.writerow(row + ["NONE_PENDING_APPROVAL"])

print("Laporan validasi:", out)
print("Dokumen ditinjau:", len(records))
print("Manual langsung terverifikasi:", sum(
    r[4] == "MANUAL_LANGSUNG_TERVERIFIKASI" for r in records
))
print("Database diubah: TIDAK")
