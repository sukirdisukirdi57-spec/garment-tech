import csv
from pathlib import Path

src = Path("tindak_lanjut_spesifikasi_nilai_berbeda_20261027.csv")
out = Path("keputusan_audit_spesifikasi_57_20261027.csv")

with src.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

assert len(rows) == 57, f"Jumlah harus 57, ditemukan {len(rows)}"

extra = [
    "kategori_perbedaan",
    "rekomendasi_audit",
    "status_tinjauan_audit",
    "alasan_audit",
]

result = []
for r in rows:
    spec = r["specification_public"].strip().lower()
    public_value = r["value_public"].strip()
    local_value = r["value_lokal"].strip()
    status = r["verification_status_public"].strip().lower()

    if spec == "jumlah benang":
        kategori = "PERBEDAAN_FORMAT_SATUAN"
        rekomendasi = "PERTAHANKAN_NILAI_ANGKA; PERTIMBANGKAN_PENYERAGAMAN_FORMAT"
        alasan = (
            f"Angka public '{public_value}' dan lokal '{local_value}' "
            "tampak sama; perbedaan berupa penulisan satuan."
        )
    elif spec == "jumlah jarum":
        kategori = "PERBEDAAN_FORMAT_SATUAN"
        rekomendasi = "PERTAHANKAN_NILAI_ANGKA; PERTIMBANGKAN_PENYERAGAMAN_FORMAT"
        alasan = (
            f"Angka public '{public_value}' dan lokal '{local_value}' "
            "tampak sama; perbedaan berupa penulisan satuan."
        )
    elif spec == "jenis mesin":
        kategori = "PERBEDAAN_ISTILAH_TEKNIS"
        rekomendasi = "TINJAU_PENYELARASAN_DENGAN_NILAI_PUBLIC"
        alasan = (
            "Nilai public menyebut cylinder bed dan double-chainstitch, "
            "sedangkan nilai lokal memakai deskripsi yang lebih umum. "
            "Periksa sumber resmi sebelum menyelaraskan."
        )
    else:
        kategori = "PERLU_KLASIFIKASI_MANUAL"
        rekomendasi = "JANGAN_UBAH_SEBELUM_DITINJAU"
        alasan = "Nama spesifikasi tidak termasuk tiga kelompok yang dikenali otomatis."

    if "perlu verifikasi" in status:
        status_tinjauan = "MENUNGGU_VERIFIKASI_SUMBER"
        alasan += " Status verifikasi public masih Perlu Verifikasi."
    else:
        status_tinjauan = "DRAF_PERLU_PERSETUJUAN"
        alasan += " Status public tercatat Terverifikasi; keputusan perubahan lokal tetap menunggu persetujuan."

    r.update({
        "kategori_perbedaan": kategori,
        "rekomendasi_audit": rekomendasi,
        "status_tinjauan_audit": status_tinjauan,
        "alasan_audit": alasan,
    })
    result.append(r)

fields = list(rows[0].keys()) + extra

with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(result)

print("FILE KEPUTUSAN AUDIT DIBUAT:", out)
print("Jumlah baris:", len(result))
print("Ringkasan kategori:")
from collections import Counter
for k, v in Counter(r["kategori_perbedaan"] for r in result).items():
    print(f"- {k}: {v}")

print("\nRingkasan status tinjauan:")
for k, v in Counter(r["status_tinjauan_audit"] for r in result).items():
    print(f"- {k}: {v}")

print("\nDatabase lokal/public tidak dibuka atau diubah oleh skrip ini.")
print("Periksa file keputusan sebelum menyetujui tindakan berikutnya.")
