# Catatan Koreksi Matriks Audit — JUKI DDL-9000CS

Tanggal: 2026-10-21
Tujuan: menyelaraskan temuan matriks Revisi 2 dengan hasil pembacaan manual.
Ruang lingkup: dokumen audit saja; database tidak diubah.

## 1. Koreksi temuan lama

### E007 — ID 1416
Hasil pembacaan manual: manual menyebut "Motor overload" dan kondisi kepala mesin diganti.

Koreksi temuan:
- Hapus pernyataan bahwa deskripsi dan penyebab belum dicocokkan.
- Catat bahwa teks tersebut sesuai dengan uraian manual yang diperiksa.
- Manual tidak memberikan langkah pemeriksaan khusus pada baris yang dirujuk.
- Jangan menambahkan prosedur perbaikan tanpa sumber pendukung.

### E009 — ID 1417
Hasil pembacaan manual: solenoid energized terlalu lama. Penyebab yang tercantum meliputi kepala terkunci, bahan terlalu berat, motor tidak berputar, atau gangguan motor/driver. Pemeriksaan yang dicantumkan meliputi pulley yang terlilit benang, konektor output motor, dan kelancaran putaran motor dengan tangan.

Koreksi temuan:
- Ganti temuan lama yang menyatakan langkah pemeriksaan perlu diselaraskan dengan deskripsi.
- Catat bahwa langkah pemeriksaan tersebut memang tercantum pada uraian E009 di manual yang diperiksa.
- Pemeriksaan fisik hanya dilakukan setelah mesin dimatikan dan sumber energi diisolasi sesuai prosedur servis.
- Kecocokan varian mesin tetap perlu dikonfirmasi.

## 2. Hasil manual tambahan untuk kode yang perlu dirangkum

### E081 — ID 1427
Manual menyebut motor penggerak feed terkunci dan pemeriksaan kelancaran gerak motor. Pertahankan sebagai draf; pastikan istilah motor sesuai varian.

### E733 — ID 1436
Manual menyebut arah putaran motor berlawanan dengan arah yang ditentukan ketika motor beroperasi pada 500 sti/min atau lebih. Pemeriksaan mengacu pada kabel encoder motor poros utama dan kabel daya motor.

### E946 — ID 1447
Manual menyebut kegagalan penulisan EEPROM kepala mesin dan pemeriksaan koneksi INT PCB. Pemeriksaan PCB dilakukan teknisi kompeten.

### E955 — ID 1448
Manual menyebut arus motor poros utama melebihi nilai yang diperkirakan dan pemeriksaan koneksi kabel daya motor. Jangan menyimpulkan sensor pasti rusak hanya dari nama kode.

### E961 — ID 1449
Manual menyebut motor pitch gagal bekerja akibat beban berlebih dan pemeriksaan kelancaran motor.

### E962 — ID 1450
Manual menyebut motor presser gagal bekerja akibat beban berlebih dan pemeriksaan kelancaran motor.

### E971 — ID 1451
Manual menyebut proteksi arus berlebih IPM pada motor feed horizontal dan penyebab terkait operasi motor pitch yang tidak normal. Tidak ada langkah pemeriksaan spesifik pada baris yang diperiksa. Jangan menyalin solusi E972.

### E972 — ID 1452
Manual menyebut motor feed horizontal overload, penyebab terkait beban berlebih pada motor pitch, serta pemeriksaan kelancaran motor pitch. Pertahankan istilah sesuai teks manual; jangan mengubahnya berdasarkan dugaan.

### E973 — ID 1453
Manual menyebut proteksi arus berlebih IPM pada motor feed vertikal dan penyebab terkait operasi motor penggerak feed yang tidak normal. Tidak ada langkah pemeriksaan spesifik pada baris yang diperiksa. Jangan menyalin solusi E974.

### E974 — ID 1454
Manual menyebut motor feed vertikal overload, penyebab terkait beban berlebih pada motor penggerak feed, serta pemeriksaan kelancaran motor penggerak feed.

### E975 — ID 1455
Manual menyebut proteksi arus berlebih IPM motor presser dan penyebab terkait operasi motor presser yang tidak normal. Tidak ada langkah pemeriksaan spesifik pada baris yang diperiksa. Jangan menyalin solusi E976.

### E976 — ID 1456
Manual menyebut motor presser horizontal overload, penyebab terkait beban berlebih pada motor presser, serta pemeriksaan kelancaran motor presser.

### E985 — ID 1457
Manual menyebut kegagalan motor pitch atau motor penggerak feed kembali ke titik asal. Pemeriksaan mengacu pada penyetelan titik asal motor yang bersangkutan.

## 3. Prinsip koreksi matriks

1. Perbarui temuan lama E007 dan E009 agar sesuai dengan hasil pembacaan manual.
2. Pertahankan kode E971, E973, dan E975 tanpa menambahkan langkah pemeriksaan yang tidak dicantumkan pada baris manual.
3. Jangan menganggap pasangan E971/E972, E973/E974, dan E975/E976 mempunyai solusi yang sama.
4. Pertahankan semua 43 baris sebagai DRAF_PERLU_VERIFIKASI_TEKNIS.
5. Pastikan varian fisik, panel, kotak kontrol, dan versi sistem cocok dengan manual sebelum persetujuan teknis.
6. Pekerjaan pada rangkaian listrik, PCB, motor driver, dan konektor internal harus dilakukan teknisi kompeten dengan prosedur keselamatan yang sesuai.

## 4. Batasan

Catatan ini merupakan koreksi dokumentasi berdasarkan hasil pembacaan teks manual yang dicatat selama audit. Catatan ini bukan sertifikasi teknis dan tidak menyetujui perubahan database.

Database tidak diubah.
