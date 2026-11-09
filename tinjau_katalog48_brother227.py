import csv
from pathlib import Path

master = Path("audit-tinjauan-120-kandidat-baru-brother227.csv")
output = Path("audit-tinjauan-katalog48-brother227.csv")
expected = ("12281", "SB1040001", "SCREW")

if not master.exists():
    raise SystemExit(f"CSV master tidak ditemukan: {master}")

with master.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = [
        r for r in reader
        if r.get("local_catalog", "").strip() == "48"
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
    "Nama hanya menyebut sekrup tanpa ukuran atau posisi pemasangan. "
    "Verifikasi spesifikasi, lokasi, dan fungsi pada diagram resmi "
    "sebelum menetapkan mekanisme; kecocokan BAS-311HN-03S belum pasti."
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
