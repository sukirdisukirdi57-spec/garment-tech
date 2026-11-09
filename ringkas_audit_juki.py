import sqlite3
from pathlib import Path

DB = Path("database/garment.db")
if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

db = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
db.row_factory = sqlite3.Row

try:
    print("=== RINGKASAN AUDIT JUKI ===")

    machines = db.execute("""
        SELECT m.id, m.model, b.name AS brand
        FROM machines m
        LEFT JOIN brands b ON b.id = m.brand_id
        WHERE UPPER(COALESCE(b.name, '')) LIKE '%JUKI%'
        ORDER BY m.model
    """).fetchall()

    if not machines:
        print("Tidak ditemukan mesin JUKI melalui tabel brands.")
        raise SystemExit(0)

    total_rows = total_codes = total_missing = 0

    for m in machines:
        rows = db.execute("""
            SELECT id, problem, code, source
            FROM troubleshooting
            WHERE machine_id = ?
            ORDER BY id
        """, (m["id"],)).fetchall()

        coded = [r for r in rows if (r["code"] or "").strip()]
        missing = [r for r in rows if not (r["code"] or "").strip()]
        no_source = [
            r for r in coded if not (r["source"] or "").strip()
        ]

        total_rows += len(rows)
        total_codes += len(coded)
        total_missing += len(missing)

        print(f"\n{m['model']} (ID {m['id']})")
        print(
            f"Data: {len(rows)} | Kode terisi: {len(coded)}"
            f" | Kosong: {len(missing)}"
        )
        print(f"Kode terisi tanpa sumber: {len(no_source)}")

        if coded:
            print("Contoh kode (maks. 10):")
            for r in coded[:10]:
                print(
                    f"  ID {r['id']} | {r['code']} | {r['problem']}"
                )

    print("\n=== TOTAL ===")
    print("Model JUKI:", len(machines))
    print("Data troubleshooting:", total_rows)
    print("Kode terisi:", total_codes)
    print("Kode kosong:", total_missing)
    print("\nMode baca saja: database tidak diubah.")

finally:
    db.close()
