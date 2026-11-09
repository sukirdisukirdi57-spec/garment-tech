import csv
import sqlite3
from pathlib import Path

DB = Path("database/garment.db")
OUT = Path("tools/pegasus_document_source_audit.csv")
MODELS = ("E22L", "E256", "EX5400", "TML326")

con = sqlite3.connect(
    f"file:{DB.resolve()}?mode=ro", uri=True
)
con.row_factory = sqlite3.Row

try:
    sql = """
        SELECT m.id AS machine_id, m.model,
               d.id AS document_id, d.document_type,
               d.title, d.source_url, d.local_file, d.notes
        FROM machines m
        LEFT JOIN documents d ON d.machine_id = m.id
        WHERE UPPER(m.model) IN (?, ?, ?, ?)
          AND UPPER(COALESCE(m.brand_id, '')) IN (
              SELECT UPPER(CAST(id AS TEXT))
              FROM brands
              WHERE UPPER(name) = 'PEGASUS'
          )
        ORDER BY m.model, d.document_type, d.id
    """

    # Deteksi skema merek dahulu agar query tetap aman
    # jika struktur tabel brands berbeda atau tidak tersedia.
    tables = {
        r["name"] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }

    if "brands" in tables:
        brand_cols = {
            r["name"] for r in con.execute("PRAGMA table_info(brands)")
        }
    else:
        brand_cols = set()

    if "brands" in tables and {"id", "name"} <= brand_cols:
        rows = con.execute(sql, MODELS).fetchall()
    else:
        # Fallback: model sesuai nama; tampilkan brand_id untuk
        # pemeriksaan manual bila tabel merek tidak standar.
        rows = con.execute("""
            SELECT m.id AS machine_id, m.model, m.brand_id,
                   d.id AS document_id, d.document_type,
                   d.title, d.source_url, d.local_file, d.notes
            FROM machines m
            LEFT JOIN documents d ON d.machine_id = m.id
            WHERE UPPER(m.model) IN (?, ?, ?, ?)
            ORDER BY m.model, d.document_type, d.id
        """, MODELS).fetchall()

    fields = list(rows[0].keys()) if rows else [
        "machine_id", "model", "document_id", "document_type",
        "title", "source_url", "local_file", "notes"
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dict(r) for r in rows)

    print("=== AUDIT SUMBER DOKUMEN PEGASUS ===")
    print("Jumlah baris:", len(rows))
    print("CSV:", OUT)

    for model in MODELS:
        group = [r for r in rows if r["model"].upper() == model]
        print(f"\n--- {model}: {len(group)} baris ---")
        for r in group:
            if r["document_id"] is None:
                print("BELUM ADA DOKUMEN TERDAFTAR")
                continue
            print(
                f'ID {r["document_id"]} | {r["document_type"]} | '
                f'{r["title"]}'
            )
            print("URL:", r["source_url"] or "(kosong)")
            print("File lokal:", r["local_file"] or "(tidak ada)")
            print("Catatan:", r["notes"] or "(kosong)")

    print("\nIntegritas:", con.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0])
    print("Mode: READ ONLY; database tidak diubah")
finally:
    con.close()
