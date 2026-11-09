import sqlite3

db = sqlite3.connect(
    "file:database/garment.db?mode=ro",
    uri=True
)
db.row_factory = sqlite3.Row

try:
    rows = db.execute("""
        SELECT
            m.id AS machine_id,
            m.model,
            t.id AS troubleshooting_id,
            t.code,
            t.problem,
            t.symptoms,
            t.possible_cause,
            t.solution,
            t.safety_notes,
            t.source
        FROM troubleshooting t
        JOIN machines m ON m.id = t.machine_id
        JOIN brands b ON b.id = m.brand_id
        WHERE UPPER(b.name) = 'JUKI'
          AND (
              t.code IS NULL
              OR TRIM(t.code) = ''
          )
        ORDER BY m.model, t.id
    """).fetchall()

    print(f"TOTAL BARIS KODE KOSONG: {len(rows)}")

    current_model = None
    for r in rows:
        if r["model"] != current_model:
            current_model = r["model"]
            print("\n" + "=" * 65)
            print(f"MODEL: {current_model} | MACHINE ID: {r['machine_id']}")
            print("=" * 65)

        print(f"\nID: {r['troubleshooting_id']}")
        print(f"Masalah   : {r['problem']}")
        print(f"Gejala    : {r['symptoms']}")
        print(f"Penyebab  : {r['possible_cause']}")
        print(f"Solusi    : {r['solution']}")
        print(f"Keselamatan: {r['safety_notes']}")
        print(f"Sumber    : {r['source']}")

    print("\nAudit selesai. Database tidak diubah.")

finally:
    db.close()
