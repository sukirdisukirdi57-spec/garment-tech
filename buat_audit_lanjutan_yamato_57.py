import csv
from pathlib import Path
from collections import Counter

src = Path("keputusan_audit_spesifikasi_57_20261027.csv")
out = Path("audit_lanjutan_sumber_resmi_yamato_57_20261027.csv")

if not src.exists():
    raise SystemExit(f"File sumber tidak ditemukan: {src}")

with src.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 57:
    raise SystemExit(f"Audit dihentikan: seharusnya 57 baris, ditemukan {len(rows)}")

new_columns = [
    "hasil_pemeriksaan_sumber_resmi",
    "catatan_verifikasi_model",
    "rekomendasi_lanjutan",
    "status_keputusan_final",
]

for r in rows:
    model = (r.get("model_public") or r.get("model_lokal") or "").strip()
    spec = r["specification_public"].strip().lower()
    public_status = r["verification_status_public"].strip()

    if spec == "jenis mesin":
        hasil = (
            "Sumber resmi seri VM mendukung istilah Cylinder Bed "
            "dan Double Chain Stitch."
        )
        catatan = (
            "Cocokkan kode model secara individual dengan halaman spesifikasi "
            "resmi; halaman seri saja tidak menggantikan pemeriksaan setiap model."
        )
        rekomendasi = (
            "PERTIMBANGKAN_PENYELARASAN_ISTILAH_SETELAH_VERIFIKASI_MODEL"
        )
    elif spec == "jumlah benang":
        hasil = (
            "Sumber resmi seri VM menunjukkan 8 benang untuk VM1804 "
            "dan 12 benang untuk VM1806."
        )
        catatan = (
            f"Model {model}: pastikan konfigurasi model individual sesuai "
            "dengan halaman resmi dan nilai public."
        )
        rekomendasi = (
            "PERTAHANKAN_NILAI_ANGKA; TINJAU_FORMAT_SATUAN"
        )
    elif spec == "jumlah jarum":
        hasil = (
            "Sumber resmi seri VM menunjukkan 4 jarum untuk VM1804 "
            "dan 6 jarum untuk VM1806."
        )
        catatan = (
            f"Model {model}: pastikan konfigurasi model individual sesuai "
            "dengan halaman resmi dan nilai public."
        )
        rekomendasi = (
            "PERTAHANKAN_NILAI_ANGKA; TINJAU_FORMAT_SATUAN"
        )
    else:
        hasil = "Belum diklasifikasikan."
        catatan = "Perlu pemeriksaan manual."
        rekomendasi = "JANGAN_UBAH_SEBELUM_DITINJAU"

    if public_status == "Perlu Verifikasi":
        status_final = "MENUNGGU_VERIFIKASI_PER_MODEL"
    else:
        status_final = "SUMBER_SERI_DIPERIKSA_PERSETUJUAN_PERUBAHAN_BELUM_ADA"

    r.update({
        "hasil_pemeriksaan_sumber_resmi": hasil,
        "catatan_verifikasi_model": catatan,
        "rekomendasi_lanjutan": rekomendasi,
        "status_keputusan_final": status_final,
    })

fields = list(rows[0].keys()) + new_columns

with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("File dibuat:", out)
print("Jumlah baris:", len(rows))
print("\nKategori spesifikasi:")
for k, v in Counter(r["specification_public"] for r in rows).items():
    print(f"- {k}: {v}")

print("\nStatus keputusan:")
for k, v in Counter(r["status_keputusan_final"] for r in rows).items():
    print(f"- {k}: {v}")

print("\nFile sumber tidak ditimpa.")
print("Database lokal dan public tidak diubah.")
