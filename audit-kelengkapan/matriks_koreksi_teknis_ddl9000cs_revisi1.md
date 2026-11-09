# Matriks Koreksi Teknis — JUKI DDL-9000CS

> Status: DRAF. Dokumen ini adalah daftar kerja audit, bukan panduan servis tervalidasi.
> Database dibuka dalam mode baca-saja; file database tidak diubah oleh skrip ini.

## Ringkasan

- Jumlah entri yang diperiksa: 43
- Kode unik: 43
- Integritas SQLite: `ok`
- Foreign-key error: 0
- Referensi utama: manual JUKI `DDL-9000C-S INSTRUCTION MANUAL`, bagian 4-6, daftar error, halaman cetak 52–54.
- Kecocokan varian `DDL-9000CS` dengan cakupan manual tetap perlu dikonfirmasi.
- Tidak ada perubahan pada database.

## Matriks per kode

| ID | Kode | Masalah saat ini | Temuan audit | Koreksi/tindak lanjut yang disarankan | Dasar verifikasi | Status |
|---:|---|---|---|---|---|---|
| 1415 | E000 | Inisialisasi data (bukan error) | Informasi inisialisasi, bukan kerusakan menurut data saat ini. | Pisahkan sebagai informasi/status, bukan prosedur perbaikan. | Konfirmasi redaksi pada manual dan kondisi yang memicu kode. | Perlu konfirmasi manual |
| 1416 | E007 | Motor overload | Penyebab yang tersimpan menyebut penggantian kepala mesin, sedangkan solusi belum spesifik. | Periksa ulang judul kode, penyebab, dan prosedur pada manual; jangan menebak langkah perbaikan. | Manual resmi, bagian daftar error; cocokkan varian kontrol. | Prioritas tinggi |
| 1417 | E009 | Solenoid energized terlalu lama | Pemetaan kode perlu ditinjau karena uraian masalah solenoid dan solusi tentang pulley/motor berpotensi tidak selaras. | Cocokkan teks kode, penyebab, dan solusi baris ini dengan manual asli sebelum mempertahankan solusi. | Manual resmi, bagian daftar error; verifikasi pemetaan kode. | Prioritas tinggi |
| 1418 | E011 | Media tidak terpasang | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1419 | E012 | Kesalahan membaca data | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1420 | E013 | Kesalahan menulis data | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1421 | E014 | Media terlindungi dari penulisan | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1422 | E015 | Kesalahan format media | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1423 | E016 | Kapasitas media tidak mencukupi | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1424 | E032 | Kesalahan kompatibilitas file | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1425 | E071 | Konektor motor terlepas | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1426 | E072 | Motor overload saat thread trimmer beroperasi | Solusi hanya menyatakan manual tidak mencantumkan item pemeriksaan. | Periksa konteks lengkap baris manual. Jika memang tidak ada langkah tambahan, pertahankan sebagai eskalasi teknisi tanpa menambahkan dugaan. | Manual resmi, bagian daftar error. | Perlu verifikasi manual |
| 1427 | E081 | Motor penggerak feed terkunci | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1428 | E204 | USB masih terpasang | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1429 | E220 | Peringatan kekurangan grease | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1430 | E221 | Error kekurangan grease | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1431 | E302 | Error deteksi kemiringan kepala mesin | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1432 | E303 | Kesalahan sensor meniskus (meniscus sensor) | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1433 | E704 | Kegagalan data / ketidakcocokan versi sistem | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1434 | E730 | Gangguan encoder | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1435 | E731 | Gangguan sensor lubang motor | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1436 | E733 | Motor berputar terbalik | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1437 | E811 | Tegangan berlebih | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1438 | E813 | Tegangan rendah | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1439 | E815 | Resistor regeneratif tidak terhubung | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1440 | E903 | Gangguan catu daya 85 V | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1441 | E904 | Gangguan catu daya 24 V | Solusi belum memberikan langkah pemeriksaan spesifik. | Pastikan manual memang tidak mencantumkan pemeriksaan lain; pemeriksaan catu daya internal hanya oleh teknisi kompeten. | Manual resmi, bagian daftar error. | Perlu verifikasi manual |
| 1442 | E910 | Error pencarian titik asal motor presser | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1443 | E912 | Error deteksi kecepatan motor poros utama | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1444 | E915 | Gangguan komunikasi dengan panel operasi | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1445 | E922 | Kegagalan kontrol poros utama | Solusi belum memberikan item pemeriksaan spesifik. | Periksa teks lengkap manual dan dokumentasi servis yang sesuai; jangan menambahkan diagnosis tanpa sumber. | Manual resmi dan dokumentasi servis yang cocok dengan varian. | Perlu verifikasi manual |
| 1446 | E924 | Gangguan driver motor | Solusi belum memberikan item pemeriksaan spesifik. | Konfirmasi apakah manual mengarahkan ke penggantian/servis driver; jangan menyimpulkan komponen rusak hanya dari kode. | Manual resmi dan dokumentasi servis yang cocok dengan varian. | Perlu verifikasi manual |
| 1447 | E946 | Error penulisan EEPROM kepala mesin | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1448 | E955 | Error sensor arus listrik | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1449 | E961 | Error deviasi motor pitch | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1450 | E962 | Error deviasi motor presser | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1451 | E971 | Proteksi arus berlebih IPM motor feed horizontal | Solusi belum memberikan item pemeriksaan spesifik. | Cocokkan dengan manual lengkap. Jangan mengarang prosedur untuk proteksi arus berlebih IPM. | Manual resmi, bagian daftar error. | Perlu verifikasi manual |
| 1452 | E972 | Motor feed horizontal overload | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1453 | E973 | Proteksi arus berlebih IPM motor feed vertikal | Solusi belum memberikan item pemeriksaan spesifik. | Cocokkan dengan manual lengkap. Jangan mengarang prosedur untuk proteksi arus berlebih IPM. | Manual resmi, bagian daftar error. | Perlu verifikasi manual |
| 1454 | E974 | Motor feed vertikal overload | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1455 | E975 | Proteksi arus berlebih IPM motor presser | Solusi belum memberikan item pemeriksaan spesifik. | Cocokkan dengan manual lengkap. Jangan mengarang prosedur untuk proteksi arus berlebih IPM. | Manual resmi, bagian daftar error. | Perlu verifikasi manual |
| 1456 | E976 | Motor presser horizontal overload | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |
| 1457 | E985 | Error pengembalian ke titik asal motor pitch atau feed | Belum ditandai sebagai anomali khusus pada audit awal; tetap perlu pemeriksaan baris demi baris. | Bandingkan kode, uraian, penyebab, dan setiap langkah solusi dengan teks manual. Pertahankan hanya langkah yang didukung sumber; tandai bagian yang belum terbukti. | Manual resmi, bagian daftar error; pastikan halaman dan varian sesuai. | Belum diverifikasi satu per satu |

## Aturan penerimaan revisi

1. Jangan menandai solusi sebagai tervalidasi hanya karena terdengar masuk akal.
2. Catat halaman manual dan teks pendukung untuk setiap koreksi teknis.
3. Jika manual tidak memberi langkah pemeriksaan, tulis secara eksplisit bahwa langkah tidak ditemukan; jangan membuat prosedur sendiri.
4. Prosedur terkait tegangan, PCB, driver, motor, encoder, dan rangkaian internal harus diarahkan kepada teknisi kompeten.
5. Pastikan model kepala mesin, panel, dan kotak kontrol cocok dengan manual sebelum mengesahkan instruksi.
6. Perubahan database baru dilakukan setelah matriks ditinjau dan mendapat persetujuan eksplisit.

## Hasil validasi pembuatan matriks

- Baris dibaca: 43
- Kode unik: 43
- SQLite integrity check: `ok`
- Foreign-key errors: 0
- Database diakses dengan `mode=ro`; tidak ada operasi tulis ke database.

---

## Revisi 1 — temuan manual dan tindak lanjut

Tanggal audit: 2026-10-21

Status: DRAF. Belum disetujui sebagai perubahan data produksi.

Manual pembanding:
- JUKI DDL-9000C-S Instruction Manual, bagian 4-6, daftar error.
  https://juki.com/pub/media/wysiwyg/products/DDL9000CSeries_manual.pdf
- Halaman produk JUKI DDL-9000C Series:
  https://juki.com/ddl-9000c-series

Kesesuaian manual dengan varian fisik DDL-9000CS serta control box harus
dipastikan sebelum prosedur teknis dianggap tervalidasi.

| Kode | Temuan pembanding | Tindak lanjut | Status |
|---|---|---|---|
| E000 | Inisialisasi data; manual menyatakan bukan error. | Kategorikan sebagai informasi/status, bukan kerusakan. Jelaskan dampak inisialisasi sebelum menyarankannya. | Didukung manual; redaksi ditinjau |
| E007 | Deskripsi manual menyebut motor overload; penggantian kepala mesin muncul sebagai konteks penyebab. | Cocokkan penyebab dan tindakan di database dengan manual yang sesuai; jangan menyimpulkan motor rusak hanya dari kode. | Perlu tinjau pemetaan |
| E009 | Solenoid energized terlalu lama. Item pemeriksaan mencakup pulley terlilit benang, konektor keluaran motor, dan kelancaran putaran pulley. | Cocokkan solusi yang tersimpan dengan daftar manual. Matikan dan amankan daya sebelum pemeriksaan fisik; kelistrikan oleh teknisi. | Deskripsi dan pemeriksaan didukung manual |
| E072 | Motor overload saat thread trimmer bekerja; manual instruksi tidak memberi item pemeriksaan spesifik pada baris tersebut. | Jangan mengarang prosedur. Catat kondisi error dan eskalasikan ke teknisi. | Prosedur lanjutan belum tersedia |
| E904 | Gangguan catu daya 24 V; tidak ada item pemeriksaan spesifik yang terkonfirmasi pada baris manual instruksi. | Jangan menyarankan pengguna memeriksa tegangan internal; rujuk teknisi kompeten. | Perlu dokumentasi servis |
| E922 | Kegagalan kontrol poros utama; tindakan khusus belum terkonfirmasi. | Jangan menetapkan komponen rusak atau menyarankan penggantian tanpa bukti. | Perlu verifikasi manual/servis |
| E924 | Gangguan driver motor; tindakan khusus belum terkonfirmasi. | Verifikasi dokumentasi servis sesuai control box; jangan langsung menyimpulkan driver harus diganti. | Perlu verifikasi manual/servis |
| E971 | Proteksi arus berlebih IPM motor feed horizontal; prosedur khusus belum terkonfirmasi. | Jangan menambahkan prosedur kelistrikan tanpa sumber; eskalasi diagnosis ke teknisi. | Perlu verifikasi manual/servis |
| E973 | Proteksi arus berlebih IPM motor feed vertikal; prosedur khusus belum terkonfirmasi. | Jangan menambahkan prosedur kelistrikan tanpa sumber; eskalasi diagnosis ke teknisi. | Perlu verifikasi manual/servis |
| E975 | Proteksi arus berlebih IPM motor presser; prosedur khusus belum terkonfirmasi. | Jangan menambahkan prosedur kelistrikan tanpa sumber; eskalasi diagnosis ke teknisi. | Perlu verifikasi manual/servis |

### Aturan revisi

1. Jangan mengubah kode berdasarkan dugaan.
2. Pisahkan deskripsi error, kemungkinan penyebab, item pemeriksaan manual,
   dan tindakan teknisi.
3. Jika manual instruksi tidak menyebut tindakan, catat keterbatasan sumber.
4. Pastikan varian mesin, control box, dan versi manual sesuai.
5. Semua entri tetap berstatus draf sampai verifikasi teknis disetujui.
6. Dokumen ini tidak mengubah database SQLite.

### Ringkasan pemeriksaan

- Baris troubleshooting machine_id 17: 43
- Kode unik: 43
- SQLite integrity_check: ok
- Foreign-key error: 0
- Database diubah: tidak
