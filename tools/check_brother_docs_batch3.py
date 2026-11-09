import sqlite3

DB = "database/garment.db"

TARGETS = [
    (50, "S-7220B", "Manual", "Brother S-7220B Instruction Manual"),
    (50, "S-7220B", "Product Page", "Brother S-7220B Official Product Page"),
    (53, "S-7200A", "Manual", "Brother S-7200A Instruction Manual"),
    (53, "S-7200A", "Product Page", "Brother S-7200A Official Product Page"),
]

con = sqlite3.connect(DB)
cur = con.cursor()

print("=== BROTHER DOCUMENT BATCH 3 ===")
print("MODE   : SAFETY CHECK ONLY")
print("DATABASE: TIDAK DIUBAH")

errors = []

for machine_id, expected_model, doc_type, title in TARGETS:
    row = cur.execute(
        "SELECT id, model FROM machines WHERE id=?",
        (machine_id,)
    ).fetchone()

    if not row:
        errors.append(
            f"ID {machine_id}: MACHINE TIDAK DITEMUKAN"
        )
        continue

    actual_id, actual_model = row

    if actual_model != expected_model:
        errors.append(
            f"ID {machine_id}: MODEL SALAH "
            f"(DB={actual_model}, TARGET={expected_model})"
        )

    dup = cur.execute("""
        SELECT id
        FROM documents
        WHERE machine_id=?
          AND document_type=?
          AND title=?
    """, (machine_id, doc_type, title)).fetchone()

    if dup:
        errors.append(
            f"DUPLIKAT: {machine_id} | {expected_model} | "
            f"{doc_type} | {title} | doc_id={dup[0]}"
        )

print("\n=== HASIL SAFETY CHECK ===")

if errors:
    print("STATUS: TIDAK AMAN")
    for e in errors:
        print("-", e)
else:
    print("STATUS: AMAN")
    print("\nTARGET INSERT:")
    for machine_id, model, doc_type, title in TARGETS:
        print(f"{machine_id} | {model} | {doc_type} | {title}")

con.close()
