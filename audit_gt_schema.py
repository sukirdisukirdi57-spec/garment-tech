import sqlite3

db = sqlite3.connect("database/garment.db")

for table in ["machines", "parts", "components", "component_parts", "documents"]:
print("\n===== " + table + " =====")
columns = db.execute("PRAGMA table_info(" + table + ")").fetchall()
print("Kolom:", [(c[1], c[2]) for c in columns])
total = db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
print("Jumlah baris:", total)

db.close()
