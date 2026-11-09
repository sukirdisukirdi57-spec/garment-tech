import csv
from pathlib import Path
from collections import Counter

src = Path("audit_lanjutan_sumber_resmi_yamato_57_20261027.csv")
out = Path("audit_sumber_33_yamato_20261027.csv")

with src.open(newline="", encoding="utf-8-sig") as f:
    all_rows = list(csv.DictReader(f))

rows = [
    r for r in all_rows
    if r["verification_status_public"].strip() == "Terverifikasi"
]

if len(rows) != 33:
    raise SystemExit(f"Dihentikan: diharapkan 33 baris, ditemukan {len(rows)}")

series_url = (
    "https://www.yamato-sewing.com/en/product/"
    "double_chain_stitch/vm/specifications/"
)

model_urls = {
    "VM1804P-254-102": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804p-254-102/",
    "VM1804P-300-102": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/",
    "VM1804P-382-102": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/",
    "VM1804P-NG-102": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804p-ng-102/",
    "VM1804PR-254-102": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804pr-254-102/",
    "VM1804PR-300-102": series_url,
    "VM1804PR-NG-102": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804pr-ng-102/",
    "VM1806P-430-004": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1806p-430-004/",
    "VM1806P-NG-004": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1806p-ng-004/",
    "VM1806PR-430-004": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1806pr-430-004/",
    "VM1806PR-NG-004": "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1806pr-ng-004/",
}

for r in rows:
    model = r["model_public"].strip()
    if model not in model_urls:
        raise SystemExit(f"Model belum dipetakan: {model}")

    spec = r["specification_public"].strip().lower()
    value = r["value_public"].strip()

    if model_urls[model] == series_url:
        evidence = "PERLU_COCOKKAN_TABEL_SERI"
    else:
        evidence = "PERLU_COCOKKAN_HALAMAN_MODEL"

    if spec == "jenis mesin":
        recommendation = "TINJAU_PENYELARASAN_ISTILAH"
    elif spec == "jumlah benang":
        expected = "8" if model.startswith("VM1804") else "12"
        recommendation = (
            "NILAI_ANGKA_SESUAI_POLA_SERI"
            if value == expected else "PERIKSA_KETIDAKSESUAIAN_NILAI"
        )
    elif spec == "jumlah jarum":
        expected = "4" if model.startswith("VM1804") else "6"
        recommendation = (
            "NILAI_ANGKA_SESUAI_POLA_SERI"
            if value == expected else "PERIKSA_KETIDAKSESUAIAN_NILAI"
        )
    else:
        recommendation = "TINJAU_MANUAL"

    r.update({
        "url_sumber_untuk_diperiksa": model_urls[model],
        "metode_pemeriksaan": evidence,
        "rekomendasi_audit_33": recommendation,
        "status_keputusan": "BELUM_ADA_PERSETUJUAN_PERUBAHAN",
    })

fields = list(rows[0].keys()) + [
    "url_sumber_untuk_diperiksa",
    "metode_pemeriksaan",
    "rekomendasi_audit_33",
    "status_keputusan",
]

with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("File dibuat:", out)
print("Jumlah baris:", len(rows))
print("Jumlah model:", len(set(r["model_public"] for r in rows)))
print("\nMetode pemeriksaan:")
for k, v in Counter(r["metode_pemeriksaan"] for r in rows).items():
    print(f"- {k}: {v}")

print("\nRekomendasi:")
for k, v in Counter(r["rekomendasi_audit_33"] for r in rows).items():
    print(f"- {k}: {v}")

print("\nStatus public asli dipertahankan.")
print("Database lokal dan public tidak diubah.")
