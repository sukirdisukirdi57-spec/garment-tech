# Verifikasi Manual DDL-9000CS — Batch 3

Tanggal: 2026-10-21
Sumber: JUKI DDL-9000C-S Instruction Manual
Bagian: 4-6, List of errors, halaman cetak 52-54
Referensi:
https://www.juki.co.jp/industrial_j/download_j/manual_j/ddl9000cs/menu/ddl9000cs/pdf/instruction_eg.pdf

Status: catatan audit berdasarkan teks manual; database tidak diubah.

| Kode | Hasil pencocokan manual | Tindak lanjut |
|---|---|---|
| E011-E016 | Manual mencantumkan tindakan umum mematikan daya dan memeriksa media. | Pertahankan sebagai kutipan umum; jangan mengklaim langkah lebih spesifik berasal dari manual tanpa bukti. |
| E032 | Manual mencantumkan tindakan mematikan daya dan memeriksa media. | Pertahankan; solusi tambahan perlu diberi label rekomendasi, bukan kutipan manual. |
| E220 | Peringatan saat jumlah jahitan yang ditentukan tercapai; tambahkan grease di titik yang ditentukan dan reset error. | Bedakan dari E221; pastikan jenis grease dan titik pelumasan sesuai manual lengkap. |
| E221 | Mesin tidak dapat melanjutkan jahitan karena jumlah jahitan yang ditentukan tercapai; tambahkan grease dan reset error. | Pertahankan perbedaan dari E220. |
| E302 | Sakelar deteksi kemiringan aktif; manual melarang pengoperasian demi keselamatan dan menyebut pemeriksaan kabel sakelar serta kabel INT PCB. | Pertahankan larangan operasi; jangan menganjurkan bypass interlock. |
| E730-E731 | Manual mengelompokkan pemeriksaan sinyal motor: konektor CN39, kabel, dan arah pemasangan konektor encoder. | Pertahankan kode dan deskripsi terpisah; verifikasi kecocokan varian. |
| E811 | Tegangan input terlalu tinggi atau konfigurasi suplai tidak cocok. | Pemeriksaan listrik dan konfigurasi hanya oleh teknisi kompeten. |
| E813 | Tegangan input terlalu rendah atau konfigurasi suplai tidak cocok; manual juga menyebut kemungkinan kerusakan rangkaian internal akibat overvoltage. | Jangan menyarankan pengguna mengubah konektor pemilih tegangan. |
| E815 | Manual menyebut pemeriksaan konektor resistor regeneratif CN11. | Isolasi daya dan verifikasi diagram unit sebelum pemeriksaan. |
| E903 | Manual menyebut pemeriksaan motor dan sekring F2. | Pemeriksaan kelistrikan oleh teknisi kompeten. |
| E904 | Catu daya 24 V tidak keluar dengan benar; tidak ada item pemeriksaan pada baris manual. | Jangan mengarang langkah diagnosis; rujuk teknisi. |
| E910 | Manual menyebut memory switch No. 23 dan penyetelan titik asal motor presser. | Verifikasi varian dan prosedur sebelum publikasi. |
| E912 | Manual menyebut pemeriksaan koneksi kabel encoder dan kabel daya motor poros utama. | Pemeriksaan konektor internal oleh teknisi kompeten. |
| E915 | Manual menyebut konektor CN38 pada CTL PCB atau CN200 pada panel, serta kemungkinan kabel putus. | Verifikasi nomor konektor pada varian mesin. |

Catatan:
- Semua hasil tetap berupa catatan audit; belum merupakan persetujuan perubahan database.
- Pekerjaan pada PCB, rangkaian listrik, konektor internal, dan konfigurasi tegangan dilakukan teknisi kompeten.
- Kecocokan manual dengan varian mesin fisik tetap perlu dikonfirmasi.
