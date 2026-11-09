# Audit Teknis Lanjutan — JUKI DDL-8000C

## Sumber
- Manual resmi JUKI DDL-8000C:
  https://www.juki.co.jp/industrial_j/download_j/manual_j/ddl8000c/menu/8000c/pdf/instruction_jp.pdf
- Bagian: 5-4 エラーコード一覧 (Daftar Kode Error)
- Halaman cetak yang diperiksa: 52–57
- Status: DRAF_PERLU_VERIFIKASI_TEKNIS
- Catatan: kecocokan varian mesin dan konfigurasi listrik tetap perlu dikonfirmasi.

## Temuan terverifikasi dari kutipan manual

| Kode | Temuan audit |
|---|---|
| E01 | Tegangan input terlalu tinggi. Manual menyebut ambang AC300V (AC130V); pastikan konfigurasi unit sebelum menerapkan angka dalam panduan pengguna. |
| E02 | Tegangan input terlalu rendah. Manual menyebut ambang AC150V (AC80V); pastikan konfigurasi unit sebelum menerapkan angka dalam panduan pengguna. |
| E03 | Gangguan komunikasi CPU; manual menyebut pemeriksaan konektor dan kabel panel. |
| E05 | Sinyal pedal tidak normal; manual menyebut pemeriksaan konektor dan kabel pedal. |
| E07 | Rotor motor poros utama terkunci; periksa hambatan mekanis dan konektor sesuai prosedur aman. |
| E09 | Sinyal penentuan posisi atas encoder motor poros utama tidak normal. |
| E10 | Arus berlebih pada solenoid; prosedur diagnosis rinci perlu ditangani teknisi kompeten. |
| E11 | Deskripsi sama dengan E09 dalam manual; jangan dianggap duplikat untuk dihapus. |
| E14 | Sinyal encoder motor poros utama tidak normal; manual juga membahas pemasangan dan kebersihan encoder disk. |
| E15 | Arus motor poros utama berlebih; manual menyebut pemeriksaan konektor/kabel daya motor. |
| E17 | Deteksi kepala mesin miring; manual menyebut pemeriksaan posisi kepala dan penyetelan sensor. |
| E20 | Motor poros utama gagal mulai; periksa konektor daya, encoder, dan pengaturan titik asal motor. |
| E32 | Berkas tidak kompatibel. |
| E46 | Gangguan reset watchdog timer; manual menyebut matikan dan hidupkan daya, lalu layanan purnajual bila tetap gagal. |
| E60 | Gangguan resistansi regeneratif; pemeriksaan kerusakan/kekenduran dan penggantian perlu prosedur teknisi. |
| E70 | Kesalahan sistem; manual menyebut mematikan dan menyalakan daya kembali. |
| E71 | Data tersimpan rusak/CRC; manual menyebut inisialisasi melalui parameter U272. Waspadai kehilangan data/pengaturan. |
| E72 | Gangguan hilangnya fase suplai tiga fase; manual menyebut pemeriksaan suplai AC tiga fase 220V dan konektor. Konfirmasi spesifikasi unit. |
| E80 | Gangguan komunikasi chip utama dan chip penggerak; manual mengarahkan ke layanan purnajual/control box. |
| E82 | Arus motor pitch berlebih; periksa kemungkinan motor terkunci dan konektor daya/encoder. |
| E84 | Gangguan fase Z motor pitch; manual membahas hambatan mekanis, konektor, pemasangan encoder disk, dan kontaminasi minyak. |
| E85 | Sinyal encoder motor pitch tidak normal; periksa konektor dan encoder disk. |
| E86 | Motor pitch tidak beroperasi normal; prosedur pemeriksaan mirip E85, tetapi kode tetap terpisah. |
| E87 | Motor pitch terkunci; periksa hambatan mekanis dan konektor daya/encoder. |
| E92 | Arus berlebih pada motor pemotong benang/penekan benang; periksa hambatan mekanis dan konektor. |
| E94 | Gangguan fase Z motor pemotong benang/penekan benang; manual juga menyebut pemeriksaan encoder disk dan minyak. |
| E95 | Sinyal encoder motor pemotong benang/penekan benang tidak normal; periksa konektor encoder. |
| E96 | Motor pemotong benang/penekan benang gagal mulai; periksa konektor daya dan encoder. |
| E97 | Motor pemotong benang/penekan benang terkunci; periksa hambatan mekanis dan konektor. |
| E100 | Beban berlebih motor poros utama; periksa beban mekanis dan pengaturan titik asal motor. |
| E110 | Gangguan penerimaan data panel saat daya dinyalakan; periksa konektor panel. |
| PEDAL | Inisialisasi awal belum selesai; manual menyebut menginjak pedal ke belakang untuk menjalankan inisialisasi. |
| P_OFF | Indikasi daya mati; matikan sakelar dan tunggu layar padam sebelum menyalakan kembali. |

## Tindakan lanjutan
1. Bandingkan setiap baris dengan isi aktual database.
2. Periksa kelengkapan gejala, penyebab, solusi, dan catatan keselamatan.
3. Pertahankan status draf sampai varian mesin, konfigurasi listrik, dan solusi teknis diverifikasi.
4. Jangan mengubah database utama sebelum usulan revisi disetujui.
