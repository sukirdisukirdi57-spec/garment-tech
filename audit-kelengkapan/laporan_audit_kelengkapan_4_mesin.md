# Laporan Audit Kelengkapan Data — Empat Mesin

Tanggal audit: 2026-10-21
Mode: baca-saja; database tidak diubah.

## 1. Ringkasan database

- Total mesin: 225
- Total troubleshooting: 1492
- Total baris empat mesin target: 177
- Baris troubleshooting tanpa mesin terkait: 0
- Integritas SQLite: ok
- Foreign key errors: 0

## 2. Ringkasan per mesin

| Mesin | Baris | Kode kosong | Kode unik | Kode duplikat | Sumber kosong | Baris berstatus draf |
|---|---:|---:|---:|---:|---:|---:|
| JUKI DDL-8000C (ID 16) | 33 | 0 | 33 | 0 | 0 | 33 |
| JUKI DDL-9000CS (ID 17) | 43 | 0 | 43 | 0 | 0 | 43 |
| LYGOLD LGA105E-BUT (ID 226) | 8 | 8 | 0 | 0 | 0 | 8 |
| BROTHER BAS-311HN-03S (ID 227) | 93 | 19 | 74 | 0 | 0 | 93 |

## 3. Kelengkapan enam kolom

Angka menunjukkan jumlah baris yang kolomnya kosong atau hanya berisi spasi.

| Mesin | Problem | Symptoms | Possible cause | Solution | Safety notes | Source |
|---|---:|---:|---:|---:|---:|---:|
| JUKI DDL-8000C (ID 16) | 0 | 0 | 0 | 0 | 0 | 0 |
| JUKI DDL-9000CS (ID 17) | 0 | 0 | 0 | 0 | 0 | 0 |
| LYGOLD LGA105E-BUT (ID 226) | 0 | 0 | 0 | 0 | 0 | 0 |
| BROTHER BAS-311HN-03S (ID 227) | 0 | 0 | 0 | 0 | 0 | 0 |

## 4. Rincian masalah yang ditemukan

### JUKI DDL-8000C (ID 16)

- Tidak ditemukan kolom kosong, kode kosong, atau kode duplikat dalam pemeriksaan dasar.
- Kelengkapan isi tidak otomatis membuktikan akurasi teknis.

### JUKI DDL-9000CS (ID 17)

- Tidak ditemukan kolom kosong, kode kosong, atau kode duplikat dalam pemeriksaan dasar.
- Kelengkapan isi tidak otomatis membuktikan akurasi teknis.

### LYGOLD LGA105E-BUT (ID 226)

- Kode kosong pada 8 baris.
- Kelengkapan isi tidak otomatis membuktikan akurasi teknis.

### BROTHER BAS-311HN-03S (ID 227)

- Kode kosong pada 19 baris.
- Kelengkapan isi tidak otomatis membuktikan akurasi teknis.

## 5. Batasan interpretasi

- Kode kosong dapat wajar untuk troubleshooting umum yang bukan kode alarm.
- Kode duplikat dihitung per mesin setelah spasi dibuang dan huruf diubah menjadi kapital; duplikat belum tentu salah jika memang memiliki makna berbeda.
- Penanda draf diperiksa dari kolom `source` karena tabel belum memiliki kolom status terpisah.
- Pemeriksaan ini mengukur kelengkapan struktural, bukan kebenaran diagnosis atau keamanan solusi.
- Semua perubahan data harus melalui persetujuan eksplisit dan pencadangan terlebih dahulu.

## 6. Kesimpulan

Gunakan hasil per mesin dan per kolom untuk menentukan prioritas perbaikan dokumentasi. Jangan mengubah data hanya berdasarkan jumlah kosong; tinjau konteks setiap baris terlebih dahulu.

Database tidak diubah dalam audit ini.
