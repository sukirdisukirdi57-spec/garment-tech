import csv
from pathlib import Path
from collections import Counter

src = Path("audit_lanjutan_sumber_resmi_yamato_57_20261027.csv")
out = Path("hasil_verifikasi_model_yamato_24_20261027.csv")

with src.open(newline="", encoding="utf-8-sig") as f:
    all_rows = list(csv.DictReader(f))

rows = [
    r for r in all_rows
    if r["verification_status_public"].strip() == "Perlu Verifikasi"
]

if len(rows) != 24:
    raise SystemExit(f"Dihentikan: seharusnya 24 baris, ditemukan {len(rows)}")

model_sources = {
    "VM1804P-254-003": (
        "HALAMAN_MODEL_RESMI_DIPERIKSA",
        "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804p-254-003/"
    ),
    "VM1804P-300-003": (
        "HALAMAN_MODEL_RESMI_DIPERIKSA",
        "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804p-300-003/"
    ),
    "VM1804P-382-003": (
        "HALAMAN_MODEL_RESMI_DIPERIKSA",
        "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804p-382-003/"
    ),
    "VM1804P-NG-003": (
        "HALAMAN_MODEL_RESMI_DIPERIKSA",
        "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804p-ng-003/"
    ),
    "VM1804PR-254-003": (
        "HALAMAN_MODEL_RESMI_DIPERIKSA",
        "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804pr-254-003/"
    ),
    "VM1804PR-300-003": (
        "HALAMAN_MODEL_RESMI_DIPERIKSA",
        "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804pr-300-003/"
    ),
    "VM1804PR-382-102": (
        "TABEL_SERI_RESMI_DIPERIKSA",
        "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/"
    ),
    "VM1804PR-NG-003": (
        "HALAMAN_MODEL_RESMI_DIPERIKSA",
        "https://www.yamato-sewing.com/en/product/double_chain_stitch/vm/specifications/vm1804pr-ng-003/"
    ),
}

new_columns = [
    "hasil_pemeriksaan_sumber",
    "url_sumber_diperiksa",
    "keputusan_audit",
    "catatan_status_public",
]

for r in rows:
    model = r["model_public"].strip()
    if model not in model_sources:
        raise SystemExit(f"Model belum dipetakan: {model}")

    hasil, url = model_sources[model]
    spec = r["specification_public"].strip().lower()

    if spec == "jenis mesin":
        keputusan = "SUMBER_MENDUKUNG_JENIS_MESIN"
    elif spec == "jumlah benang":
        keputusan = "SUMBER_MENDUKUNG_8_BENANG"
    elif spec == "jumlah jarum":
        keputusan = "SUMBER_MENDUKUNG_4_JARUM"
    else:
        keputusan = "PERLU_TINJAUAN_MANUAL"

    r.update({
        "hasil_pemeriksaan_sumber": hasil,
        "url_sumber_diperiksa": url,
        "keputusan_audit": keputusan,
        "catatan_status_public": (
            "Status public Perlu Verifikasi dipertahankan. "
            "Catatan ini adalah hasil audit sumber, bukan perubahan status public "
            "atau persetujuan perubahan database."
        ),
    })

fields = list(rows[0].keys()) + new_columns

with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("File dibuat:", out)
print("Jumlah baris:", len(rows))
print("Jumlah model:", len(set(r["model_public"] for r in rows)))
print("Kategori keputusan:")
for k, v in Counter(r["keputusan_audit"] for r in rows).items():
    print(f"- {k}: {v}")

print("\nStatus public tetap Perlu Verifikasi pada file sumber.")
print("Database lokal dan public tidak diubah.")
