import sqlite3
from pathlib import Path

DB = Path("database/garment.db")

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB.resolve()}")

db = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
db.row_factory = sqlite3.Row

def columns(table):
    return {
        row["name"]
        for row in db.execute(f'PRAGMA table_info("{table}")')
    }

def find_table(candidates):
    tables = {
        r["name"]
        for r in db.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
        """)
    }
    return next((t for t in candidates if t in tables), None)

try:
    tables = {
        r["name"]
        for r in db.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
        """)
    }

    if "machines" not in tables or "troubleshooting" not in tables:
        raise SystemExit(
            "Tabel machines atau troubleshooting tidak ditemukan."
        )

    mc = columns("machines")
    tc = columns("troubleshooting")

    required = {"id", "model"}
    if not required.issubset(mc):
        raise SystemExit("Kolom id/model pada machines tidak sesuai.")
    if not {"machine_id", "problem", "code"}.issubset(tc):
        raise SystemExit(
            "Kolom machine_id/problem/code pada troubleshooting tidak sesuai."
        )

    # Cari tabel merek melalui foreign key.
    brand_table = None
    if "brand_id" in mc:
        for fk in db.execute('PRAGMA foreign_key_list("machines")'):
            if fk["from"] == "brand_id":
                brand_table = fk["table"]
                break

    # Fallback jika foreign key tidak didefinisikan.
    if not brand_table:
        brand_table = find_table(["brands", "brand", "manufacturers"])

    brand_cols = columns(brand_table) if brand_table else set()
    brand_name_col = next(
        (c for c in ("name", "brand_name", "title")
         if c in brand_cols),
        None
    )

    print("=== AUDIT DATABASE JUKI (READ-ONLY) ===")
    print("Database:", DB.resolve())
    print("Mode: hanya membaca; tidak ada data yang diubah.")
    print()

    if brand_table and brand_name_col and "brand_id" in mc:
        query = f"""
            SELECT m.id, m.model, b."{brand_name_col}" AS brand
            FROM machines m
            LEFT JOIN "{brand_table}" b ON m.brand_id = b.id
            WHERE UPPER(b."{brand_name_col}") LIKE '%JUKI%'
            ORDER BY m.model, m.id
        """
        machines = db.execute(query).fetchall()
    else:
        print(
            "PERHATIAN: tabel/kolom merek tidak terdeteksi dengan pasti."
        )
        print("Daftar mesin berikut perlu diperiksa mereknya secara manual.")
        machines = db.execute("""
            SELECT id, model, NULL AS brand
            FROM machines
            ORDER BY model, id
        """).fetchall()

    if not machines:
        print("Tidak ditemukan mesin dengan merek JUKI.")
        print("Periksa isi tabel merek dan relasi brand_id.")
        raise SystemExit(0)

    print(f"Jumlah mesin untuk diperiksa: {len(machines)}")

    total_rows = 0
    total_codes = 0
    total_missing = 0

    for machine in machines:
        mid = machine["id"]
        model = machine["model"]

        rows = db.execute("""
            SELECT id, problem, code, source,
                   symptoms, possible_cause, solution, safety_notes
            FROM troubleshooting
            WHERE machine_id = ?
            ORDER BY id
        """, (mid,)).fetchall()

        coded = [r for r in rows if (r["code"] or "").strip()]
        missing = [r for r in rows if not (r["code"] or "").strip()]
        no_source = [
            r for r in coded if not (r["source"] or "").strip()
        ] if "source" in tc else coded

        total_rows += len(rows)
        total_codes += len(coded)
        total_missing += len(missing)

        print("\n" + "=" * 68)
        print(f"Machine ID : {mid}")
        print(f"Model      : {model}")
        if machine["brand"]:
            print(f"Merek      : {machine['brand']}")
        print(f"Total data : {len(rows)}")
        print(f"Kode terisi: {len(coded)}")
        print(f"Kode kosong: {len(missing)}")

        if coded:
            print("\n-- DATA BERKODE (perlu dicocokkan dengan manual model) --")
            for r in coded:
                source = r["source"] if "source" in tc else None
                print(
                    f"ID {r['id']} | {r['code']} | "
                    f"{r['problem']} | Sumber: {source or 'KOSONG'}"
                )

        if no_source:
            print("\nPERLU VERIFIKASI SUMBER:")
            for r in no_source:
                print(f"ID {r['id']} | kode {r['code']} | {r['problem']}")

        if missing:
            print("\n-- DATA TANPA KODE ERROR --")
            for r in missing:
                print(f"ID {r['id']} | {r['problem']}")

    print("\n" + "=" * 68)
    print("=== RINGKASAN ===")
    print("Jumlah mesin diperiksa :", len(machines))
    print("Jumlah baris troubleshooting:", total_rows)
    print("Baris dengan kode terisi:", total_codes)
    print("Baris tanpa kode        :", total_missing)
    print()
    print("CATATAN:")
    print("- Kode terisi belum otomatis berarti kode resmi.")
    print("- Cocokkan kode, model, panel dan sistem kontrol dengan manual.")
    print("- Masalah mekanis tanpa kode resmi harus tetap tanpa kode.")
    print("- Audit ini tidak menambah, menghapus, atau mengubah data.")

finally:
    db.close()
