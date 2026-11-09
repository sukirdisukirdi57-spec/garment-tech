#!/usr/bin/env python3
import csv
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
CSV_FILE = BASE / "draf_ddl8000c_revisi_manual.csv"

FIELDS = {
    "1": ("problem", "Masalah"),
    "2": ("symptoms", "Gejala"),
    "3": ("possible_cause", "Kemungkinan penyebab"),
    "4": ("solution", "Solusi"),
    "5": ("safety_notes", "Catatan keselamatan"),
    "6": ("source", "Sumber manual"),
}

def main():
    if not CSV_FILE.exists():
        print("CSV tidak ditemukan:", CSV_FILE)
        return

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = list(reader)

    if not columns or "code" not in columns:
        print("Struktur CSV tidak valid.")
        return

    codes = {}
    for i, row in enumerate(rows):
        code = row.get("code", "").strip().upper()
        if code:
            codes.setdefault(code, []).append(i)

    print("\n=== EDIT TROUBLESHOOTING JUKI ===")
    print("File:", CSV_FILE)
    print("Jumlah baris:", len(rows))
    print("Kode tersedia:", ", ".join(sorted(codes)))
    print("\nKetik kode yang ingin diedit, misalnya E01.")
    print("Ketik Q untuk keluar.")

    code = input("\nKode: ").strip().upper()
    if code == "Q":
        return
    if code not in codes:
        print("Kode tidak ditemukan. Mode ini hanya mengedit kode yang sudah ada.")
        return
    if len(codes[code]) != 1:
        print("Kode duplikat ditemukan. Perbaiki duplikasi secara terpisah.")
        return

    row = rows[codes[code][0]]
    print("\nKode:", code)
    print("Model:", row.get("target_model", "(tidak tercatat)"))
    print("Status:", row.get("review_status", "(kosong)"))
    print("\nTekan Enter untuk mempertahankan isi lama.")
    print("Jangan memasukkan klaim yang belum didukung sumber.")

    changes = {}
    for number, (field, label) in FIELDS.items():
        old = row.get(field, "")
        print(f"\n{number}. {label}")
        print("Lama:", old or "(kosong)")
        new = input("Baru: ").strip()
        if new and new != old:
            changes[field] = new

    if not changes:
        print("\nTidak ada perubahan.")
        return

    print("\n=== PRATINJAU PERUBAHAN ===")
    for field, value in changes.items():
        print(f"{field}: {value}")

    print("\nStatus verifikasi akan tetap:", row.get("review_status", ""))
    confirm = input("Simpan perubahan ke CSV draf? Ketik SIMPAN: ")
    if confirm != "SIMPAN":
        print("Dibatalkan; file tidak diubah.")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = CSV_FILE.with_name(
        CSV_FILE.stem + ".bak_" + stamp + CSV_FILE.suffix
    )
    shutil.copy2(CSV_FILE, backup)

    row.update(changes)
    fd, temp_name = tempfile.mkstemp(
        prefix=".troubleshooting_", suffix=".tmp", dir=str(BASE)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=columns, extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())

        # Validasi ulang file sementara sebelum mengganti CSV.
        with open(temp_name, encoding="utf-8-sig", newline="") as f:
            check = list(csv.DictReader(f))
        if len(check) != len(rows):
            raise RuntimeError("Jumlah baris berubah; pembatalan.")

        os.replace(temp_name, CSV_FILE)
    except Exception:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
        print("Gagal menyimpan. Backup asli:", backup)
        raise

    print("\nBerhasil menyimpan draf.")
    print("Backup:", backup)
    print("Database tidak diubah.")
    print("Status verifikasi tidak dinaikkan otomatis.")

if __name__ == "__main__":
    main()
