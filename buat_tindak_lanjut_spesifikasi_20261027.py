import csv
from pathlib import Path
from collections import Counter

source = Path("rekonsiliasi_spesifikasi_public_vs_lokal_20261027.csv")
if not source.exists():
    raise SystemExit(f"Laporan sumber tidak ditemukan: {source}")

groups = {
    "BELUM_ADA_SPESIFIKASI_LOKAL": (
        "tindak_lanjut_spesifikasi_belum_ada_lokal_20261027.csv",
        "PERIKSA_KANDIDAT_BARU",
        "Periksa kemungkinan duplikasi berdasarkan mesin, nama, dan nilai. "
        "Tambahkan hanya setelah peninjauan dan persetujuan."
    ),
    "NAMA_SAMA_NILAI_BERBEDA": (
        "tindak_lanjut_spesifikasi_nilai_berbeda_20261027.csv",
        "BANDINGKAN_NILAI",
        "Public menjadi acuan. Tinjau perbedaan nilai dan konteks model "
        "sebelum menyelaraskan data lokal."
    ),
    "PERLU_AUDIT_IDENTITAS_MESIN": (
        "tindak_lanjut_identitas_mesin_20261027.csv",
        "AUDIT_IDENTITAS",
        "Pastikan identitas model dan pemetaan machine ID. "
        "Jangan pindahkan atau tambahkan spesifikasi sebelum terverifikasi."
    ),
}

with source.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames or [])
    rows = list(reader)

if not fieldnames or "status_rekonsiliasi" not in fieldnames:
    raise SystemExit("Kolom status_rekonsiliasi tidak ditemukan.")

counts = Counter(r.get("status_rekonsiliasi", "") for r in rows)
expected = {
    "BELUM_ADA_SPESIFIKASI_LOKAL": 551,
    "NAMA_SAMA_NILAI_BERBEDA": 57,
    "PERLU_AUDIT_IDENTITAS_MESIN": 21,
}

for status, number in expected.items():
    if counts.get(status, 0) != number:
        raise SystemExit(
            f"Jumlah {status} tidak sesuai: "
            f"{counts.get(status, 0)}; diharapkan {number}. "
            "Tidak ada berkas tindak lanjut yang dibuat."
        )

extra = ["rekomendasi_tindak_lanjut", "status_tinjauan"]
out_fields = fieldnames + extra

for status, (filename, action, note) in groups.items():
    selected = [r.copy() for r in rows
                if r.get("status_rekonsiliasi") == status]

    for r in selected:
        r["rekomendasi_tindak_lanjut"] = action + ": " + note
        r["status_tinjauan"] = "BELUM_DITINJAU"

    target = Path(filename)
    with target.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(selected)

    print(f"{target}: {len(selected)} baris")

print("\nRingkasan laporan sumber:")
for status, n in counts.items():
    print(f"{status}: {n}")

print("\nSelesai. Hanya berkas audit CSV yang dibuat.")
print("Database lokal dan web public tidak diubah.")
