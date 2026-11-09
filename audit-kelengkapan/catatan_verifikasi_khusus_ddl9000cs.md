# Catatan Verifikasi Khusus — JUKI DDL-9000CS

## Status

Dokumen tambahan audit teknis. Tidak mengubah database.
Seluruh kode tetap DRAF_PERLU_VERIFIKASI_TEKNIS.

Acuan awal: JUKI DDL-9000C-S Instruction Manual,
bagian 4-6, List of errors, halaman cetak 52–54.
Kecocokan manual dengan varian mesin DDL-9000CS masih perlu dikonfirmasi.

## Temuan per kode

### E000 — Inisialisasi data (bukan error)
- Isi database: manual menyatakan ini bukan error.
- Penilaian: secara umum sesuai dengan keterangan manual yang telah ditinjau.
- Tindak lanjut: pastikan teks aplikasi tidak menyarankan perbaikan untuk kode ini.

### E072 — Motor overload saat thread trimmer beroperasi
- Kondisi gangguan sudah dijelaskan dalam database.
- Bagian manual yang ditinjau tidak memberikan item pemeriksaan untuk baris ini.
- Tindak lanjut: pertahankan solusi konservatif; cari dokumentasi resmi tambahan atau konfirmasi teknisi sebelum menambahkan prosedur.

### E904 — Gangguan catu daya 24 V
- Database menyebut tegangan 24 V tidak keluar dengan benar.
- Bagian manual yang ditinjau tidak memberikan item pemeriksaan untuk baris ini.
- Tindak lanjut: pemeriksaan rangkaian catu daya hanya oleh teknisi kompeten. Jangan menambahkan langkah pengukuran atau perbaikan rinci tanpa prosedur resmi yang sesuai varian.

### E922 — Kegagalan kontrol poros utama
- Kondisi gangguan terkait operasi poros utama.
- Bagian manual yang ditinjau tidak memberikan item pemeriksaan untuk baris ini.
- Tindak lanjut: jangan menyimpulkan penyebab komponen tertentu hanya dari kode. Minta diagnosis teknisi atau sumber resmi tambahan.

### E924 — Gangguan driver motor
- Database menyebut kemungkinan driver motor rusak.
- Bagian manual yang ditinjau tidak memberikan item pemeriksaan untuk baris ini.
- Tindak lanjut: perlakukan kerusakan driver sebagai kemungkinan yang perlu diagnosis, bukan kesimpulan final. Pekerjaan pada driver dan rangkaian internal hanya untuk teknisi kompeten.

### E971 — Proteksi arus berlebih IPM motor feed horizontal
- Database mengaitkan kondisi dengan operasi motor pitch yang tidak normal.
- Bagian manual yang ditinjau tidak memberikan item pemeriksaan untuk baris ini.
- Tindak lanjut: verifikasi terminologi motor dan cakupan fungsi terhadap varian mesin. Jangan menambahkan langkah servis yang belum didukung manual.

### E973 — Proteksi arus berlebih IPM motor feed vertikal
- Database mengaitkan kondisi dengan operasi motor penggerak feed yang tidak normal.
- Bagian manual yang ditinjau tidak memberikan item pemeriksaan untuk baris ini.
- Tindak lanjut: pastikan nama motor sesuai nomenklatur resmi varian. Serahkan diagnosis rangkaian penggerak kepada teknisi kompeten.

### E975 — Proteksi arus berlebih IPM motor presser
- Database mengaitkan kondisi dengan operasi motor presser yang tidak normal.
- Bagian manual yang ditinjau tidak memberikan item pemeriksaan untuk baris ini.
- Tindak lanjut: verifikasi istilah motor presser terhadap manual varian dan hindari menambahkan langkah perbaikan tanpa sumber resmi.

## Keputusan audit sementara

1. E000 dapat dipertahankan sebagai kode informatif/non-error setelah kecocokan varian dipastikan.
2. Tujuh kode lainnya memiliki uraian kondisi gangguan, tetapi langkah penanganannya belum terverifikasi dari bagian manual yang ditinjau.
3. Ketiadaan item pemeriksaan pada bagian yang ditinjau bukan bukti bahwa prosedur tidak tersedia di dokumentasi lain.
4. Jangan menandai kode sebagai terverifikasi final sampai sumber yang tepat atau konfirmasi teknis tersedia.
5. Tidak ada perubahan database yang dilakukan.

## Manual resmi

https://www.juki.co.jp/industrial_j/download_j/manual_j/ddl9000cs/menu/ddl9000cs/pdf/instruction_eg.pdf
