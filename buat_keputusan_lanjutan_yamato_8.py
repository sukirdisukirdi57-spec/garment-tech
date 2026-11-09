import csv
from pathlib import Path

src = Path("audit_sumber_33_yamato_20261027.csv")
out = Path("keputusan_lanjutan_yamato_8_20261027.csv")

models = {
    "VM1804P-254-102": ("4", "8", "25,4 mm"),
    "VM1804P-NG-102": ("4", "8", "Tanpa needle gauge"),
    "VM1804PR-254-102": ("4", "8", "25,4 mm"),
    "VM1804PR-NG-102": ("4", "8", "Tanpa needle gauge"),
    "VM1806P-430-004": ("6", "12", "43,0 mm"),
    "VM1806P-NG-004": ("6", "12", "Tanpa needle gauge"),
    "VM1806PR-430-004": ("6", "12", "43,0 mm"),
    "VM1806PR-NG-004": ("6", "12", "Tanpa needle gauge"),
}

with src.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

assert len(rows) == 33, f"Jumlah baris tidak sesuai: {len(rows)}"

selected = [r for r in rows if r["model_public"].strip() in models]
assert len(selected) == 24, (
    f"Seharusnya 24 baris untuk 8 model, ditemukan {len(selected)}"
)

result = []
for r in selected:
    model = r["model_public"].strip()
    needles, threads, gauge = models[model]
    spec = r["specification_public"].strip()

    if spec == "Jenis mesin":
        finding = "Istilah sumber mendukung cylinder bed double-chainstitch."
    elif spec == "Jumlah benang":
        expected = threads
        finding = f"Konfigurasi sumber seri: {expected} benang."
    elif spec == "Jumlah jarum":
        expected = needles
        finding = f"Konfigurasi sumber seri: {expected} jarum."
    else:
        finding = "Perlu ditinjau manual."

    result.append({
        "server_specification_id": r["server_specification_id"],
        "local_specification_id": r["local_specification_id"],
        "model": model,
        "spesifikasi": spec,
        "nilai_public": r["value_public"],
        "nilai_lokal": r["value_lokal"],
        "jumlah_jarum_sumber": needles,
        "jumlah_benang_sumber": threads,
        "needle_gauge_sumber": gauge,
        "hasil_catatan": finding,
        "status_keputusan": "DRAF_PERLU_TINJAUAN",
        "catatan": (
            "Catatan konfigurasi sumber seri; pastikan halaman model individual "
            "sebelum mengubah status verifikasi atau nilai lokal."
        ),
        "source_url": r["source_url"],
    })

fields = list(result[0].keys())
with out.open("x", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(result)

print("File baru:", out)
print("Baris:", len(result))
print("Model:", len(set(r["model"] for r in result)))
print("Status:", "DRAF_PERLU_TINJAUAN")
print("CSV asli tidak diubah.")
print("Database tidak diubah.")
