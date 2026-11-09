import sqlite3

DB = "database/garment.db"

TARGET = (
    "PEGASUS",
    "Japan",
    "https://www.pegasus.co.jp/en/",
    "Brand mesin jahit industri PEGASUS."
)

con = sqlite3.connect(DB)
cur = con.cursor()

try:
    print("=== PEGASUS BRAND INSERT ===")
    print("MODE : SAFETY CHECK + TRANSACTION")

    # 1. Cek ulang sebelum transaction
    existing = cur.execute("""
        SELECT id, name
        FROM brands
        WHERE UPPER(name) = UPPER(?)
    """, (TARGET[0],)).fetchone()

    if existing:
        raise RuntimeError(
            f"Brand PEGASUS sudah ada: ID={existing[0]}"
        )

    print("1. DUPLIKAT : TIDAK ADA")

    print("\n=== RENCANA INSERT ===")
    print("NAME            :", TARGET[0])
    print("COUNTRY         :", TARGET[1])
    print("OFFICIAL WEBSITE:", TARGET[2])
    print("NOTES           :", TARGET[3])

    con.execute("BEGIN")

    cur.execute("""
        INSERT INTO brands
        (name, country, official_website, notes)
        VALUES (?, ?, ?, ?)
    """, TARGET)

    brand_id = cur.lastrowid

    # 2. Verifikasi sebelum commit
    row = cur.execute("""
        SELECT id, name, country, official_website, notes
        FROM brands
        WHERE id=?
    """, (brand_id,)).fetchone()

    if not row:
        raise RuntimeError("Verifikasi INSERT gagal.")

    if row[1] != "PEGASUS":
        raise RuntimeError(
            f"Verifikasi model brand gagal: {row}"
        )

    print("\n2. VERIFIKASI : OK")
    print("BRAND ID     :", brand_id)

    con.commit()

    print("\n=== HASIL ===")
    print("INSERT BERHASIL : 1")
    print("COMMIT          : OK")
    print("DATABASE        : PEGASUS DITAMBAHKAN")

except Exception as e:
    con.rollback()
    print("\n=== ERROR ===")
    print("ROLLBACK        : OK")
    print("DATABASE        : TIDAK BERUBAH")
    print("ERROR           :", e)

finally:
    con.close()
