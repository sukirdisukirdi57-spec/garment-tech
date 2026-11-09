import sqlite3

DB = "file:database/garment.db?mode=ro"

db = sqlite3.connect(DB, uri=True)
db.row_factory = sqlite3.Row

try:
    models = ("DDL-8000C", "DDL-8000CSM", "DDL-9000C-S")

    for model in models:
        rows = db.execute("""
            SELECT
                t.id,
                t.code,
                t.problem,
                t.symptoms,
                t.possible_cause,
                t.solution,
                t.safety_notes,
                t.source
            FROM troubleshooting AS t
            JOIN machines AS m ON m.id = t.machine_id
            JOIN brands AS b ON b.id = m.brand_id
            WHERE m.model = ?
              AND UPPER(b.name) = 'JUKI'
              AND TRIM(COALESCE(t.code, '')) <> ''
            ORDER BY t.id
        """, (model,)).fetchall()

        print("\n" + "=" * 78)
        print(f"MODEL: {model} | TOTAL: {len(rows)}")
        print("=" * 78)

        for r in rows:
            print(f"\nID: {r['id']} | KODE: {r['code']}")
            print(f"Masalah       : {r['problem']}")
            print(f"Gejala        : {r['symptoms']}")
            print(f"Penyebab      : {r['possible_cause']}")
            print(f"Solusi        : {r['solution']}")
            print(f"Keselamatan   : {r['safety_notes']}")
            print(f"Sumber        : {r['source']}")

    print("\nAudit selesai. Database tidak diubah.")

finally:
    db.close()
