import sqlite3
import sys

DB = "database/garment.db"

TARGETS = {
    108: {
        "model": "BE-438DP",
        "need": ["Catalog"],
    },
    111: {
        "model": "KE-430DP",
        "need": ["Manual", "Parts List"],
    },
    113: {
        "model": "BAS-311HX",
        "need": ["Manual", "Parts List"],
    },
    114: {
        "model": "BAS-326HX",
        "need": ["Manual", "Parts List"],
    },
}

con = sqlite3.connect(DB)
cur = con.cursor()

print("=== BROTHER DOCUMENT SAFETY CHECK ===")
print("MODE: READ ONLY — TIDAK ADA INSERT / UPDATE / DELETE\n")

errors = 0

for machine_id, target in TARGETS.items():
    row = cur.execute(
        "SELECT id, model FROM machines WHERE id=?",
        (machine_id,)
    ).fetchone()

    if not row:
        print(f"ERROR: ID {machine_id} tidak ditemukan")
        errors += 1
        continue

    db_id, db_model = row

    if db_model != target["model"]:
        print(
            f"ERROR: ID {machine_id} model database = {db_model}, "
            f"seharusnya = {target['model']}"
        )
        errors += 1
        continue

    print(f"--- {machine_id} | {db_model} ---")

    docs = cur.execute("""
        SELECT id, document_type, title
        FROM documents
        WHERE machine_id=?
        ORDER BY id
    """, (machine_id,)).fetchall()

    existing_types = [d[1] for d in docs]

    for doc_id, doc_type, title in docs:
        print(f"  ADA     : {doc_id} | {doc_type} | {title}")

    for needed in target["need"]:
        count = existing_types.count(needed)

        if count == 0:
            print(f"  KURANG  : {needed}")
        elif count == 1:
            print(f"  SUDAH   : {needed} — aman, tidak perlu INSERT")
        else:
            print(
                f"  WARNING : {needed} sudah {count} record "
                f"(potensi duplikat)"
            )
            errors += 1

    print()

con.close()

print("=== HASIL ===")

if errors == 0:
    print("SAFETY CHECK: AMAN")
    print("Tidak ditemukan ID/model salah atau duplikat pada target.")
    print("Database TIDAK diubah.")
else:
    print(f"SAFETY CHECK: CEK ULANG — {errors} masalah ditemukan.")
    print("Database TIDAK diubah.")
    sys.exit(1)
