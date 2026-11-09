import sqlite3

db = sqlite3.connect("database/garment.db")
db.row_factory = sqlite3.Row

print("=== STRUKTUR TROUBLESHOOTING ===")
for r in db.execute("PRAGMA table_info(troubleshooting)"):
    print(r["name"], "|", r["type"], "| NOT NULL:", r["notnull"])

print("\n=== IDENTITAS MESIN UAM-04 ===")
for r in db.execute("""
SELECT m.id, b.name AS brand, m.model
FROM machines m
JOIN brands b ON b.id = m.brand_id
WHERE UPPER(b.name) = 'MAICA'
AND UPPER(m.model) = 'UAM-04'
"""):
    print(dict(r))

print("\n=== DATA ALARM UAM-04 SAAT INI ===")
for r in db.execute("""
SELECT t.id, t.problem, t.code, t.source
FROM troubleshooting t
JOIN machines m ON m.id = t.machine_id
JOIN brands b ON b.id = m.brand_id
WHERE UPPER(b.name) = 'MAICA'
AND UPPER(m.model) = 'UAM-04'
ORDER BY t.id
"""):
    print(dict(r))

print("\n=== KODE YANG SUDAH DIGUNAKAN MAICA ===")
for r in db.execute("""
SELECT t.code, m.model, COUNT(*) AS jumlah
FROM troubleshooting t
JOIN machines m ON m.id = t.machine_id
JOIN brands b ON b.id = m.brand_id
WHERE UPPER(b.name) = 'MAICA'
AND t.code IS NOT NULL
AND TRIM(t.code) != ''
GROUP BY t.code, m.model
ORDER BY m.model, t.code
"""):
    print(dict(r))

print("\nIntegritas:", db.execute(
    "PRAGMA integrity_check"
).fetchone()[0])

db.close()
