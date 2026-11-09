import sqlite3

DB = "database/garment.db"

machines = [
    ("WT169P", 14, "Interlock"),
    ("W264P", 14, "Interlock"),
    ("FS703P", 15, "Flatseamer"),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    # Safety check
    brand = cur.execute(
        "SELECT id FROM brands WHERE name = 'PEGASUS'"
    ).fetchone()

    if not brand:
        raise RuntimeError("Brand PEGASUS tidak ditemukan")

    brand_id = brand[0]

    for model, type_id, type_name in machines:
        type_row = cur.execute(
            "SELECT id FROM machine_types WHERE id = ? AND name = ?",
            (type_id, type_name)
        ).fetchone()

        if not type_row:
            raise RuntimeError(
                f"Machine type tidak cocok: {type_id} {type_name}"
            )

        exists = cur.execute("""
            SELECT id FROM machines
            WHERE brand_id = ? AND model = ?
        """, (brand_id, model)).fetchone()

        if exists:
            raise RuntimeError(
                f"Model sudah ada: {model} (ID {exists[0]})"
            )

    # Transaction
    for model, type_id, type_name in machines:
        cur.execute("""
            INSERT INTO machines
            (brand_id, machine_type_id, model, function, description, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            brand_id,
            type_id,
            model,
            None,
            f"Mesin jahit industri PEGASUS {model}.",
            "Ditambahkan melalui PEGASUS Batch 3."
        ))

    conn.commit()

    print("INSERT BERHASIL :", len(machines))
    print("COMMIT : OK")

    for model, _, _ in machines:
        row = cur.execute("""
            SELECT id, model, machine_type_id
            FROM machines
            WHERE brand_id = ? AND model = ?
        """, (brand_id, model)).fetchone()
        print(f"{row[1]} | ID {row[0]} | machine_type_id {row[2]}")

except Exception as e:
    conn.rollback()
    print("ROLLBACK : OK")
    print("ERROR :", e)

finally:
    conn.close()
