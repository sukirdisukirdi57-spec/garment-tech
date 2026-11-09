import sqlite3

DB = "database/garment.db"

models = ["WX664P", "W3562P", "W3664P"]

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=== SAFETY CHECK PEGASUS BATCH 2 DOCUMENTS ===")

for model in models:
    row = cur.execute("""
        SELECT m.id, m.model, b.name, mt.name
        FROM machines m
        JOIN brands b ON b.id = m.brand_id
        LEFT JOIN machine_types mt ON mt.id = m.machine_type_id
        WHERE b.name = 'PEGASUS' AND m.model = ?
    """, (model,)).fetchone()

    if not row:
        print(f"[ERROR] {model}: MACHINE TIDAK DITEMUKAN")
        continue

    machine_id, machine_model, brand, machine_type = row

    docs = cur.execute("""
        SELECT document_type, title, source_url
        FROM documents
        WHERE machine_id = ?
        ORDER BY document_type
    """, (machine_id,)).fetchall()

    print(f"\n{model} | ID {machine_id} | {machine_type}")
    print(f"Existing documents: {len(docs)}")

    for doc in docs:
        print(f"  - {doc[0]} | {doc[1]}")

print("\nSTATUS: READ-ONLY")
print("DATABASE TIDAK DIUBAH.")
conn.close()
