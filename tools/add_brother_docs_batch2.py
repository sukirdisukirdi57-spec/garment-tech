import sqlite3
import sys

DB = "database/garment.db"

TARGETS = [
    (
        76,
        "S-6280A",
        "Manual",
        "Brother S-6280A Instruction Manual",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/s-6280a",
    ),
    (
        76,
        "S-6280A",
        "Parts List",
        "Brother S-6280A Parts Book",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/s-6280a",
    ),
    (
        80,
        "S-7180AT",
        "Manual",
        "Brother S-7180AT Instruction Manual",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/s-7180at",
    ),
    (
        80,
        "S-7180AT",
        "Parts List",
        "Brother S-7180AT Parts Book",
        "https://industrialsewingmachine.global.brother/en-ap/all-products/s-7180at",
    ),
]

con = sqlite3.connect(DB)
cur = con.cursor()

try:
    print("=== BROTHER DOCUMENT BATCH 2 ===")
    print("TARGET :", len(TARGETS), "dokumen")
    print("MODE   : SAFETY CHECK + TRANSACTION\n")

    # 1. Cek ID + model
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

    # 2. Cek duplikat
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
                f"{machine_id} | {model} | {doc_type} | existing id={row[0]}"
            )

    if duplicates:
        print("\nDUPLIKAT DITEMUKAN:")
        for item in duplicates:
            print(" ", item)

        raise RuntimeError(
            "INSERT dibatalkan karena dokumen target sudah ada."
        )

    print("2. DUPLIKAT         : TIDAK ADA")

    # 3. Tampilkan rencana
    print("\n=== RENCANA INSERT ===")

    for machine_id, model, doc_type, title, source_url in TARGETS:
        print(
            f"{machine_id} | {model} | {doc_type} | {title}"
        )

    print("\n3. RENCANA INSERT    : OK")

    # 4. Transaction
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
            "Sumber resmi Brother. Manual/Parts-book tersedia melalui halaman resmi produk Brother.",
        ))

        inserted += cur.rowcount

    # 5. Pastikan tepat 4 INSERT
    if inserted != len(TARGETS):
        raise RuntimeError(
            f"Jumlah INSERT tidak sesuai: {inserted}, "
            f"seharusnya {len(TARGETS)}"
        )

    # 6. Verifikasi sebelum COMMIT
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
    print("DATABASE        : BERUBAH SESUAI 4 TARGET")

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
