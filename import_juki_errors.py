
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
SOURCE = "tmp/ddl8000csm-audit/instruction.txt"

# Data awal untuk diperiksa, belum dimasukkan ke database.
ERRORS = [
    ("E01", "Tegangan masuk terlalu tinggi",
     "Tegangan suplai AC melebihi batas manual.",
     "Matikan mesin. Jangan gunakan sampai tegangan sesuai manual."),
    ("E02", "Tegangan masuk terlalu rendah",
     "Tegangan suplai AC di bawah batas manual.",
     "Matikan mesin. Jangan gunakan sampai tegangan sesuai manual."),
    ("E03", "Gangguan komunikasi CPU",
     "Koneksi panel operasi atau kabel mungkin bermasalah.",
     "Matikan daya. Periksa konektor dan kabel dari luar. Hubungi teknisi jika berlanjut."),
    ("E05", "Sinyal pedal tidak normal",
     "Konektor, kabel pedal, atau sensor mungkin bermasalah.",
     "Matikan daya. Periksa konektor dan kabel. Hubungi teknisi jika berlanjut."),
    ("E07", "Motor poros utama terkunci",
     "Mekanisme mungkin macet atau sambungan motor bermasalah.",
     "Matikan daya. Jangan paksa pulley. Minta teknisi memeriksa jika macet.")
]

def main():
    if not DB.is_file():
        print("GAGAL: database tidak ditemukan:", DB)
        return

    if not Path(SOURCE).is_file():
        print("GAGAL: teks manual tidak ditemukan:", SOURCE)
        return

    # Baca database saja; belum ada perubahan data.
    con = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
    try:
        columns = {
            row[1] for row in con.execute("PRAGMA table_info(troubleshooting)")
        }
        if not {"machine_id", "problem", "symptoms",
                "possible_cause", "solution", "safety_notes", "source"} <= columns:
            print("GAGAL: struktur tabel tidak sesuai.")
            return

        for machine_id in (16, 225):
            machine = con.execute(
                "SELECT id, model FROM machines WHERE id=?",
                (machine_id,)
            ).fetchone()
            if machine:
                print(f"Mesin: ID {machine[0]} - {machine[1]}")
            else:
                print(f"PERINGATAN: mesin ID {machine_id} tidak ditemukan.")

        print("\nMODE: PEMERIKSAAN SAJA")
        print("Tidak ada data yang ditambahkan atau diubah.")
        print("\nDaftar kode yang akan diperiksa:")
        for code, title, cause, solution in ERRORS:
            print(f"- {code}: {title}")
            print(f"  Penyebab: {cause}")
            print(f"  Tindakan: {solution}")

        print("\nCatatan: daftar ini baru 5 contoh, bukan seluruh kode manual.")
        print("Belum ada impor. Kecocokan model harus diperiksa dahulu.")
    finally:
        con.close()

if __name__ == "__main__":
    main()
