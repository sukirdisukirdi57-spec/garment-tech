import sqlite3
import csv
from pathlib import Path

DB = Path("database/garment.db")
OUT = Path("tools/he800c_audit/staging/he800c_spec_candidates.csv")

candidates = [
    {
        "specification": "Ukuran lubang kancing",
        "value": "Panjang lubang 4–32 mm; panjang total maksimum 40 mm",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Bedakan panjang lubang dari panjang total lubang kancing."
    },
    {
        "specification": "Panjang tusuk zigzag maksimum",
        "value": "36 mm",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Nilai batas yang tercantum pada diagram ukuran lubang kancing."
    },
    {
        "specification": "Metode penggerak cutter",
        "value": "Double position solenoid",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Metode penggerak pemotong material."
    },
    {
        "specification": "Jumlah jahitan maksimum per program",
        "value": "999 jahitan",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Manual juga menyebut 3.000 jahitan untuk program siklus keseluruhan."
    },
    {
        "specification": "Jumlah jahitan program siklus",
        "value": "3.000 jahitan",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Batas untuk keseluruhan program siklus; bukan batas per program biasa."
    },
    {
        "specification": "Media penyimpanan data",
        "value": "SD memory card",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Manual tidak menjamin semua media SD dapat beroperasi."
    },
    {
        "specification": "Jarum untuk spesifikasi -2",
        "value": "Schmetz 134 Nm90",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2; parts book ref. 37+",
        "description": "Varian -2; kode jarum parts book SA9253090."
    },
    {
        "specification": "Jarum untuk spesifikasi -3",
        "value": "Schmetz 134 Nm75",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2; parts book ref. 37+",
        "description": "Varian -3; kode jarum parts book SA9253075."
    },
    {
        "specification": "Catu daya",
        "value": "1 fase 100/220 V; 3 fase 220/380/400 V",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Trans box diperlukan untuk 1 fase 100 V dan 3 fase 380/400 V. Konfirmasi konfigurasi unit sebelum penggunaan."
    },
    {
        "specification": "Perlengkapan penahan benang bawah",
        "value": "Standar",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Lower thread holding device."
    },
    {
        "specification": "Bobbin presser",
        "value": "Standar",
        "notes": "Manual resmi Brother HE-800C, bagian 2-1, halaman cetak 2",
        "description": "Tercantum sebagai perlengkapan standar."
    },
]

with sqlite3.connect(DB) as con:
    con.row_factory = sqlite3.Row
    machine = con.execute(
        "SELECT id, model FROM machines WHERE id = 102"
    ).fetchone()

    if not machine or machine["model"] != "HE-800C":
        raise SystemExit("Dibatalkan: machine ID 102 tidak cocok dengan HE-800C.")

    existing = con.execute(
        """SELECT specification, value, notes, description
           FROM specifications WHERE machine_id = ?""",
        (102,)
    ).fetchall()

existing_names = {r["specification"].strip().casefold() for r in existing}

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "machine_id", "model", "status",
            "specification", "value", "notes", "description"
        ]
    )
    writer.writeheader()
    for item in candidates:
        name = item["specification"]
        status = (
            "PERIKSA_KEMUNGKINAN_DUPLIKAT"
            if name.strip().casefold() in existing_names
            else "KANDIDAT_BARU"
        )
        writer.writerow({
            "machine_id": 102,
            "model": "HE-800C",
            "status": status,
            **item
        })

print("Audit staging selesai — database tidak diubah.")
print(f"Spesifikasi yang sudah ada: {len(existing)}")
print(f"Kandidat yang diperiksa: {len(candidates)}")
print(f"File laporan: {OUT}")
print("\nStatus kandidat:")
for item in candidates:
    status = (
        "PERIKSA_KEMUNGKINAN_DUPLIKAT"
        if item["specification"].strip().casefold() in existing_names
        else "KANDIDAT_BARU"
    )
    print(f"- {status}: {item['specification']}")
