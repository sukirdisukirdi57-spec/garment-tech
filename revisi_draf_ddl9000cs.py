import csv
import re
from pathlib import Path

source_file = Path("audit-kelengkapan/sumber_error_ddl9000cs.txt")
output_file = Path("audit-kelengkapan/draf_ddl9000cs_manual_revisi.csv")

if not source_file.exists():
    raise SystemExit("ERROR: arsip sumber manual tidak ditemukan.")

source_text = source_file.read_text(errors="replace")

if "4-6. List of errors" not in source_text:
    raise SystemExit("ERROR: judul bagian daftar error tidak ditemukan.")

# Kode yang terlihat pada tabel manual halaman cetak 52–54.
codes = [
    "E000", "E007", "E009", "E011", "E012", "E013", "E014",
    "E015", "E016", "E032", "E071", "E072", "E081", "E204",
    "E220", "E221", "E302", "E303", "E704", "E730", "E731",
    "E733", "E811", "E813", "E815", "E903", "E904", "E910",
    "E912", "E915", "E922", "E924", "E946", "E955", "E961",
    "E962", "E971", "E972", "E973", "E974", "E975", "E976",
    "E985"
]

# Deskripsi di bawah ini ditranskripsikan dari teks manual yang
# abang kirim. Penyebab dan pemeriksaan diringkas tanpa menambah
# prosedur perbaikan yang tidak tertulis di manual.
data = {
"E000": ("Inisialisasi data (bukan error)",
         "Kepala mesin diganti atau operasi inisialisasi dijalankan.",
         "Manual menyatakan ini bukan error; tidak ada tindakan perbaikan khusus yang dicantumkan."),
"E007": ("Motor overload",
         "Manual menyebut penggantian kepala mesin.",
         "Tidak ada item pemeriksaan yang tercantum pada baris ini."),
"E009": ("Solenoid energized terlalu lama",
         "Kepala mesin terkunci; bahan terlalu berat; motor tidak berputar; atau motor/driver bermasalah.",
         "Manual: periksa pulley terlilit benang, konektor output motor longgar, dan apakah motor dapat diputar dengan lancar menggunakan tangan. Matikan daya dan lakukan pemeriksaan mekanis hanya jika aman."),
"E011": ("Media tidak terpasang",
         "Tidak ada media yang dimasukkan.",
         "Manual: matikan daya dan periksa media."),
"E012": ("Kesalahan membaca data",
         "Data pada media tidak dapat dibaca.",
         "Manual: matikan daya dan periksa media."),
"E013": ("Kesalahan menulis data",
         "Data tidak dapat ditulis ke media.",
         "Manual: matikan daya dan periksa media."),
"E014": ("Media terlindungi dari penulisan",
         "Media berada dalam keadaan write-protect.",
         "Manual: matikan daya dan periksa media."),
"E015": ("Kesalahan format media",
         "Media tidak dapat diformat.",
         "Manual: matikan daya dan periksa media."),
"E016": ("Kapasitas media tidak mencukupi",
         "Kapasitas media tidak cukup.",
         "Manual: matikan daya dan periksa media."),
"E032": ("Kesalahan kompatibilitas file",
         "File tidak kompatibel.",
         "Manual: matikan daya dan periksa media."),
"E071": ("Konektor motor terlepas",
         "Konektor motor terlepas, rangkaian deteksi arus rusak, atau umpan balik arus tidak tersedia.",
         "Manual: periksa apakah konektor output motor longgar atau terlepas."),
"E072": ("Motor overload saat thread trimmer beroperasi",
         "Kondisi overload terjadi ketika pemotong benang bekerja.",
         "Manual tidak mencantumkan item pemeriksaan pada baris ini."),
"E081": ("Motor penggerak feed terkunci",
         "Motor penggerak feed terkunci.",
         "Manual: periksa apakah motor penggerak feed bekerja dengan lancar."),
"E204": ("USB masih terpasang",
         "Mesin dinyalakan tanpa melepas USB thumb drive.",
         "Manual: lepaskan USB thumb drive."),
"E220": ("Peringatan kekurangan grease",
         "Jumlah jahitan yang telah ditentukan tercapai.",
         "Manual: tambahkan grease pada titik yang ditentukan dan reset error sesuai petunjuk resmi."),
"E221": ("Error kekurangan grease",
         "Mesin tidak dapat melanjutkan jahitan karena jumlah jahitan yang ditentukan tercapai.",
         "Manual: tambahkan grease pada titik yang ditentukan dan reset error sesuai petunjuk resmi."),
"E302": ("Error deteksi kemiringan kepala mesin",
         "Sakelar deteksi tilt aktif saat daya mesin masih menyala.",
         "Manual: periksa apakah kepala mesin dimiringkan sebelum daya dimatikan; periksa kabel sakelar tilt yang terjepit dan kabel pada INT PCB. Periksa rangkaian internal hanya oleh teknisi kompeten."),
"E303": ("Error sensor meniskus",
         "Sinyal sensor meniskus tidak dapat dideteksi.",
         "Manual: periksa kesesuaian pengaturan model kepala mesin dan konektor encoder motor yang mungkin putus."),
"E704": ("Kegagalan data / ketidakcocokan versi sistem",
         "Versi sistem tidak cocok dengan pengaturan kepala mesin.",
         "Manual menyebut penulisan ulang versi sistem yang sesuai; lakukan hanya dengan prosedur servis resmi."),
"E730": ("Gangguan encoder",
         "Sinyal motor tidak masuk dengan benar.",
         "Manual: periksa konektor sinyal motor CN39, kabel sinyal yang mungkin terjepit/putus, dan arah pemasangan konektor encoder."),
"E731": ("Gangguan sensor lubang motor",
         "Sinyal motor tidak masuk dengan benar.",
         "Manual mencantumkan pemeriksaan konektor sinyal motor CN39, kabel sinyal, dan arah pemasangan konektor encoder."),
"E733": ("Motor berputar terbalik",
         "Pada kecepatan 500 sti/min atau lebih, motor berputar berlawanan dengan arah yang ditentukan.",
         "Manual: periksa sambungan kabel encoder motor poros utama dan kabel daya motor poros utama."),
"E811": ("Tegangan berlebih",
         "Tegangan suplai melampaui batas yang dijamin atau konfigurasi tegangan tidak cocok.",
         "Manual: periksa tegangan suplai dan konektor pemilih 100 V/200 V. Pemeriksaan listrik/PCB harus dilakukan teknisi kompeten dengan prosedur keselamatan."),
"E813": ("Tegangan rendah",
         "Tegangan suplai terlalu rendah atau konfigurasi tegangan tidak cocok; manual juga menyebut kemungkinan kerusakan rangkaian internal akibat tegangan berlebih.",
         "Manual: periksa tegangan suplai dan konektor pemilih 100 V/200 V. Pemeriksaan listrik/PCB harus dilakukan teknisi kompeten."),
"E815": ("Resistor regeneratif tidak terhubung",
         "Resistor regeneratif tidak terhubung.",
         "Manual: periksa sambungan resistor regeneratif pada konektor CN11. Matikan daya sebelum pemeriksaan."),
"E903": ("Gangguan catu daya 85 V",
         "Tegangan 85 V tidak keluar dengan benar.",
         "Manual: periksa kemungkinan motor bermasalah dan sekring F2. Pemeriksaan kelistrikan oleh teknisi kompeten."),
"E904": ("Gangguan catu daya 24 V",
         "Tegangan 24 V tidak keluar dengan benar.",
         "Manual tidak mencantumkan item pemeriksaan pada baris ini; serahkan pemeriksaan rangkaian kepada teknisi kompeten."),
"E910": ("Error pencarian titik asal motor presser",
         "Motor presser gagal kembali ke titik asal.",
         "Manual: periksa pengaturan presser (memory switch No. 23) dan penyetelan titik asal motor presser."),
"E912": ("Error deteksi kecepatan motor poros utama",
         "Motor poros utama berjalan melebihi kecepatan yang diperkirakan.",
         "Manual: periksa sambungan kabel encoder dan kabel motor poros utama."),
"E915": ("Gangguan komunikasi dengan panel operasi",
         "Konektor panel operasi tidak terpasang dengan benar.",
         "Manual: periksa koneksi CN38 pada CTL PCB atau CN200 pada panel, serta kemungkinan kabel putus."),
"E922": ("Kegagalan kontrol poros utama",
         "Poros utama tidak beroperasi sebagaimana mestinya.",
         "Manual tidak mencantumkan item pemeriksaan pada baris ini; perlu diagnosis teknisi kompeten."),
"E924": ("Gangguan driver motor",
         "Driver motor rusak.",
         "Manual tidak mencantumkan item pemeriksaan pada baris ini; diagnosis dan penggantian oleh teknisi kompeten."),
"E946": ("Error penulisan EEPROM kepala mesin",
         "Data tidak dapat ditulis ke EEPROM kepala mesin.",
         "Manual: periksa koneksi INT PCB kepala mesin."),
"E955": ("Error sensor arus listrik",
         "Arus motor poros utama melebihi nilai yang diperkirakan.",
         "Manual: periksa sambungan kabel daya motor poros utama."),
"E961": ("Error deviasi motor pitch",
         "Motor pitch gagal bekerja akibat beban berlebih.",
         "Manual: periksa apakah motor pitch bergerak dengan lancar."),
"E962": ("Error deviasi motor presser",
         "Presser gagal bekerja akibat beban berlebih.",
         "Manual: periksa apakah motor presser bergerak dengan lancar."),
"E971": ("Proteksi arus berlebih IPM motor feed horizontal",
         "Operasi motor pitch tidak normal.",
         "Manual tidak mencantumkan item pemeriksaan pada baris ini."),
"E972": ("Motor feed horizontal overload",
         "Motor pitch menerima beban berlebih.",
         "Manual: periksa apakah motor pitch bergerak dengan lancar."),
"E973": ("Proteksi arus berlebih IPM motor feed vertikal",
         "Operasi motor penggerak feed tidak normal.",
         "Manual tidak mencantumkan item pemeriksaan pada baris ini."),
"E974": ("Motor feed vertikal overload",
         "Motor penggerak feed menerima beban berlebih.",
         "Manual: periksa apakah motor penggerak feed bergerak dengan lancar."),
"E975": ("Proteksi arus berlebih IPM motor presser",
         "Operasi motor presser tidak normal.",
         "Manual tidak mencantumkan item pemeriksaan pada baris ini."),
"E976": ("Motor presser horizontal overload",
         "Motor presser menerima beban berlebih.",
         "Manual: periksa apakah motor presser bergerak dengan lancar."),
"E985": ("Error pengembalian ke titik asal motor pitch atau feed",
         "Motor pitch atau motor penggerak feed gagal kembali ke titik asal.",
         "Manual: periksa penyetelan titik asal motor pitch dan motor penggerak feed."),
}

assert len(codes) == 43, f"Jumlah kode tidak sesuai: {len(codes)}"
assert len(set(codes)) == 43, "Kode duplikat ditemukan"
assert set(codes) == set(data), "Ada kode yang belum memiliki data atau kode tambahan"

source_url = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ddl9000cs/menu/ddl9000cs/pdf/instruction_eg.pdf"
)

fields = [
    "target_machine_id", "target_model", "reference_machine_id",
    "reference_model", "code", "problem", "symptoms",
    "possible_cause", "solution", "safety_notes", "source",
    "review_status"
]

with output_file.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for code in codes:
        problem, cause, solution = data[code]
        if code == "E000":
            symptoms = "Operasi inisialisasi data; manual menyatakan ini bukan error."
        else:
            symptoms = "Gejala yang tersedia pada kutipan adalah kondisi penyebab yang tercantum di manual; tidak ada gejala tambahan yang diasumsikan."

        writer.writerow({
            "target_machine_id": 17,
            "target_model": "DDL-9000CS",
            "reference_machine_id": "",
            "reference_model": "DDL-9000C-S",
            "code": code,
            "problem": problem,
            "symptoms": symptoms,
            "possible_cause": cause,
            "solution": solution,
            "safety_notes": (
                "Draf referensi manual. Cocokkan varian mesin terlebih dahulu. "
                "Matikan dan cabut sumber daya sebelum pemeriksaan fisik yang memerlukannya. "
                "Pekerjaan pada tegangan, PCB, motor, encoder, dan rangkaian internal "
                "hanya untuk teknisi kompeten. Jangan menjalankan mesin bila kondisi tidak aman."
            ),
            "source": f"{source_url} (bagian 4-6, halaman cetak 52-54)",
            "review_status": "DRAF_PERLU_VERIFIKASI_TEKNIS"
        })

# Validasi hasil tertulis; database tidak dibuka.
with output_file.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

assert len(rows) == 43, f"Jumlah baris salah: {len(rows)}"
assert len({r["code"] for r in rows}) == 43, "Kode duplikat"
assert all(r["target_machine_id"] == "17" for r in rows)
assert all(r["review_status"] == "DRAF_PERLU_VERIFIKASI_TEKNIS" for r in rows)
assert all(r["problem"] and r["possible_cause"] and r["solution"] for r in rows)
assert not any("placeholder" in r["problem"].lower() for r in rows)

print("CSV revisi berhasil dibuat:", output_file)
print("Jumlah baris:", len(rows))
print("Jumlah kode unik:", len({r['code'] for r in rows}))
print("Kode E000:", next(r["problem"] for r in rows if r["code"] == "E000"))
print("Status seluruh baris: DRAF_PERLU_VERIFIKASI_TEKNIS")
print("Database tidak diubah.")
