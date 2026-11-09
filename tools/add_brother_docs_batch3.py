import sqlite3

DB = "database/garment.db"

TARGETS = [
    (50, "S-7220B", "Manual",
     "Brother S-7220B Instruction Manual",
     "https://industrialsewingmachine.global.brother/en-ap/all-products/s-7220b"),
    (50, "S-7220B", "Product Page",
     "Brother S-7220B Official Product Page",
     "https://industrialsewingmachine.global.brother/en-ap/all-products/s-7220b"),
    (53, "S-7200A", "Manual",
     "Brother S-7200A Instruction Manual",
     "https://www.brother-usa.com/-/media/brother/product-catalog-media/documents/2020/08/25/08/35/s7200a_e_2003_05.pdf"),
    (53, "S-7200A", "Product Page",
     "Brother S-7200A Official Product Page",
     "https://industrialsewingmachine.global.brother/en-ap/all-products/s-7200a"),
]

con = sqlite3.connect(DB)
cur = con.cursor()

try:
    print("=== BROTHER DOCUMENT BATCH 3 ===")
    print("TARGET : 4 dokumen")
    print("MODE   : SAFETY CHECK + TRANSACTION")

    # 1. ID + MODEL
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
                f"Model salah untuk ID {machine_id}: "
                f"DB={row[1]}, TARGET={expected_model}"
            )

    print("1. ID + MODEL       : OK")

    # 2. DUPLIKAT
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
                f"Duplikat ditemukan: {machine_id} | "
                f"{doc_type} | {title} | doc_id={dup[0]}"
            )

    print("2. DUPLIKAT         : TIDAK ADA")

    print("\n=== RENCANA INSERT ===")
    for machine_id, model, doc_type, title, source_url in TARGETS:
        print(f"{machine_id} | {model} | {doc_type} | {title}")

    print("\n3. RENCANA INSERT    : OK")

    # 4. TRANSACTION
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

    # 5. VERIFIKASI SEBELUM COMMIT
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
    print("DATABASE        : BERUBAH SESUAI 4 TARGET")

except Exception as e:
    con.rollback()
    print("\n=== ERROR ===")
    print("ROLLBACK        : OK")
    print("DATABASE        : TIDAK BERUBAH")
    print("ERROR           :", e)

finally:
    con.close()
