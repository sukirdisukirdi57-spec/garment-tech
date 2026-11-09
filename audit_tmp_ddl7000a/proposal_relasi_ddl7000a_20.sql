-- PROPOSAL SAJA: belum dijalankan.
-- Target: DDL-7000A machine_id=4.
-- Relasi baru menggunakan pola existing: sub-part, notes NULL.
-- Periksa kembali sebelum menyetujui impor.

INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 282, 1280, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=282 AND part_id=1280);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 283, 1304, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=283 AND part_id=1304);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 284, 1313, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=284 AND part_id=1313);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 285, 1333, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=285 AND part_id=1333);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 286, 1351, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=286 AND part_id=1351);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 287, 1358, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=287 AND part_id=1358);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 288, 1367, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=288 AND part_id=1367);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 289, 1371, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=289 AND part_id=1371);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 290, 1450, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=290 AND part_id=1450);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 291, 1465, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=291 AND part_id=1465);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 292, 1509, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=292 AND part_id=1509);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 293, 1516, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=293 AND part_id=1516);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 294, 1552, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=294 AND part_id=1552);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 295, 1555, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=295 AND part_id=1555);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 296, 1564, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=296 AND part_id=1564);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 297, 1585, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=297 AND part_id=1585);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 298, 1592, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=298 AND part_id=1592);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 299, 1604, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=299 AND part_id=1604);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 300, 1618, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=300 AND part_id=1618);
INSERT INTO component_parts (component_id, part_id, relation_type, notes) SELECT 301, 1703, 'sub-part', NULL WHERE NOT EXISTS (SELECT 1 FROM component_parts WHERE component_id=301 AND part_id=1703);
