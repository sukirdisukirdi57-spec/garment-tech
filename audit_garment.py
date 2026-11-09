import sqlite3
from pathlib import Path

db = Path("database/garment.db")

if not db.exists():
    print("Database tidak ditemukan:", db.resolve())
    raise SystemExit

conn = sqlite3.connect(
    f"file:{db.resolve()}?mode=ro",
    uri=True
)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

tables = [
    "machines", "components", "documents",
    "parts", "specifications", "troubleshooting"
]

existing = {
    r["name"] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
}

print("\n===== AUDIT DATA KOSONG =====")

for table in tables:
    if table not in existing:
        print(f"\n{table}: tabel tidak ditemukan")
        continue

    print(f"\n--- {table} ---")
    columns = cur.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    for col in columns:
        name = col["name"]
        if name == "id":
            continue

        sql = (
            f'SELECT COUNT(*) FROM "{table}" '
            f'WHERE "{name}" IS NULL '
            f'OR TRIM(CAST("{name}" AS TEXT)) = ""'
        )
        count = cur.execute(sql).fetchone()[0]

        if count:
            print(f"{name}: {count} kosong")

print("\n===== DUPLIKAT MODEL MESIN =====")

if "machines" in existing:
    rows = cur.execute("""
        SELECT brand_id, LOWER(TRIM(model)) AS model_bersih,
               COUNT(*) AS jumlah
        FROM machines
        WHERE model IS NOT NULL AND TRIM(model) <> ''
        GROUP BY brand_id, LOWER(TRIM(model))
        HAVING COUNT(*) > 1
        ORDER BY jumlah DESC
        LIMIT 30
    """).fetchall()

    if not rows:
        print("Tidak ditemukan duplikat berdasarkan pemeriksaan ini.")

    for r in rows:
        print(
            f"brand_id={r['brand_id']}, "
            f"model={r['model_bersih']}, jumlah={r['jumlah']}"
        )

print("\n===== RELASI DATA =====")

checks = [
    ("machines", "brand_id", "brands"),
    ("machines", "machine_type_id", "machine_types"),
    ("components", "machine_id", "machines"),
    ("documents", "machine_id", "machines"),
]

for child, column, parent in checks:
    if child not in existing or parent not in existing:
        continue

    child_cols = {
        r["name"] for r in cur.execute(
            f'PRAGMA table_info("{child}")'
        )
    }
    parent_cols = {
        r["name"] for r in cur.execute(
            f'PRAGMA table_info("{parent}")'
        )
    }

    if column not in child_cols or "id" not in parent_cols:
        continue

    sql = f"""
        SELECT COUNT(*)
        FROM "{child}" c
        LEFT JOIN "{parent}" p ON c."{column}" = p.id
        WHERE c."{column}" IS NOT NULL AND p.id IS NULL
    """
    count = cur.execute(sql).fetchone()[0]
    print(f"{child}.{column} -> {parent}.id: {count}")

conn.close()
print("\n===== AUDIT SELESAI =====")
