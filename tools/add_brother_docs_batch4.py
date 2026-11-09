import sqlite3

DB = "database/garment.db"

TARGETS = [
    (79, "S-7180A", "Manual",
     "Brother S-7180A Instruction Manual",
     "https://industrialsewingmachine.global.brother/en-ap/all-products/s-7180a"),
    (108, "BE-438DP", "Manual",
     "Brother BE-438DP Instruction Manual",
     "https://industrialsewingmachine.global.brother/en-ap/all-products/be-438dp"),
    (108, "BE-438DP", "Parts List",
     "Brother BE-438DP Parts Book",
     "https://industrialsewingmachine.global.brother/en-ap/all-products/be-438dp"),
]

con = sqlite3.connect(DB)
cur = con.cursor()

try:
    print("=== BROTHER DOCUMENT BATCH 4 ===")
    print("TARGET : 3 dokumen")
    print("MODE   : SAFETY CHECK + TRANSACTION")

    for machine_id, expected_model, doc_type, title, source_url in TARGETS:
        row = cur.execute(
            "SELECT id, model FROM machines WHERE id=?",
            (machine_id,)
        ).fetchone()

        if not row:
            raise RuntimeError(
                f"Machine ID {machine_id} tidak ditemukan."
            )

        if row[1] != expected_model:
            raise RuntimeError(
                f"Model salah: ID {machine_id}, "
                f"DB={row[1]}, TARGET={expected_model}"
            )

    print("1. ID + MODEL       : OK")

    for machine_id, model, doc_type, title, source_url in TARGETS:
        dup = cur.execute("""
            SELECT id
            FROM documents
            WHERE machine_id=?
              AND document_type=?
              AND title=?
        """, (machine_id, doc_type, title)).fetchone()

        if dup:
            raise RuntimeError(
                f"Duplikat: {machine_id} | {doc_type} | "
                f"{title} | doc_id={dup[0]}"
            )

    print("2. DUPLIKAT         : TIDAK ADA")

    print("\n=== RENCANA INSERT ===")
    for machine_id, model, doc_type, title, source_url in TARGETS:
        print(f"{machine_id} | {model} | {doc_type} | {title}")

    print("\n3. RENCANA INSERT    : OK")

    con.execute("BEGIN")

    inserted_ids = []

    for machine_id, model, doc_type, title, source_url in TARGETS:
        cur.execute("""
            INSERT INTO documents
            (machine_id, document_type, title, source_url, local_file, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            machine_id,
            doc_type,
            title,
            source_url,
            None,
            "Sumber resmi Brother."
        ))

        inserted_ids.append(cur.lastrowid)

    for doc_id in inserted_ids:
        row = cur.execute("""
            SELECT id, machine_id, document_type, title
            FROM documents
            WHERE id=?
        """, (doc_id,)).fetchone()

        if not row:
            raise RuntimeError(
                f"Verifikasi gagal untuk document ID {doc_id}"
            )

    print("4. VERIFIKASI        : OK")

    con.commit()

    print("\n=== HASIL ===")
    print(f"INSERT BERHASIL : {len(inserted_ids)}")
    print("COMMIT          : OK")
    print("DATABASE        : BERUBAH SESUAI 3 TARGET")

except Exception as e:
    con.rollback()
    print("\n=== ERROR ===")
    print("ROLLBACK        : OK")
    print("DATABASE        : TIDAK BERUBAH")
    print("ERROR           :", e)

finally:
    con.close()
