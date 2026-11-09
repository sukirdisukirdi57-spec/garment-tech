import csv
from pathlib import Path

master = Path("audit-tinjauan-120-kandidat-baru-brother227.csv")
output = Path("audit-tinjauan-katalog44-brother227.csv")

expected = {
    "12359": ("", "ANTI-SPIN SPRING"),
    "12277": ("SB2097001", "PULLEY SHAFT"),
}

if not master.exists():
    raise SystemExit(f"CSV master tidak ditemukan: {master}")

with master.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = [
        r for r in reader
        if r.get("local_catalog", "").strip() == "44"
    ]

if len(rows) != len(expected):
    raise SystemExit(
        f"Jumlah kandidat {len(rows)}; seharusnya {len(expected)}. "
        "Laporan tidak dibuat."
    )

seen = set()

for row in rows:
    part_id = row.get("local_part_id", "").strip()
    actual = (
        row.get("part_number", "").strip(),
        row.get("local_part_name", "").strip(),
    )

    if part_id not in expected or actual != expected[part_id]:
        raise SystemExit(
            f"Identitas tidak cocok: ID={part_id}, data={actual}. "
            "Laporan tidak dibuat."
        )

    if part_id in seen:
        raise SystemExit(f"ID duplikat: {part_id}")

    seen.add(part_id)
    row["keputusan_audit"] = "PERLU_VERIFIKASI_KATALOG"
    row["mekanisme_usulan"] = "BELUM DITETAPKAN"
    row["rujukan_katalog"] = (
        "Cocokkan dengan diagram dan daftar komponen resmi Brother "
        "BAS-311HN/326H; kecocokan submodel -03S belum terkonfirmasi."
    )

    if part_id == "12359":
        row["catatan_auditor"] = (
            "Nomor komponen kosong pada data lokal. Verifikasi nomor "
            "komponen dan posisi anti-spin spring melalui diagram resmi "
            "sebelum menetapkan mekanisme."
        )
    else:
        row["catatan_auditor"] = (
            "Nama menunjukkan pulley shaft, tetapi mekanisme dan posisi "
            "pemasangan belum terkonfirmasi. Periksa diagram resmi dan "
            "verifikasi kecocokan submodel BAS-311HN-03S."
        )

if seen != set(expected):
    raise SystemExit("Ada kandidat yang belum diproses. Laporan tidak dibuat.")

with output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Kandidat tervalidasi: {len(rows)}")
for row in rows:
    print(
        f'{row["local_part_id"]} | {row["part_number"] or "(kosong)"} | '
        f'{row["local_part_name"]} | {row["keputusan_audit"]}'
    )
print(f"Laporan: {output.resolve()}")
print("Database dan CSV master tidak diubah.")
