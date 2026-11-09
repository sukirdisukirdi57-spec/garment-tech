import sqlite3
import csv
from pathlib import Path
from collections import Counter

DB = "database/garment.db"
OUT = "audit-brother227-local-parts-ringkas.csv"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

machine = con.execute("""
    SELECT id, model FROM machines
    WHERE model = 'BAS-311HN-03S'
""").fetchone()

if not machine:
    raise SystemExit("Model BAS-311HN-03S tidak ditemukan.")

rows = con.execute("""
    SELECT part_number, part_name, quantity, catalog_ref,
           diagram_page, source_document_id, note, notes, quantity_raw
    FROM parts
    WHERE machine_id = ?
    ORDER BY catalog_ref, diagram_page, part_number
""", (machine["id"],)).fetchall()

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "part_number", "part_name", "quantity", "catalog_ref",
        "diagram_page", "source_document_id", "note", "notes",
        "quantity_raw"
    ])
    writer.writerows([tuple(r) for r in rows])

print("Model:", machine["model"], "| machine_id:", machine["id"])
print("Jumlah baris lokal:", len(rows))
print("Nomor part kosong:", sum(not (r["part_number"] or "").strip() for r in rows))
print("Nama part kosong:", sum(not (r["part_name"] or "").strip() for r in rows))
print("Jumlah referensi katalog:", len(set(r["catalog_ref"] for r in rows)))
print("Laporan dibuat:", Path(OUT).resolve())
print("Database tidak diubah.")
con.close()
