-- USULAN TERJEMAHAN SOLUSI JUKI PS-800-12080
-- Khusus machine_id = 11 dan 53 kode yang ditentukan.
-- Hanya mengubah kolom solution.
-- Mode uji: ROLLBACK membatalkan seluruh perubahan.
-- Jangan hapus ROLLBACK sebelum peninjauan dan persetujuan.

.bail on
PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;

UPDATE troubleshooting
SET solution = CASE TRIM(code)
    WHEN 'E001' THEN 'Tekan tombol [Reset] untuk melakukan reset.'
    WHEN 'E002' THEN 'Periksa sensor X untuk memastikan tidak ada masalah kontak atau kerusakan.'
    WHEN 'E003' THEN 'Periksa sensor Y untuk memastikan tidak ada masalah kontak atau kerusakan.'
    WHEN 'E004' THEN 'Periksa sensor Z untuk memastikan tidak ada masalah kontak atau kerusakan.'
    WHEN 'E005' THEN 'Periksa sensor U untuk memastikan tidak ada masalah kontak atau kerusakan.'
    WHEN 'E006' THEN 'Periksa sensor poros untuk memastikan tidak ada masalah kontak atau kerusakan.'
    WHEN 'E007' THEN 'Periksa apakah encoder spindel mengalami kerusakan.'
    WHEN 'E205' THEN 'Tekan tombol “Press the frame” untuk menurunkan rangka.'
    WHEN 'E206' THEN 'Pelat kepala patah. Ganti pelat kepala yang patah dengan pelat baru.'
    WHEN 'E207' THEN 'Periksa sinyal input I/O untuk mengetahui apakah status sinyal input berada pada kondisi HIGH atau LOW.'
    WHEN 'E208' THEN 'Periksa apakah unit pemasok udara menyuplai udara secara normal.'
    WHEN 'E209' THEN 'Periksa apakah sinyal posisi nol (zero signal) motor pemotong benang (clipper motor) berfungsi normal.'
    WHEN 'E210' THEN 'Periksa apakah sinyal posisi nol motor sepatu penekan (presser foot motor) berfungsi normal.'
    WHEN 'E211' THEN 'Periksa apakah sinyal garis nol (zero line signal) motor penjepit benang (wire grab motor) berfungsi normal.'
    WHEN 'E212' THEN 'Periksa apakah sinyal posisi nol motor pemotong (cutter motor) berfungsi normal.'
    WHEN 'E213' THEN 'Jalankan kembali proses penanganan benang, atau nonaktifkan fungsi deteksi benang putus sebelum melanjutkan pengoperasian.'
    WHEN 'E214' THEN 'Nilai penghitung telah mencapai jumlah total yang ditetapkan. Nilai penghitung akan dihapus dan penghitungan dimulai kembali saat operasi dimulai ulang.'
    WHEN 'E215' THEN 'Ganti kait rumah sekoci benang bawah.'
    WHEN 'E216' THEN 'Jumlah titik (pins) dalam file grafis telah melebihi batas maksimum. Ganti file grafis yang sedang digunakan dengan file baru.'
    WHEN 'E217' THEN 'Pindai ulang file grafis atau ganti dengan file grafis lain.'
    WHEN 'E218' THEN 'Waktu antre pemrosesan data grafis bergantung pada ukuran grafis. Tunggu hingga pemrosesan data selesai.'
    WHEN 'E219' THEN 'Hubungi produsen peralatan.'
    WHEN 'E220' THEN 'Ganti file pembaruan (upgrade file) dengan file pembaruan yang baru.'
    WHEN 'E221' THEN 'Pilih jenis file pembaruan yang sesuai dengan file yang akan diperbarui.'
    WHEN 'E222' THEN 'Hubungi produsen peralatan.'
    WHEN 'E223' THEN 'Hubungi produsen peralatan.'
    WHEN 'E224' THEN 'Periksa sambungan kabel ke papan kepala dari kemungkinan kontak buruk atau kerusakan, serta periksa kerusakan pelat kepala mesin.'
    WHEN 'E225' THEN 'Jika sambungan kabel layar tidak longgar atau rusak, periksa apakah papan utama layar (display motherboard) atau kabel listrik mengalami kerusakan dan perlu diganti.'
    WHEN 'E226' THEN 'Ganti file grafis jika file tersebut rusak atau tidak ditujukan untuk digunakan pada jenis sistem ini.'
    WHEN 'E227' THEN 'Jika sambungan kabel layar tidak longgar atau rusak, periksa apakah papan utama layar (display motherboard) atau kabel listrik mengalami kerusakan dan perlu diganti.'
    WHEN 'E228' THEN 'Periksa apakah data file grafis rusak atau berada di luar rentang yang dapat ditoleransi sistem.'
    WHEN 'E229' THEN 'Sudut koreksi grafis terlalu besar. Kurangi nilai sudut perubahan tersebut.'
    WHEN 'E230' THEN 'Proses data grafis yang diperlukan, lalu tunggu beberapa saat sebelum memulai pengoperasian.'
    WHEN 'E231' THEN 'Periksa apakah motor sepatu penekan (presser foot motor) berfungsi normal.'
    WHEN 'E232' THEN 'Masukkan kembali flash disk USB atau ganti dengan flash disk USB yang baru.'
    WHEN 'E233' THEN '1. Ganti file grafis dengan file lain. 2. Masukkan kembali flash disk USB atau ganti dengan flash disk USB yang baru.'
    WHEN 'E234' THEN '1. Atur ulang posisi titik referensi. 2. Atur ulang nilai offset kepala 2 atau kepala 3. 3. Ganti grafis dengan lebar kecil menggunakan grafis dengan lebar normal.'
    WHEN 'E235' THEN 'Ganti file grafis dengan file lain.'
    WHEN 'E236' THEN 'Hubungi produsen peralatan.'
    WHEN 'E237' THEN 'Atur kata sandi administrator terlebih dahulu.'
    WHEN 'E238' THEN 'Perintah atau file tersebut tidak perlu diedit.'
    WHEN 'E239' THEN 'Hubungi produsen peralatan.'
    WHEN 'E240' THEN 'Terjadi kesalahan komunikasi CAN atau program pada papan utama (motherboard) sudah usang.'
    WHEN 'E241' THEN '1. Waktu telah diubah secara tidak sah. 2. Tegangan baterai papan utama (motherboard) rendah.'
    WHEN 'E242' THEN '1. Sinyal input I/O Work Enable tidak normal. 2. Nonaktifkan fungsi input I/O Work Enable dengan mengatur nilai parameter menjadi 0 (nol).'
    WHEN 'E243' THEN 'Menunggu sinyal input I/O yang ditentukan dalam file grafis.'
    WHEN 'E244' THEN 'Perintah penundaan (delay) dijalankan melalui file grafis.'
    WHEN 'E245' THEN 'Persingkat nama file.'
    WHEN 'E246' THEN 'Angkat sepatu penekan (presser foot) terlebih dahulu dengan menekan tombol “Presser foot”.'
    WHEN 'E247' THEN 'Tekan rangka (frame) terlebih dahulu.'
    WHEN 'E248' THEN 'Tekan rangka penekan tambahan (auxiliary pressure frame) terlebih dahulu.'
    WHEN 'E249' THEN 'Tekan ke bawah semua blok penekan belakang (back pressure blocks).'
    WHEN 'E250' THEN 'Ganti bahan yang akan dilubangi dengan bahan yang baru.'
END
WHERE machine_id = 11
  AND TRIM(code) IN (
    'E001','E002','E003','E004','E005','E006','E007',
    'E205','E206','E207','E208','E209','E210','E211','E212',
    'E213','E214','E215','E216','E217','E218','E219','E220',
    'E221','E222','E223','E224','E225','E226','E227','E228',
    'E229','E230','E231','E232','E233','E234','E235','E236',
    'E237','E238','E239','E240','E241','E242','E243','E244',
    'E245','E246','E247','E248','E249','E250'
  );

SELECT changes() AS jumlah_baris_yang_diuji;

-- CATATAN KESELAMATAN:
-- E213: Manual menyebut opsi mematikan deteksi benang putus.
-- Jangan nonaktifkan fungsi keselamatan tanpa prosedur resmi dan otorisasi teknisi.
-- E242: Manual menyebut mematikan Work enable input IO dengan parameter 0.
-- Perubahan parameter hanya oleh teknisi berwenang sesuai prosedur resmi.
--
-- Mode pemeriksaan: tampilkan target dan hasil sementara sebelum dibatalkan.
SELECT code, solution
FROM troubleshooting
WHERE machine_id = 11
  AND TRIM(code) IN (
    'E001','E002','E003','E004','E005','E006','E007',
    'E205','E206','E207','E208','E209','E210','E211','E212',
    'E213','E214','E215','E216','E217','E218','E219','E220',
    'E221','E222','E223','E224','E225','E226','E227','E228',
    'E229','E230','E231','E232','E233','E234','E235','E236',
    'E237','E238','E239','E240','E241','E242','E243','E244',
    'E245','E246','E247','E248','E249','E250'
  )
ORDER BY code;

ROLLBACK;
