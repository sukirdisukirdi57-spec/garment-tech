-- USULAN SAJA: JUKI PS-800-12080, machine_id=11
-- Dibuat dari ps800-error-codes-review.csv
-- Belum dijalankan; periksa dan setujui terlebih dahulu.
-- Hanya menambah kode yang belum ada untuk machine_id=11.
-- Tidak menggunakan UPDATE atau DELETE.

BEGIN TRANSACTION;

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E001 — No reset', 'Panel menampilkan kode E001.', '', 'Click the [Reset] button to reset.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E001'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E001');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E002 — No X zero signal', 'Panel menampilkan kode E002.', '', 'Inspect the X sensor for poor contact or breakage', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E002'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E002');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E003 — No Y zero signal', 'Panel menampilkan kode E003.', '', 'Inspect the Y sensor for poor contact or breakage', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E003'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E003');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E004 — No Z zero signal', 'Panel menampilkan kode E004.', '', 'Inspect the Z sensor for poor contact or breakage', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E004'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E004');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E005 — No U zero signal', 'Panel menampilkan kode E005.', '', 'Inspect the U sensor for poor contact or breakage', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E005'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E005');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E006 — Extended shaft infinite bit signal', 'Panel menampilkan kode E006.', '', 'Inspect the shaft sensor for poor contact or breakage', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E006'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E006');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E007 — No spindle zero signal', 'Panel menampilkan kode E007.', '', 'Check the spindle encoder for breakage', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E007'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E007');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E020 — X axis overpressure', 'Panel menampilkan kode E020.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E020'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E020');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E021 — X axis undervoltage', 'Panel menampilkan kode E021.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E021'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E021');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E022 — X axis hardware overcurrent', 'Panel menampilkan kode E022.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E022'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E022');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E023 — X axis software overcurrent', 'Panel menampilkan kode E023.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E023'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E023');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E024 — X axis encoder failure', 'Panel menampilkan kode E024.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E024'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E024');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E025 — X axis open circuit', 'Panel menampilkan kode E025.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E025'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E025');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E026 — X axis overload', 'Panel menampilkan kode E026.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E026'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E026');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E027 — Position out of the X axis allowable range', 'Panel menampilkan kode E027.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E027'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E027');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E028 — X axis AD sampling failed', 'Panel menampilkan kode E028.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E028'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E028');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E029 — X axis overheat', 'Panel menampilkan kode E029.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E029'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E029');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E030 — Y axis overpressure', 'Panel menampilkan kode E030.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E030'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E030');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E031 — Y axis undervoltage', 'Panel menampilkan kode E031.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E031'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E031');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E032 — Y axis hardware overcurrent', 'Panel menampilkan kode E032.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E032'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E032');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E033 — Y axis software overcurrent', 'Panel menampilkan kode E033.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E033'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E033');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E034 — Y axis encoder failure', 'Panel menampilkan kode E034.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E034'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E034');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E035 — Y axis open circuit', 'Panel menampilkan kode E035.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E035'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E035');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E036 — Y axis overload', 'Panel menampilkan kode E036.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E036'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E036');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E037 — Position out of the Y axis allowable range', 'Panel menampilkan kode E037.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E037'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E037');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E038 — Y axis AD sampling failed', 'Panel menampilkan kode E038.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E038'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E038');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E039 — Y axis overheat', 'Panel menampilkan kode E039.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E039'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E039');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E040 — Z axis overpressure', 'Panel menampilkan kode E040.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E040'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E040');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E041 — Z axis undervoltage', 'Panel menampilkan kode E041.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E041'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E041');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E042 — Z axis hardware overcurrent', 'Panel menampilkan kode E042.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E042'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E042');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E043 — Z axis software overcurrent', 'Panel menampilkan kode E043.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E043'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E043');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E044 — Z axis encoder failure', 'Panel menampilkan kode E044.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E044'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E044');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E045 — Z axis open circuit', 'Panel menampilkan kode E045.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E045'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E045');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E046 — Z axis overload', 'Panel menampilkan kode E046.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E046'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E046');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E047 — Position out of the Z axis allowable range', 'Panel menampilkan kode E047.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E047'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E047');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E048 — Z axis AD sampling failed', 'Panel menampilkan kode E048.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E048'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E048');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E049 — Z axis overheat', 'Panel menampilkan kode E049.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E049'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E049');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E050 — Thread trimming shaft overpressure', 'Panel menampilkan kode E050.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E050'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E050');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E051 — Thread trimming shaft undervoltage', 'Panel menampilkan kode E051.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E051'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E051');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E052 — Thread trimming shaft hardware overcurrent', 'Panel menampilkan kode E052.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E052'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E052');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E053 — Thread trimming shaft software overcurrent', 'Panel menampilkan kode E053.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E053'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E053');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E054 — Thread trimming shaft encoder failure', 'Panel menampilkan kode E054.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E054'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E054');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E055 — Thread trimming shaft open circuit', 'Panel menampilkan kode E055.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E055'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E055');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E056 — Thread trimmer overload', 'Panel menampilkan kode E056.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E056'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E056');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E057 — Position out of the thread trimming shaft allowable range', 'Panel menampilkan kode E057.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E057'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E057');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E058 — Thread trimmer AD sampling failed', 'Panel menampilkan kode E058.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E058'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E058');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E059 — Thread trimming shaft overheat', 'Panel menampilkan kode E059.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E059'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E059');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E060 — Spindle overpressure', 'Panel menampilkan kode E060.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E060'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E060');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E061 — Spindle undervoltage', 'Panel menampilkan kode E061.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E061'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E061');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E062 — Spindle hardware overcurrent', 'Panel menampilkan kode E062.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E062'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E062');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E063 — Spindle software overcurrent', 'Panel menampilkan kode E063.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E063'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E063');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E064 — Spindle encoder failure', 'Panel menampilkan kode E064.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E064'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E064');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E065 — Spindle cannot rotate', 'Panel menampilkan kode E065.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E065'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E065');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E066 — Spindle rotation fault detected', 'Panel menampilkan kode E066.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E066'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E066');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E067 — Y servo hardware protection', 'Panel menampilkan kode E067.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E067'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E067');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E068 — Y servo HOC', 'Panel menampilkan kode E068.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E068'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E068');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E069 — Y servo AD module initial calibration fault', 'Panel menampilkan kode E069.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E069'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E069');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E070 — Y servo parameter storage exception', 'Panel menampilkan kode E070.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E070'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E070');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E071 — Y servo system parameter fault', 'Panel menampilkan kode E071.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E071'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E071');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E072 — Y servo AD sampling module failure', 'Panel menampilkan kode E072.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E072'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E072');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E073 — Y servo encoder disconnection', 'Panel menampilkan kode E073.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E073'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E073');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E074 — Y servo encoder AB interference', 'Panel menampilkan kode E074.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E074'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E074');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E075 — Y servo encoder Z interference', 'Panel menampilkan kode E075.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E075'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E075');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E076 — Y servo bus undervoltage', 'Panel menampilkan kode E076.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E076'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E076');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E077 — Y servo bus overvoltage', 'Panel menampilkan kode E077.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E077'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E077');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E078 — Y servo software overcurrent', 'Panel menampilkan kode E078.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E078'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E078');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E079 — Y servo motor overload', 'Panel menampilkan kode E079.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E079'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E079');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E080 — Y servo drive overload', 'Panel menampilkan kode E080.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E080'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E080');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E081 — Y servo motor overheat', 'Panel menampilkan kode E081.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E081'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E081');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E082 — Y servo drive overheat', 'Panel menampilkan kode E082.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E082'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E082');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E083 — Y servo fan fault', 'Panel menampilkan kode E083.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E083'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E083');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E084 — Y servo overspeed', 'Panel menampilkan kode E084.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E084'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E084');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E085 — Position out of the Y servo allowable range', 'Panel menampilkan kode E085.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E085'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E085');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E086 — Y servo bus voltage phase loss', 'Panel menampilkan kode E086.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E086'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E086');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E087 — Y servo motor phase sequence error', 'Panel menampilkan kode E087.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E087'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E087');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E088 — Y servo driver rated current input error', 'Panel menampilkan kode E088.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E088'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E088');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E089 — Y servo brake resistor overload', 'Panel menampilkan kode E089.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E089'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E089');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E090 — Y servo absolute encoder overheat', 'Panel menampilkan kode E090.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E090'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E090');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E091 — Y servo battery voltage is low', 'Panel menampilkan kode E091.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E091'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E091');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E092 — Y servo position information has been lost', 'Panel menampilkan kode E092.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E092'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E092');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E093 — Y servo drive does not match the motor', 'Panel menampilkan kode E093.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E093'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E093');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E094 — Y servo origin retrieval has failed', 'Panel menampilkan kode E094.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E094'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E094');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E095 — Y servo main power supply failure', 'Panel menampilkan kode E095.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E095'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E095');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E096 — Learning of the Y servo offset angle has failed', 'Panel menampilkan kode E096.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E096'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E096');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E097 — Y servo power OFF restart', 'Panel menampilkan kode E097.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E097'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E097');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E098 — Y servo initialization LAN9252 error', 'Panel menampilkan kode E098.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E098'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E098');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E099 — Communication between the Y servo DSP and ESC is interrupted', 'Panel menampilkan kode E099.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E099'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E099');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E100 — Communication between the Y servo net- work cable and host is interrupted', 'Panel menampilkan kode E100.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E100'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E100');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E101 — Exclusive for reading the Y servo PDO com- munication parameter', 'Panel menampilkan kode E101.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E101'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E101');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E102 — Y servo PDO communication has no index', 'Panel menampilkan kode E102.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E102'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E102');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E103 — Y servo PDO communication synchroniza- tion time is out of range', 'Panel menampilkan kode E103.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E103'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E103');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E104 — Y servo PDO communication data is out of range', 'Panel menampilkan kode E104.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E104'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E104');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E105 — Y servo UVW short circuit', 'Panel menampilkan kode E105.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E105'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E105');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E106 — Y servo inertia identification has failed', 'Panel menampilkan kode E106.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E106'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E106');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E107 — Y servo encoder EEPROM reading / writing has failed', 'Panel menampilkan kode E107.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E107'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E107');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E108 — Y servo positive position limit', 'Panel menampilkan kode E108.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E108'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E108');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E109 — Y servo position negative limit', 'Panel menampilkan kode E109.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E109'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E109');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E110 — Y servo electronic gear ratio range', 'Panel menampilkan kode E110.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E110'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E110');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E111 — Y servo input pulse frequency is too high', 'Panel menampilkan kode E111.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E111'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E111');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E200 — XY drive alarm', 'Panel menampilkan kode E200.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E200'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E200');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E201 — X drive alarm', 'Panel menampilkan kode E201.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E201'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E201');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E202 — Y drive alarm', 'Panel menampilkan kode E202.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E202'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E202');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E203 — Spindle returns to the initial position', 'Panel menampilkan kode E203.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E203'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E203');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E204 — Main motor direction is wrong', 'Panel menampilkan kode E204.', '', 'Solusi tidak dicantumkan dalam tabel kode error manual.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E204'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E204');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E205 — Pressure frame fails to come down', 'Panel menampilkan kode E205.', '', 'Click the "Press the frame" button to place the frame.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E205'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E205');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E206 — Head board failure', 'Panel menampilkan kode E206.', '', 'The head plate has broken. It is necessary to change the broken head plate with a new one.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E206'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E206');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E207 — Input I/O timeout error', 'Panel menampilkan kode E207.', '', 'Check whether the input IO has "high" or "low" of the input signal.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E207'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E207');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E208 — Insufficient air pressure', 'Panel menampilkan kode E208.', '', 'Check whether the air supply unit supplies air normally.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E208'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E208');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E209 — Clipper motor is not at the correct position', 'Panel menampilkan kode E209.', '', 'Check whether the zero signal of the clipper motor is normal.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E209'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E209');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E210 — Presser motor is not at the correct position', 'Panel menampilkan kode E210.', '', 'Check that the zero signal of the presser foot motor is normal.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E210'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E210');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E211 — Wire grab motor is not at the correct position', 'Panel menampilkan kode E211.', '', 'Check whether the zero line signal of the wire grab motor is normal.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E211'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E211');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E212 — Cutter is not at the correct position', 'Panel menampilkan kode E212.', '', 'Check whether the zero signal of the cutter motor is nor- mal.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E212'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E212');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E213 — Wire breaks', 'Panel menampilkan kode E213.', '', 'Execute the thread again or turn OFF the wire break detection function before proceeding the operation.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E213'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E213');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E214 — Number of jobs is too many', 'Panel menampilkan kode E214.', '', 'Counted value on the counter has reached the total number you have set. The total number on the counter is cleared and the counter re-starts counting by re-starting the operation.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E214'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E214');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E215 — Bottom line has been already used up', 'Panel menampilkan kode E215.', '', 'It is necessary to change the bobbin thread hook.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E215'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E215');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E216 — File size is too large', 'Panel menampilkan kode E216.', '', 'The number of pins in the graphics file has exceeded the maximum range. The current graphics file must be changed with a new one.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E216'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E216');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E217 — Work file is not found', 'Panel menampilkan kode E217.', '', 'It is necessary to re-scan or change over the graphics file.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E217'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E217');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E218 — Waiting for the work data', 'Panel menampilkan kode E218.', '', 'Queuing time for processing graphic data differs with the size of graphic', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E218'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E218');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E219 — Electrical failure. Contact the manufacturer.', 'Panel menampilkan kode E219.', '', 'Contact the manufacturer of the equipment', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E219'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E219');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E220 — Wrong upgrade file', 'Panel menampilkan kode E220.', '', 'It is necessary to replace the upgrade file with the new upgrade file.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E220'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E220');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E221 — Error has occurred during upgrading of the file type', 'Panel menampilkan kode E221.', '', 'It is necessary to select the correct type of upgrade file for the file to be upgraded', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E221'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E221');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E222 — Not yet upgraded', 'Panel menampilkan kode E222.', '', 'Contact the manufacturer of the equipment', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E222'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E222');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E223 — It is not an upgrade file made by the same OEM', 'Panel menampilkan kode E223.', '', 'Contact the manufacturer of the equipment', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E223'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E223');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E224 — Cannot be connected to the head board', 'Panel menampilkan kode E224.', '', 'Inspect the head board for poor contact of the head board connection line and / or breakage of the desk head plate', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E224'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E224');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E225 — Connect to the main board', 'Panel menampilkan kode E225.', '', 'If the mother board for the display or the electric cord has broken though the screen line connection is neither poor nor broken, check that replacement of the broken part is necessary.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E225'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E225');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E226 — The current file is not valid', 'Panel menampilkan kode E226.', '', 'It is necessary to change the graphics file if the graphical file has broken or the file is not intended to be used with this system type.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E226'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E226');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E227 — File transfer has failed', 'Panel menampilkan kode E227.', '', 'If the mother board for the display or the electric cord has broken though the screen line connection is neither poor nor broken, check that replacement of the broken part is necessary.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E227'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E227');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E228 — Data out of range', 'Panel menampilkan kode E228.', '', 'Check whether the current graphics file data is defective exceeding the ignorable range.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E228'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E228');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E229 — This adjustment angle is too large', 'Panel menampilkan kode E229.', '', 'Corrected graphic angle is too large. Decrease the changed angle value.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E229'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E229');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E230 — Reading of graphics', 'Panel menampilkan kode E230.', '', 'Process the necessary graphic data. Then, wait for a while before starting operation.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E230'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E230');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E231 — Presser foot error', 'Panel menampilkan kode E231.', '', 'Check whether the presser foot motor is normal.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E231'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E231');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E232 — U disk has not been detected', 'Panel menampilkan kode E232.', '', 'Re-insert the U disk or replace the U disk with a new one.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E232'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E232');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E233 — File reading / writing error', 'Panel menampilkan kode E233.', '', '① Replace the graphics file with a different one. ② Re-insert the U disk or replace the U disk with a new one.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E233'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E233');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E234 — Graphics out of range or head offset', 'Panel menampilkan kode E234.', '', '① Reset the position of reference point. ② Reset the offset value of the head 2 or head 3. ③ Replace the small-width graphic with the normal-width graphic.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E234'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E234');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E235 — This file is not a file to be processed', 'Panel menampilkan kode E235.', '', 'Replace the graphics file with a different one.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E235'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E235');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E236 — Ferroelectric damage', 'Panel menampilkan kode E236.', '', 'Contact the manufacturer of the equipment', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E236'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E236');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E237 — Set an administration password', 'Panel menampilkan kode E237.', '', 'Firstly, set the administration password.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E237'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E237');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E238 — Edit is not supported', 'Panel menampilkan kode E238.', '', 'Command or file that is not required to be edited', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E238'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E238');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E239 — Contact the manufacturer', 'Panel menampilkan kode E239.', '', 'Contact the manufacturer of the equipment', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E239'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E239');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E240 — Communication fault 2', 'Panel menampilkan kode E240.', '', 'CAN communication error has occurred, or the motherboard program is old one.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E240'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E240');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E241 — At the time of fault', 'Panel menampilkan kode E241.', '', '① Time has been modified illegally. ② Motherboard battery voltage is low.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E241'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E241');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E242 — No job IO', 'Panel menampilkan kode E242.', '', '① Work enable input IO signal is abnormal. ② Shut down the "Work enable input IO" function. Set the parameter value to 0 (zero).', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E242'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E242');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E243 — Input waiting IO', 'Panel menampilkan kode E243.', '', 'Waiting for the input IO signal in the graphics file.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E243'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E243');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E244 — Delay is executed', 'Panel menampilkan kode E244.', '', 'Delay command is executed with the graphics file.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E244'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E244');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E245 — File name is too long', 'Panel menampilkan kode E245.', '', 'It is necessary to shorten the file name.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E245'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E245');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E246 — Lift the presser foot in advance', 'Panel menampilkan kode E246.', '', 'It is necessary to lift the presser foot by clicking the "Presser foot" button.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E246'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E246');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E247 — Frame is not pressed', 'Panel menampilkan kode E247.', '', 'It is necessary to press the frame in advance.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E247'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E247');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E248 — Auxiliary pressure frame is not pressed', 'Panel menampilkan kode E248.', '', 'It is necessary to firstly press the auxiliary pressure frame.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E248'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E248');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E249 — Pressure frame and auxiliary pressure frame are not pressed', 'Panel menampilkan kode E249.', '', 'It is necessary to push down all of the back pressure blocks.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E249'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E249');

INSERT INTO troubleshooting
(machine_id, problem, symptoms, possible_cause, solution, safety_notes, source, code)
SELECT 11, 'Kode error E250 — Punched bottom material has run out', 'Panel menampilkan kode E250.', '', 'It is necessary to replace the material to be punched with a new one.', 'Ikuti prosedur keselamatan mesin. Pemeriksaan listrik, servo, dan komponen internal dilakukan teknisi kompeten.', 'JUKI PS-800-12080 Instruction Manual, bagian 4-26, List of error codes, halaman 46-50.', 'E250'
WHERE NOT EXISTS (SELECT 1 FROM troubleshooting WHERE machine_id = 11 AND TRIM(code) = 'E250');

-- COMMIT sengaja belum ditambahkan.
-- Tinjau isi file sebelum memutuskan menjalankan SQL.
