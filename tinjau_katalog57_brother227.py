import csv
from pathlib import Path

master = Path("audit-tinjauan-120-kandidat-baru-brother227.csv")
output = Path("audit-tinjauan-katalog57-brother227.csv")
expected = ("12559", "SA4354001", "SHOULDER SCREW, 6-1.8")

if not master.exists():
    raise SystemExit(f"CSV master tidak ditemukan: {master}")

with master.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = [
        r for r in reader
        if r.get("local_catalog", "").strip() == "57"
    ]

if len(rows) != 1:
    raise SystemExit(
        f"Ditemukan {len(rows)} kandidat; seharusnya 1. "
        "Laporan tidak dibuat."
    )

row = rows[0]
actual = (
    row.get("local_part_id", "").strip(),
    row.get("part_number", "").strip(),
    row.get("local_part_name", "").strip(),
)

if actual != expected:
    raise SystemExit(
        f"Identitas kandidat tidak cocok: {actual}. "
        "Laporan tidak dibuat."
    )

row["keputusan_audit"] = "PERLU_VERIFIKASI_KATALOG"
row["mekanisme_usulan"] = "BELUM DITETAPKAN"
row["rujukan_katalog"] = (
    "Cocokkan dengan diagram dan daftar komponen resmi Brother "
    "BAS-311HN/326H; kecocokan submodel -03S belum terkonfirmasi."
)
row["catatan_auditor"] = (
    "Nama menunjukkan shoulder screw dengan spesifikasi 6-1.8, "
    "tetapi fungsi dan lokasi pemasangan belum diketahui. Verifikasi "
    "diagram resmi serta kecocokan untuk BAS-311HN-03S."
)

with output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(row)

print("Kandidat tervalidasi: 1")
print(
    f'{row["part_number"]} | {row["local_part_name"]} | '
    f'{row["keputusan_audit"]} | {row["mekanisme_usulan"]}'
)
print(f"Laporan: {output.resolve()}")
print("Database dan CSV master tidak diubah.")
