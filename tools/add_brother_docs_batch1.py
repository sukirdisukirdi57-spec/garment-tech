import sqlite3
import sys

DB = "database/garment.db"

TARGETS = [
    (
        108,
        "BE-438DP",
        "Catalog",
        "Brother BE-438DP Official Catalog",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/be-438dp",
    ),
    (
        111,
        "KE-430DP",
        "Manual",
        "Brother KE-430DP Instruction Manual",
        "https://industrialsewingmachine.global.brother/en-emea/all-products/ke-430dp",
    ),
    (
        111,
        "KE-430DP",
        "Parts List",
        "Brother KE-430DP Parts Book",
        "https://industrialsewingmachine.global.brother/en-emea/all-products/ke-430dp",
    ),
    (
        113,
        "BAS-311HX",
        "Manual",
        "BAS-311HX/BAS-326H Instruction Manual",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/nexio%20bas-311hx",
    ),
    (
        113,
        "BAS-311HX",
        "Parts List",
        "BAS-311HX/BAS-326H Parts Book",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/nexio%20bas-311hx",
    ),
    (
        114,
        "BAS-326HX",
        "Manual",
        "BAS-311HX/BAS-326H Instruction Manual",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/nexio-bas-326hx",
    ),
    (
        114,
        "BAS-326HX",
        "Parts List",
        "BAS-311HX/BAS-326H Parts Book",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/nexio-bas-326hx",
    ),
]

con = sqlite3.connect(DB)
cur = con.cursor()

try:
    print("=== BROTHER DOCUMENT INSERT SAFETY CHECK ===")
    print("Target:", len(TARGETS), "dokumen")
    print("Mode: TRANSACTION + ROLLBACK ON ERROR\n")

    # 1. Pastikan semua machine ID dan model benar
    for machine_id, model, doc_type, title, source_url in TARGETS:
        row = cur.execute(
            "SELECT id, model FROM machines WHERE id=?",
            (machine_id,)
        ).fetchone()

        if row is None:
            raise RuntimeError(
                f"ID mesin tidak ditemukan: {machine_id}"
            )

        if row[1] != model:
            raise RuntimeError(
                f"MODEL SALAH: ID {machine_id} = {row[1]}, "
                f"seharusnya {model}"
            )

    print("1. ID + MODEL       : OK")

    # 2. Pastikan tidak ada target yang sudah terdaftar
    duplicates = []

    for machine_id, model, doc_type, title, source_url in TARGETS:
        row = cur.execute("""
            SELECT id
            FROM documents
            WHERE machine_id=?
              AND document_type=?
              AND title=?
            LIMIT 1
        """, (machine_id, doc_type, title)).fetchone()

        if row:
            duplicates.append(
                f"{machine_id} | {model} | {doc_type} | "
                f"existing id={row[0]}"
            )

    if duplicates:
        print("\nDUPLIKAT DITEMUKAN:")
        for item in duplicates:
            print(" ", item)

        raise RuntimeError(
            "INSERT dibatalkan karena ada dokumen target yang sudah ada."
        )

    print("2. DUPLIKAT         : TIDAK ADA")

    # 3. Tampilkan rencana INSERT
    print("\n=== RENCANA INSERT ===")

    for machine_id, model, doc_type, title, source_url in TARGETS:
        print(
            f"{machine_id} | {model} | {doc_type} | {title}"
        )

    print("\n3. RENCANA INSERT    : OK")

    # 4. Mulai transaksi
    con.execute("BEGIN")

    inserted = 0

    for machine_id, model, doc_type, title, source_url in TARGETS:
        cur.execute("""
            INSERT INTO documents (
                machine_id,
                document_type,
                title,
                source_url,
                local_file,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            machine_id,
            doc_type,
            title,
            source_url,
            None,
            "Sumber resmi Brother. Dokumen tersedia melalui halaman resmi produk/support Brother.",
        ))

        inserted += cur.rowcount

    # 5. Pastikan tepat 7 row berhasil dibuat
    if inserted != len(TARGETS):
        raise RuntimeError(
            f"Jumlah INSERT tidak sesuai: {inserted}, "
            f"seharusnya {len(TARGETS)}"
        )

    # 6. Verifikasi dalam transaksi sebelum commit
    for machine_id, model, doc_type, title, source_url in TARGETS:
        row = cur.execute("""
            SELECT id
            FROM documents
            WHERE machine_id=?
              AND document_type=?
              AND title=?
        """, (machine_id, doc_type, title)).fetchone()

        if row is None:
            raise RuntimeError(
                f"Verifikasi gagal: {machine_id} | {doc_type}"
            )

    con.commit()

    print("\n=== HASIL ===")
    print(f"INSERT BERHASIL : {inserted}")
    print("COMMIT          : OK")
    print("DATABASE        : BERUBAH SESUAI 7 TARGET")

except Exception as e:
    con.rollback()

    print("\n=== HASIL ===")
    print("INSERT DIBATALKAN")
    print("ROLLBACK        : OK")
    print("DATABASE        : TIDAK BERUBAH")
    print("ERROR           :", e)

    sys.exit(1)

finally:
    con.close()
