import csv
import sqlite3
from pathlib import Path

db_path = Path("database/garment.db")
out_path = Path("stage8_audit_report.csv")

audit_notes = {
    21: (
        "Gejala umum",
        "Siklus tidak berjalan memiliki beberapa kemungkinan penyebab; "
        "belum cukup untuk menentukan satu kode error.",
        "Periksa prosedur pedal, pola, catu daya, dan control box "
        "sesuai manual; jangan menetapkan kode otomatis."
    ),
    22: (
        "Gejala umum",
        "Benang putus dapat disebabkan tegangan, jalur benang, jarum, "
        "hook, atau timing; E052 berkaitan dengan deteksi putus benang "
        "saat mesin berjalan, bukan seluruh penyebab mekanis.",
        "Cocokkan dengan bagian Troubles And Corrective Measures "
        "pada manual."
    ),
    23: (
        "Perlu verifikasi manual",
        "Hasil potong buruk tidak otomatis berarti sensor pisau "
        "atau kegagalan pisau kembali ke posisi semula.",
        "Periksa ukuran dan kondisi pisau serta setelan yang relevan "
        "di manual."
    ),
    24: (
        "Gejala umum",
        "Panjang lubang kancing yang salah dapat terkait parameter "
        "pola atau mekanisme feeding; belum menunjuk satu kode error.",
        "Verifikasi panjang yang diprogram, pola, dan spesifikasi "
        "model yang digunakan."
    ),
    25: (
        "Gejala umum",
        "Pola jahitan tidak sesuai dapat berasal dari pemilihan pola "
        "atau data/setelan; tidak otomatis berarti data rusak.",
        "Verifikasi nomor pola dan parameter pada panel."
    ),
    26: (
        "Perlu verifikasi manual",
        "Jahitan loncat atau tidak rapi dapat disebabkan jarum, "
        "tegangan, hook, timing, atau penempatan material.",
        "Gunakan panduan troubleshooting mekanis; serahkan penyetelan "
        "timing kepada teknisi yang kompeten."
    ),
    27: (
        "Perlu verifikasi manual",
        "Gangguan pengangkatan umum berbeda dari E023 (motor pengangkat "
        "kehilangan langkah) dan E083 (posisi sepatu penekan terlalu tinggi "
        "saat mulai menjahit).",
        "Pastikan gejala dan kondisi pemicu cocok sebelum mengaitkan "
        "dengan kode tertentu."
    ),
    28: (
        "Perlu verifikasi manual",
        "Putaran tidak stabil atau mesin berhenti belum membuktikan "
        "adanya satu kode motor tertentu; E303 dan E912 memiliki "
        "kondisi diagnostik spesifik.",
        "Catat pesan error yang benar-benar tampil dan cocokkan "
        "dengan daftar kode resmi."
    ),
}

db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
db.row_factory = sqlite3.Row

rows = db.execute("""
    SELECT id, code, problem, symptoms, possible_cause,
           solution, safety_notes
    FROM troubleshooting
    WHERE machine_id = 6
      AND id BETWEEN 21 AND 28
    ORDER BY id
""").fetchall()

if len(rows) != 8:
    raise SystemExit(
        f"Audit dihentikan: ditemukan {len(rows)} entri, bukan 8. "
        "Tidak ada laporan yang ditulis."
    )

fields = [
    "id", "code", "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "kategori_audit",
    "alasan", "rekomendasi", "status"
]

with out_path.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for row in rows:
        category, reason, recommendation = audit_notes[row["id"]]
        writer.writerow({
            **dict(row),
            "kategori_audit": category,
            "alasan": reason,
            "rekomendasi": recommendation,
            "status": "Belum dipetakan; menunggu verifikasi manual"
        })

db.close()

print("Laporan dibuat:", out_path)
print("Jumlah baris audit:", len(rows))
print("Ukuran file:", out_path.stat().st_size, "bytes")
print("Database utama hanya dibaca; tidak ada perubahan data.")
