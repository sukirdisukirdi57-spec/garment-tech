import sqlite3

db = sqlite3.connect("database/garment.db")
cur = db.cursor()

print("=== STRUKTUR TABEL TROUBLESHOOTING ===")
print(cur.execute("PRAGMA table_info(troubleshooting)").fetchall())

print("\n=== 5 CONTOH TROUBLESHOOTING ===")
print(cur.execute("""
SELECT machine_id, problem, symptoms, possible_cause, solution, safety_notes, source
FROM troubleshooting
LIMIT 5
""").fetchall())

print("\n=== TROUBLESHOOTING MESIN DDL ===")
print(cur.execute("""
SELECT machine_id, problem, source
FROM troubleshooting
WHERE machine_id IN (16, 17, 225)
""").fetchall())

db.close()
print("\nSelesai. Database tidak diubah.")
