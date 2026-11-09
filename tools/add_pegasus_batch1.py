import sqlite3

DB = "database/garment.db"

TARGETS = [
    (10, "PEGASUS", 2, "Overlock", "M932",
     "Pegasus M932 industrial overlock machine."),
    (10, "PEGASUS", 2, "Overlock", "M952",
     "Pegasus M952 industrial overlock machine."),
    (10, "PEGASUS", 12, "Chainstitch", "M922",
     "Pegasus M922 industrial chainstitch machine."),
]

con = sqlite3.connect(DB)
cur = con.cursor()

try:
    print("=== PEGASUS BATCH 1 ===")
    print("TARGET : 3 mesin")
    print("MODE   : SAFETY CHECK + TRANSACTION")

    # 1. Validasi brand + machine type + model
    for brand_id, brand_name, type_id, type_name, model, description in TARGETS:

        brand = cur.execute("""
            SELECT id, name
            FROM brands
            WHERE id=?
        """, (brand_id,)).fetchone()

        if not brand or brand[1].upper() != brand_name.upper():
            raise RuntimeError(
                f"Brand tidak valid: {brand_id} | {brand_name}"
            )

        machine_type = cur.execute("""
            SELECT id, name
            FROM machine_types
            WHERE id=?
        """, (type_id,)).fetchone()

        if not machine_type or machine_type[1].lower() != type_name.lower():
            raise RuntimeError(
                f"Machine type tidak valid: "
                f"{type_id} | {type_name}"
            )

        existing = cur.execute("""
            SELECT id
            FROM machines
            WHERE brand_id=?
              AND UPPER(model)=UPPER(?)
        """, (brand_id, model)).fetchone()

        if existing:
            raise RuntimeError(
                f"Model sudah ada: {model} | ID={existing[0]}"
            )

    print("1. VALIDASI         : OK")

    print("\n=== RENCANA INSERT ===")
    for brand_id, brand_name, type_id, type_name, model, description in TARGETS:
        print(
            f"{brand_name} | {model} | "
            f"{type_name} | {description}"
        )

    print("\n2. RENCANA INSERT    : OK")

    con.execute("BEGIN")

    inserted_ids = []

    for brand_id, brand_name, type_id, type_name, model, description in TARGETS:
        cur.execute("""
            INSERT INTO machines
            (brand_id, machine_type_id, model, function, description, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            brand_id,
            type_id,
            model,
            type_name,
            description,
            "Sumber resmi PEGASUS."
        ))

        inserted_ids.append(cur.lastrowid)

    # 3. Verifikasi sebelum commit
    for machine_id in inserted_ids:
        row = cur.execute("""
            SELECT id, brand_id, machine_type_id, model
            FROM machines
            WHERE id=?
        """, (machine_id,)).fetchone()

        if not row:
            raise RuntimeError(
                f"Verifikasi gagal untuk machine ID {machine_id}"
            )

    print("3. VERIFIKASI        : OK")

    con.commit()

    print("\n=== HASIL ===")
    print(f"INSERT BERHASIL : {len(inserted_ids)}")
    print("COMMIT          : OK")
    print("DATABASE        : PEGASUS BATCH 1 DITAMBAHKAN")

except Exception as e:
    con.rollback()
    print("\n=== ERROR ===")
    print("ROLLBACK        : OK")
    print("DATABASE        : TIDAK BERUBAH")
    print("ERROR           :", e)

finally:
    con.close()
