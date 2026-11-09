import sqlite3

DB = "database/garment.db"

TARGET = {
    "name": "PEGASUS",
    "country": "Japan",
    "official_website": "https://www.pegasus.co.jp/en/",
    "notes": "Brand mesin jahit industri PEGASUS."
}

con = sqlite3.connect(DB)
cur = con.cursor()

print("=== PEGASUS BRAND INSERT ===")
print("MODE   : SAFETY CHECK ONLY")
print("DATABASE: TIDAK DIUBAH")

errors = []

# 1. Cek schema
columns = [
    row[1]
    for row in cur.execute("PRAGMA table_info(brands)").fetchall()
]

required_columns = {
    "name",
    "country",
    "official_website",
    "notes"
}

missing_columns = required_columns - set(columns)

if missing_columns:
    errors.append(
        "Kolom brands tidak lengkap: "
        + ", ".join(sorted(missing_columns))
    )

# 2. Cek brand berdasarkan nama
existing = cur.execute("""
    SELECT id, name, country, official_website, notes
    FROM brands
    WHERE UPPER(name) = UPPER(?)
""", (TARGET["name"],)).fetchall()

if existing:
    errors.append(
        f"Brand {TARGET['name']} sudah ada di database."
    )

# 3. Tampilkan rencana
print("\n=== TARGET ===")
print("NAME            :", TARGET["name"])
print("COUNTRY         :", TARGET["country"])
print("OFFICIAL WEBSITE:", TARGET["official_website"])
print("NOTES           :", TARGET["notes"])

print("\n=== HASIL SAFETY CHECK ===")

if errors:
    print("STATUS: TIDAK AMAN")
    for error in errors:
        print("-", error)
else:
    print("STATUS: AMAN")
    print("Brand PEGASUS belum ada.")
    print("Schema tabel brands sesuai.")
    print("DATABASE TIDAK DIUBAH.")

con.close()
