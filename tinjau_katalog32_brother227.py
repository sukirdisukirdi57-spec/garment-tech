import csv
from pathlib import Path

master = Path("audit-tinjauan-120-kandidat-baru-brother227.csv")
output = Path("audit-tinjauan-katalog32-brother227.csv")

target = {
    ("12501", "S12441001", "WASHER"): (
        "BELUM DITETAPKAN",
        "Nama komponen terlalu umum untuk menentukan mekanisme. Cocokkan nomor part dan posisi washer pada diagram resmi serta verifikasi kecocokan submodel BAS-311HN-03S."
    ),
    ("12266", "S38713100", "FAN"): (
        "BELUM DITETAPKAN",
        "Nama mengarah ke kipas, tetapi lokasi pemasangan dan mekanisme terkait belum terkonfirmasi. Periksa diagram resmi dan kecocokan submodel BAS-311HN-03S."
    ),
    ("12314", "SB4181001", "Y-PLATE PACKING"): (
        "BELUM DITETAPKAN",
        "Nama mengarah ke packing pelat Y, tetapi posisi pemasangan dan kecocokan submodel BAS-311HN-03S harus dikonfirmasi melalui diagram resmi."
    ),
}

if not master.exists():
    raise SystemExit(f"CSV master tidak ditemukan: {master}")

with master.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = [
        r for r in reader
        if r.get("local_catalog", "").strip() == "32"
    ]

if not fieldnames:
    raise SystemExit("Header CSV master tidak terbaca.")

if len(rows) != len(target):
    raise SystemExit(
        f"Jumlah kandidat tidak sesuai: ditemukan {len(rows)}, "
        f"seharusnya {len(target)}. Laporan tidak dibuat."
    )

hasil = []
seen = set()

for row in rows:
    key = (
        row.get("local_part_id", "").strip(),
        row.get("part_number", "").strip(),
        row.get("local_part_name", "").strip(),
    )

    if key not in target or key in seen:
        raise SystemExit(
            f"Kandidat tidak cocok atau duplikat: {key}. "
            "Laporan tidak dibuat."
        )

    seen.add(key)
    mekanisme, catatan = target[key]

    row["keputusan_audit"] = "PERLU_VERIFIKASI_KATALOG"
    row["mekanisme_usulan"] = mekanisme
    row["rujukan_katalog"] = (
        "Perlu dicocokkan dengan diagram dan daftar komponen resmi "
        "Brother BAS-311HN/326H; kecocokan varian -03S belum terkonfirmasi."
    )
    row["catatan_auditor"] = catatan
    hasil.append(row)

if seen != set(target):
    raise SystemExit("Ada kandidat yang belum diproses. Laporan tidak dibuat.")

with output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(hasil)

print(f"Kandidat tervalidasi: {len(hasil)}")
for row in hasil:
    print(
        f'{row["part_number"]} | {row["local_part_name"]} | '
        f'{row["keputusan_audit"]} | {row["mekanisme_usulan"]}'
    )

print(f"Laporan: {output.resolve()}")
print("Database tidak diubah; hanya CSV laporan audit yang dibuat.")
