#!/usr/bin/env python3
"""Insert parts DDL-9000C-S dari CSV ke DB + backup otomatis."""
import csv, sqlite3, shutil
from pathlib import Path
from datetime import datetime

CSV = Path("audit-kelengkapan/parts_ddl9000cs_hasil_parse.csv")
DB  = Path("database/garment.db")
MID = 17
EXPECTED_MODEL = "DDL-9000C-S"

# 1. Backup
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB.with_name(f"{DB.name}.backup-parts-ddl9000cs-{ts}")
shutil.copy2(DB, bak)
print(f"[BACKUP] {bak}")

# 2. Validasi
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT model FROM machines WHERE id = ?", (MID,))
row = cur.fetchone()
if not row or row[0] != EXPECTED_MODEL:
    raise SystemExit(f"BATAL: machine_id={MID} bukan {EXPECTED_MODEL} (dapat: {row})")

cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id = ?", (MID,))
before = cur.fetchone()[0]
print(f"[CEK] parts sebelum insert: {before}")

# 3. Insert
with CSV.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

inserted = 0
for r in rows:
    cur.execute("""INSERT INTO parts(machine_id, part_number, part_name,
                   quantity, catalog_ref, diagram_page)
                   VALUES(?,?,?,?,?,?)""",
                (MID, r["part_number"], r["part_name"],
                 int(float(r["quantity"])) if r["quantity"] else None,
                 int(r["catalog_ref"]) if r["catalog_ref"] else None,
                 None))  # diagram_page tidak tersedia dari txt
    inserted += 1

conn.commit()

# 4. Verifikasi
cur.execute("SELECT COUNT(*) FROM parts WHERE machine_id = ?", (MID,))
after = cur.fetchone()[0]
print(f"[CEK] parts sesudah insert: {after}")
print(f"[HASIL] {inserted} baris di-insert (selisih: {after - before})")

if after - before != inserted:
    print("⚠️  PERINGATAN: selisih tidak cocok dengan jumlah insert!")
else:
    print("✅ SUKSES")

conn.close()
