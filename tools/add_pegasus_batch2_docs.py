import sqlite3

DB = "database/garment.db"

docs = [
    (189, "Manual", "PEGASUS WX664P Series Manual",
     "https://www.pegasus.co.jp/en/machine/detail/series/s220/WX664P-01G"),
    (189, "Parts List", "PEGASUS WX664P Series Parts Catalog",
     "https://www.pegasus.co.jp/webcatalog/?filter=parts&lang=en"),

    (190, "Manual", "PEGASUS W3500P Series Manual (W3562P)",
     "https://www.pegasus.co.jp/en/machine/series/s202"),
    (190, "Parts List", "PEGASUS W3562P Series Parts Catalog",
     "https://www.pegasus.co.jp/webcatalog/?filter=parts&lang=en"),

    (191, "Manual", "PEGASUS W3664P Series Manual",
     "https://www.pegasus.co.jp/webcatalog/series.php?catalogid=ses00014&filter_lang=all"),
    (191, "Parts List", "PEGASUS W3664P Series Parts Catalog",
     "https://www.pegasus.co.jp/webcatalog/series.php?catalogid=ses00014&filter_lang=all"),
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
            SELECT id FROM documents
            WHERE machine_id = ? AND document_type = ?
        """, (machine_id, doc_type)).fetchone()

        if exists:
            raise RuntimeError(
                f"Dokumen sudah ada: machine_id={machine_id}, type={doc_type}"
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
    print("DATABASE : PEGASUS BATCH 2 DOCUMENTS DITAMBAHKAN")

except Exception as e:
    conn.rollback()
    print("ROLLBACK : OK")
    print("ERROR :", e)

finally:
    conn.close()
