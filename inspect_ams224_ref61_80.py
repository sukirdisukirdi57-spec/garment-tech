import sqlite3

DB = "database/garment.db"

TARGETS = [
    "400-51501",
    "400-40230",
    "SL-4040891-SC",
    "HX-0033900-00",
    "SM-1040870-TP",
    "SL-9061600-SF",
    "PS-0150065-KP",
    "400-72193",
    "400-72186",
    "SM-6041402-TN",
    "SM-7030450-SC",
    "SM-6050802-TP",
    "WP-0520656-SA",
    "G6113-875-00A",
    "TA-2100904-R0",
    "SM-1041601-SC",
    "122-09706",
    "SL-4041091-SC",
    "400-72214",
    "400-72213",
]

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    columns = [
        row["name"]
        for row in con.execute("PRAGMA table_info(parts)")
    ]

    print("=== STRUKTUR TABEL PARTS ===")
    print(columns)

    preferred = [
        "id",
        "machine_id",
        "part_number",
        "part_name",
        "description",
        "catalog_ref",
        "diagram_page",
        "notes",
    ]

    fields = [c for c in preferred if c in columns]

    print("\n=== DETAIL PART BERDASARKAN NOMOR ===")

    for number in TARGETS:
        rows = con.execute("""
            SELECT *
            FROM parts
            WHERE part_number = ?
            ORDER BY id
        """, (number,)).fetchall()

        print(f"\n--- {number} | {len(rows)} record ---")

        for row in rows:
            print({
                field: row[field]
                for field in fields
            })

    print("\n=== IDENTITAS MESIN 46 ===")

    machine_columns = [
        row["name"]
        for row in con.execute("PRAGMA table_info(machines)")
    ]

    print("Kolom machines:", machine_columns)

    machine = con.execute(
        "SELECT * FROM machines WHERE id = 46"
    ).fetchone()

    if machine:
        print(dict(machine))
    else:
        print("Machine ID 46 tidak ditemukan.")

finally:
    con.close()
