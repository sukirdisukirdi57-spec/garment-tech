import sqlite3

DB = "database/garment.db"

TARGETS = [
    (79, "S-7180A", "Manual", "Brother S-7180A Instruction Manual"),
    (108, "BE-438DP", "Manual", "Brother BE-438DP Instruction Manual"),
    (108, "BE-438DP", "Parts List", "Brother BE-438DP Parts Book"),
]

con = sqlite3.connect(DB)
cur = con.cursor()

print("=== BROTHER DOCUMENT BATCH 4 ===")
print("MODE   : SAFETY CHECK ONLY")
print("DATABASE: TIDAK DIUBAH")

errors = []

for machine_id, expected_model, doc_type, title in TARGETS:
    row = cur.execute(
        "SELECT id, model FROM machines WHERE id=?",
        (machine_id,)
    ).fetchone()

    if not row:
        errors.append(f"ID {machine_id}: MACHINE TIDAK DITEMUKAN")
        continue

    if row[1] != expected_model:
        errors.append(
            f"ID {machine_id}: MODEL SALAH "
            f"(DB={row[1]}, TARGET={expected_model})"
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
