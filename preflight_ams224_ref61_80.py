import sqlite3

DB = "database/garment.db"

TARGETS = {
    "400-51501": "TAPE",
    "400-40230": "INT PCB ASM",
    "SL-4040891-SC": "SCREW M4 L=8",
    "HX-0033900-00": "STUD",
    "SM-1040870-TP": "SCREW",
    "SL-9061600-SF": "SCREW",
    "PS-0150065-KP": "SPRING PIN 1.5X6",
    "400-72193": "X_FEED_UPPER_COVER_L_ASM_4530",
    "400-72186": "X_FEED_LOWER_COVER_L_ASM_4530",
    "SM-6041402-TN": "SCREW M4X0.7 L=14",
    "SM-7030450-SC": "SCREW M3X0.5 L=4",
    "SM-6050802-TP": "SCREW M5X0.8 L=8",
    "WP-0520656-SA": "WASHER 5.2X9.5X0.6",
    "G6113-875-00A": "CLOTH PRESSER SPONGE A",
    "TA-2100904-R0": "RUBBER PLUG",
    "SM-1041601-SC": "SCREW M4X0.7 L=16",
    "122-09706": "COLLAR",
    "SL-4041091-SC": "SCREW M4 L=10",
    "400-72214": "FEED COVER STOPPER",
    "400-72213": "OIL_PAN_GASKET",
}

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    columns = {
        row["name"]
        for row in con.execute("PRAGMA table_info(parts)")
    }

    number_col = next(
        (c for c in ("part_number", "parts_number") if c in columns),
        None
    )

    if not number_col:
        raise RuntimeError("Kolom nomor part tidak ditemukan.")

    print("=== PREFLIGHT REF 61-80 ===")
    print("Database:", DB)
    print("Kolom nomor part:", number_col)

    missing = []
    multiple = []

    for number, description in TARGETS.items():
        rows = con.execute(
            f'SELECT * FROM parts WHERE "{number_col}" = ?',
            (number,)
        ).fetchall()

        if not rows:
            missing.append(number)
            print(f"MISSING | {number} | {description}")
            continue

        if len(rows) > 1:
            multiple.append(number)

        for row in rows:
            print(
                f"FOUND | ID {row['id']} | "
                f"{number} | {description}"
            )

        if len(rows) > 1:
            print(f"WARNING: nomor part ditemukan {len(rows)} kali")

    print("\n=== OCCURRENCE REF 61-80 ===")

    existing = con.execute("""
        SELECT catalog_ref, part_number, part_name, quantity_raw
        FROM catalog_occurrences
        WHERE machine_id = 46
          AND source_document_id = 162
          AND pdf_page = 11
          AND CAST(catalog_ref AS INTEGER) BETWEEN 61 AND 80
        ORDER BY CAST(catalog_ref AS INTEGER)
    """).fetchall()

    for row in existing:
        print(dict(row))

    if not existing:
        print("Belum ada occurrence REF 61-80.")

    print("\n=== RINGKASAN ===")
    print("Jumlah target :", len(TARGETS))
    print("Missing       :", len(missing), missing)
    print("Nomor ganda   :", len(multiple), multiple)
    print("Occurrence    :", len(existing))

finally:
    con.close()
