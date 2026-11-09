import csv
from pathlib import Path

src = Path("audit-kelengkapan/draf_ddl8000c_dari_csm.csv")
dst = Path("audit-kelengkapan/draf_ddl8000c_revisi_manual.csv")

revisi = {
"E01": ("Tegangan input AC terlalu tinggi", "Manual menyebut input melebihi 300 VAC (130 VAC). Hentikan penggunaan sampai suplai sesuai spesifikasi; pemeriksaan listrik dilakukan teknisi kompeten."),
"E02": ("Tegangan input AC terlalu rendah", "Manual menyebut input di bawah 150 VAC (80 VAC). Hentikan penggunaan sampai suplai sesuai spesifikasi; pemeriksaan listrik dilakukan teknisi kompeten."),
"E03": ("Gangguan komunikasi CPU", "Matikan daya. Teknisi memeriksa konektor dan kabel panel operasi; jika berlanjut, periksa control box."),
"E05": ("Sinyal pedal tidak normal", "Matikan daya. Periksa kabel dan konektor pedal. Jika belum pulih, teknisi memeriksa sensor pedal atau control box."),
"E07": ("Motor poros utama terkunci", "Matikan daya. Periksa kemungkinan hambatan mekanis tanpa memaksa pulley. Teknisi memeriksa konektor motor dan posisi berhenti jarum."),
"E09": ("Sinyal posisi atas encoder motor poros utama tidak normal", "Matikan daya. Teknisi memeriksa konektor encoder, koreksi posisi awal motor, dan encoder disk dari kontaminasi oli."),
"E10": ("Arus elektromagnet berlebih", "Matikan daya. Pemeriksaan solenoid dan rangkaian terkait dilakukan teknisi sesuai manual; jangan menguji rangkaian saat bertegangan."),
"E11": ("Sinyal posisi atas encoder motor poros utama tidak normal", "Manual mencantumkan deskripsi dan langkah yang sama dengan E09. Matikan daya; teknisi memeriksa konektor encoder, koreksi posisi awal, dan encoder disk."),
"E14": ("Sinyal encoder motor poros utama tidak normal", "Matikan daya. Teknisi memeriksa konektor encoder, pemasangan encoder disk, dan kontaminasi oli."),
"E15": ("Arus penggerak motor poros utama berlebih", "Matikan daya. Teknisi memeriksa kabel daya motor dari kemungkinan kontak buruk atau terjepit."),
"E17": ("Mesin terdeteksi dalam posisi miring", "Matikan daya dan pastikan kepala mesin pada posisi pengoperasian normal. Teknisi memeriksa sensor kemiringan."),
"E20": ("Motor poros utama gagal mulai", "Matikan daya. Teknisi memeriksa konektor daya dan encoder serta koreksi posisi awal motor."),
"E32": ("Berkas tidak kompatibel", "Gunakan berkas yang kompatibel dengan sistem mesin sesuai petunjuk resmi."),
"E46": ("Kegagalan reset watchdog timer", "Matikan mesin lalu hidupkan kembali sesuai prosedur. Jika berulang, hubungi teknisi."),
"E60": ("Resistansi regenerasi tidak normal", "Matikan daya. Teknisi memeriksa resistansi regenerasi dari kemungkinan longgar atau rusak."),
"E70": ("Kesalahan sistem", "Manual menyarankan memutus daya lalu menyalakannya kembali. Jika berulang, hubungi teknisi."),
"E71": ("Kesalahan CRC; data tersimpan rusak", "Manual menyebut U272 Restore factory defaults untuk inisialisasi data. Minta teknisi memeriksa dampak kehilangan pengaturan sebelum menjalankannya."),
"E72": ("Kegagalan fase pada suplai daya tiga fase", "Matikan mesin. Teknisi listrik memeriksa suplai tiga fase 220 V dan sambungan sesuai konfigurasi mesin."),
"E80": ("Komunikasi chip utama dan chip penggerak tidak normal", "Manual mengarahkan penggantian control box oleh teknisi dan menghubungi layanan purnajual."),
"E82": ("Arus motor pitch berlebih", "Matikan daya. Teknisi memeriksa hambatan mekanis motor pitch serta konektor daya dan encoder."),
"E84": ("Gangguan fase Z motor pitch", "Matikan daya. Teknisi memeriksa gerakan motor, konektor encoder, encoder disk, dan kontaminasi oli."),
"E85": ("Sinyal encoder motor pitch tidak normal", "Matikan daya. Teknisi memeriksa konektor encoder, encoder disk, dan kontaminasi oli."),
"E86": ("Gangguan fungsi motor pitch", "Matikan daya. Teknisi memeriksa konektor encoder, encoder disk, dan kontaminasi oli."),
"E87": ("Motor pitch terkunci", "Matikan daya. Teknisi memeriksa hambatan mekanis serta konektor daya dan encoder; jangan memaksa mekanisme."),
"E92": ("Arus motor pemotong benang/penekan benang berlebih", "Matikan daya. Teknisi memeriksa hambatan mekanis serta konektor daya dan encoder motor."),
"E94": ("Gangguan fase Z motor pemotong benang/penekan benang", "Matikan daya. Teknisi memeriksa gerakan motor, konektor encoder, dan kontaminasi oli."),
"E95": ("Sinyal encoder motor pemotong benang/penekan benang tidak normal", "Matikan daya. Teknisi memeriksa konektor encoder motor."),
"E96": ("Motor pemotong benang/penekan benang gagal mulai", "Matikan daya. Teknisi memeriksa konektor daya dan encoder motor."),
"E97": ("Motor pemotong benang/penekan benang terkunci", "Matikan daya. Teknisi memeriksa hambatan mekanis serta konektor daya dan encoder motor."),
"E100": ("Beban motor poros utama berlebih", "Matikan daya. Teknisi memeriksa beban mekanis motor dan koreksi posisi awal."),
"E110": ("Gangguan penerimaan data panel operasi saat daya menyala", "Matikan daya. Teknisi memeriksa konektor panel operasi; jika berlanjut, periksa panel dan control box."),
"PEDAL": ("Inisialisasi awal belum selesai", "Manual menyebut menekan bagian belakang pedal untuk menjalankan inisialisasi. Pastikan area mesin aman."),
"P_OFF": ("Indikasi daya mati", "Manual menyebut matikan sakelar, tunggu sampai layar padam, lalu nyalakan kembali jika hendak melanjutkan pengoperasian.")
}

if not src.exists():
    raise SystemExit(f"CSV sumber tidak ditemukan: {src}")

with src.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fields = reader.fieldnames

codes = [r.get("code", "").strip() for r in rows]
if len(rows) != 33 or len(set(codes)) != 33 or set(codes) != set(revisi):
    raise SystemExit("Validasi gagal: daftar kode CSV tidak sesuai 33 kode yang diharapkan.")

for r in rows:
    code = r["code"].strip()
    r["problem"], r["solution"] = revisi[code]
    r["source"] = "Manual JUKI DDL-8000C Series, bagian 5-4 List of error codes, halaman cetak 54–58; varian target perlu diverifikasi."
    r["review_status"] = "DRAF_REVISI_PERLU_VERIFIKASI_TEKNIS"
    safety = "Matikan daya sebelum pemeriksaan. Pekerjaan listrik dan pemeriksaan komponen internal hanya oleh teknisi kompeten. Verifikasi varian sebelum impor."
    old = r.get("safety_notes", "").strip()
    r["safety_notes"] = f"{old} {safety}".strip() if old else safety

with dst.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("CSV revisi dibuat:", dst)
print("Jumlah baris:", len(rows))
print("Kode unik:", len(set(r["code"] for r in rows)))
print("Database tidak diubah.")
