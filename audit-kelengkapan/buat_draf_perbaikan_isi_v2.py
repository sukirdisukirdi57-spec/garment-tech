import csv
from pathlib import Path

folder = Path("audit-kelengkapan")
sumber = folder / "draf_perbaikan_isi_ddl8700.csv"
tujuan = folder / "draf_perbaikan_isi_ddl8700_v2.csv"

if not sumber.exists():
    raise SystemExit(f"File sumber tidak ditemukan: {sumber}")

with sumber.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

if not rows or not fieldnames:
    raise SystemExit("CSV sumber kosong atau header tidak ditemukan.")

revisi = {
    1: {
        "solution_usulan":
            "Hentikan mesin dan putuskan sumber listrik. Jangan membongkar "
            "atau menyetel mekanisme penggerak tanpa prosedur servis yang sesuai. "
            "Minta teknisi kompeten memeriksa penyebab mesin tidak dapat menjahit "
            "serta kondisi mekanisme penggerak dan jarum. Uji kembali hanya "
            "setelah pemeriksaan dinyatakan aman."
    },
    2: {
        "solution_usulan":
            "Putuskan listrik sebelum memeriksa jarum dan jalur benang. Periksa "
            "kondisi serta pemasangan jarum dan ikuti jalur pemasangan benang "
            "sesuai manual. Periksa area yang mungkin menggesek benang, termasuk "
            "permukaan kasar atau tajam yang terlihat. Jika tegangan perlu disetel, "
            "ubah sedikit demi sedikit dan uji pada bahan yang sama dengan "
            "pelindung terpasang."
    },
    3: {
        "solution_usulan":
            "Putuskan listrik sebelum membuka area bobbin atau hook. Periksa "
            "kondisi bobbin dan bobbin case, arah serta jalur benang sesuai manual, "
            "dan tanda kerusakan yang terlihat. Setel tegangan hanya secara "
            "bertahap sesuai prosedur. Jika ditemukan kerusakan pada hook atau "
            "bobbin case, atau masalah terus berulang, minta teknisi memeriksanya."
    },
    4: {
        "solution_usulan":
            "Putuskan listrik, lalu periksa kondisi, tipe, dan pemasangan jarum "
            "sesuai manual. Jika jahitan tetap loncat, minta teknisi kompeten "
            "memeriksa hubungan serta jarak jarum–hook menggunakan prosedur dan "
            "spesifikasi model yang tepat. Jangan mengubah penyetelan mekanis "
            "berdasarkan perkiraan."
    },
    247: {
        "solution_usulan":
            "Periksa pemasangan benang atas dan bobbin sesuai manual. Sebelum "
            "menyentuh jarum, hook, atau komponen mekanis, matikan mesin dan "
            "putuskan sumber listrik. Ubah tegangan sedikit demi sedikit, satu "
            "perubahan pada satu waktu, lalu uji pada bahan yang sama. Jika hasil "
            "tidak membaik, periksa kembali pemasangan benang dan minta bantuan "
            "teknisi sebelum mengubah setelan mekanis lain.",
        "safety_notes_usulan":
            "Putuskan sumber listrik sebelum memeriksa jarum, hook, atau komponen "
            "mekanis. Saat uji jahit, pasang pelindung sesuai konfigurasi mesin "
            "dan jauhkan tangan dari bagian bergerak."
    },
    248: {
        "solution_usulan":
            "Hentikan mesin dan putuskan listrik. Periksa jarum dan pastikan tipe, "
            "ukuran, serta pemasangannya sesuai manual. Periksa tanda benturan "
            "pada jarum dan komponen di sekitarnya, termasuk presser foot dan "
            "needle plate. Jika benturan berulang atau penyebabnya tidak jelas, "
            "jangan menjalankan mesin kembali sebelum diperiksa teknisi. Jangan "
            "menyetel timing atau cam tanpa prosedur servis yang tepat."
    },
    249: {
        "solution_usulan":
            "Putuskan listrik sebelum membersihkan atau memeriksa area feed dog. "
            "Periksa kebersihan dan kondisi yang terlihat, lalu pastikan panjang "
            "jahitan dan tekanan sepatu sesuai manual serta bahan. Uji pada bahan "
            "yang sama dengan pelindung terpasang. Jika masalah berlanjut, minta "
            "teknisi memeriksa timing dan mekanisme pengumpan sesuai prosedur "
            "model yang tepat."
    },
    250: {
        "solution_usulan":
            "Hentikan mesin jika suara atau getaran berat, muncul mendadak, atau "
            "penyebabnya tidak diketahui. Putuskan listrik sebelum pemeriksaan. "
            "Periksa pelumasan hanya sesuai prosedur manual yang berlaku. Jika "
            "penyebab belum jelas atau dicurigai ada masalah mekanis, jangan "
            "gunakan kembali mesin sebelum teknisi kompeten memeriksanya."
    }
}

expected_ids = {1, 2, 3, 4, 247, 248, 249, 250}
found_ids = set()

for row in rows:
    try:
        record_id = int(row["id"])
    except (KeyError, ValueError, TypeError):
        continue

    if record_id not in expected_ids:
        continue

    found_ids.add(record_id)
    for field, value in revisi[record_id].items():
        if field not in fieldnames:
            raise SystemExit(f"Kolom tidak ditemukan di CSV: {field}")
        row[field] = value

    # Menegaskan bahwa berkas ini hanya draf, belum diterapkan.
    if "status" in row:
        row["status"] = "DRAF V2 UNTUK DITINJAU - BELUM DITERAPKAN"

missing = expected_ids - found_ids
if missing:
    raise SystemExit(f"ID berikut tidak ditemukan di draf sumber: {sorted(missing)}")

with tujuan.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Draf revisi kedua dibuat: {tujuan}")
print(f"Jumlah ID diperiksa: {len(found_ids)}")
print("Database tidak dibuka atau diubah oleh skrip ini.")
print("Perubahan masih berupa draf dan belum diterapkan.")
