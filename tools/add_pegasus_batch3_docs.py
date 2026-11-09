import sqlite3

DB = "database/garment.db"

docs = [
    (192, "Manual", "PEGASUS WT169P Series Manual",
     "https://www.pegasus.co.jp/webcatalog/?filter=manual&lang=en"),
    (192, "Parts List", "PEGASUS WT169P Series Parts Catalog",
     "https://www.pegasus.co.jp/webcatalog/?filter=parts&lang=en"),

    (193, "Manual", "PEGASUS W200P Series Manual (W264P)",
     "https://www.pegasus.co.jp/webcatalog/?filter=manual&lang=en"),
    (193, "Parts List", "PEGASUS W264P Series Parts Catalog",
     "https://www.pegasus.co.jp/webcatalog/3DCatalog.php?itemcd=973900000029&model=W200P&rev=01"),

    (194, "Manual", "PEGASUS FS700P Series Manual (FS703P)",
     "https://www.pegasus.co.jp/webcatalog/?filter=manual&lang=en"),
    (194, "Parts List", "PEGASUS FS700P Series Parts Catalog (FS703P)",
     "https://www.pegasus.co.jp/en/machine/series/s217"),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    # Safety check
    for machine_id, doc_type, title, url in docs:
        machine = cur.execute("""
            SELECT m.id, m.model, b.name
            FROM machines m
            JOIN brands b ON b.id = m.brand_id
            WHERE m.id = ?
        """, (machine_id,)).fetchone()

        if not machine:
            raise RuntimeError(f"Machine ID {machine_id} tidak ditemukan")

        if machine[2] != "PEGASUS":
            raise RuntimeError(
                f"Machine ID {machine_id} bukan PEGASUS: {machine[2]}"
            )

        exists = cur.execute("""
            SELECT id
            FROM documents
            WHERE machine_id = ? AND document_type = ?
        """, (machine_id, doc_type)).fetchone()

        if exists:
            raise RuntimeError(
                f"Dokumen sudah ada: {machine[1]} / {doc_type}"
            )

    # Transaction
    for machine_id, doc_type, title, url in docs:
        cur.execute("""
            INSERT INTO documents
            (machine_id, document_type, title, source_url, local_file, notes)
            VALUES (?, ?, ?, ?, NULL, ?)
        """, (
            machine_id,
            doc_type,
            title,
            url,
            "Sumber resmi PEGASUS."
        ))

    conn.commit()

    print("INSERT BERHASIL :", len(docs))
    print("COMMIT : OK")
    print("DATABASE : PEGASUS BATCH 3 DOCUMENTS DITAMBAHKAN")

except Exception as e:
    conn.rollback()
    print("ROLLBACK : OK")
    print("ERROR :", e)

finally:
    conn.close()
