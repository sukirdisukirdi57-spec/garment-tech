import sqlite3
db = sqlite3.connect("database/garment.db")
cur = db.cursor()
ids = (16, 17, 225)
for mid in ids:
    print("\nMESIN ID:", mid)
    cur.execute("SELECT model, function, description, notes FROM machines WHERE id=?", (mid,))
    print("DATA:", cur.fetchone())
    cur.execute("SELECT specification, value FROM specifications WHERE machine_id=?", (mid,))
    rows = cur.fetchall()
    print("JUMLAH SPESIFIKASI:", len(rows))
    for row in rows:
        print(row)
db.close()
