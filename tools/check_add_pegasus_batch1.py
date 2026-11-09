import sqlite3

DB = "database/garment.db"

TARGETS = [
    (10, "PEGASUS", 2, "Overlock", "M932"),
    (10, "PEGASUS", 2, "Overlock", "M952"),
    (10, "PEGASUS", 12, "Chainstitch", "M922"),
]

con = sqlite3.connect(DB)
cur = con.cursor()

print("=== PEGASUS BATCH 1 ===")
print("MODE   : SAFETY CHECK ONLY")
print("DATABASE: TIDAK DIUBAH")

errors = []

for brand_id, brand_name, type_id, type_name, model in TARGETS:

    brand = cur.execute("""
        SELECT id, name
        FROM brands
        WHERE id=?
    """, (brand_id,)).fetchone()

    if not brand:
        errors.append(
            f"Brand ID {brand_id} tidak ditemukan."
        )
    elif brand[1].upper() != brand_name.upper():
        errors.append(
            f"Brand ID {brand_id} salah: "
            f"DB={brand[1]}, TARGET={brand_name}"
        )

    machine_type = cur.execute("""
        SELECT id, name
        FROM machine_types
        WHERE id=?
    """, (type_id,)).fetchone()

    if not machine_type:
        errors.append(
            f"Machine Type ID {type_id} tidak ditemukan."
        )
    elif machine_type[1].lower() != type_name.lower():
        errors.append(
            f"Machine Type ID {type_id} salah: "
            f"DB={machine_type[1]}, TARGET={type_name}"
        )

    existing = cur.execute("""
        SELECT id, model
        FROM machines
        WHERE brand_id=?
          AND UPPER(model)=UPPER(?)
    """, (brand_id, model)).fetchone()

    if existing:
        errors.append(
            f"Model sudah ada: {model} | machine_id={existing[0]}"
        )

print("\n=== TARGET INSERT ===")

for brand_id, brand_name, type_id, type_name, model in TARGETS:
    print(
        f"PEGASUS | {model} | "
        f"Machine Type: {type_id} - {type_name}"
    )

print("\n=== HASIL SAFETY CHECK ===")

if errors:
    print("STATUS: TIDAK AMAN")
    for error in errors:
        print("-", error)
else:
    print("STATUS: AMAN")
    print("Semua brand, machine type, dan model tervalidasi.")
    print("DATABASE TIDAK DIUBAH.")

con.close()
