#!/usr/bin/env python3
"""Dry-run: tampilkan preview insert parts ke DB tanpa commit."""
import csv, sqlite3
from pathlib import Path

CSV = Path("audit-kelengkapan/parts_ddl9000cs_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 17

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Cek duplikat terhadap DB saat ini
cur.execute("SELECT part_number FROM parts WHERE machine_id = ?", (MID,))
existing = {r[0] for r in cur.fetchall()}
print(f"Parts di DB saat ini untuk machine_id={MID}: {len(existing)}")

with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# Filter yang belum ada di DB
new_rows = [r for r in rows if r["part_number"] not in existing]
dup_rows = [r for r in rows if r["part_number"] in existing]

print(f"Baris CSV       : {len(rows)}")
print(f"Akan di-insert  : {len(new_rows)}")
print(f"Sudah ada di DB : {len(dup_rows)}")

print("\nPreview 3 baris yang akan di-insert:")
for r in new_rows[:3]:
    print(f"  {r['part_number']}  {r['part_name']}  qty={r['quantity']}  ref={r['catalog_ref']}")

conn.close()
print("\n(DRY-RUN — tidak ada yang ditulis ke DB)")
