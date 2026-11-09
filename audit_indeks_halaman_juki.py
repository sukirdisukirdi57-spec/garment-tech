import sqlite3
import re
from pathlib import Path
from collections import defaultdict

db = Path("database/garment.db")
txt = Path("assets/documents/juki/ams210en-parts.txt")
chunks = txt.read_text(errors="replace").split("\f")

con = sqlite3.connect(db)
con.row_factory = sqlite3.Row

parts = con.execute("""
    SELECT id, part_number, part_name, catalog_ref
    FROM parts
    WHERE machine_id = 43
    ORDER BY id
""").fetchall()

# Cari nomor halaman dan ref dari indeks numerik.
index_entries = defaultdict(list)

for chunk_no in (57, 58, 59, 60):
    if chunk_no > len(chunks):
        continue

    text = chunks[chunk_no - 1]
    if "NUMERICAL INDEX OF PARTS" not in text.upper():
        continue

    # Format indeks: PART_NUMBER PAGE REF.
    for line in text.splitlines():
        line = line.strip()
        matches = re.findall(
            r"([A-Z0-9][A-Z0-9-]*)\s+(\d{1,2})\s+(\d{1,3})",
            line
        )
        for pn, page, ref in matches:
            index_entries[pn.upper()].append((int(page), int(ref)))

print("=== JUMLAH PART DATABASE ===", len(parts))
print("=== CONTOH HASIL INDEKS ===")

for p in parts[:25]:
    pn = (p["part_number"] or "").strip().upper()
    entries = index_entries.get(pn, [])
    print(
        f"ID={p['id']} PN={pn} RefDB={p['catalog_ref']} "
        f"Indeks={entries}"
    )

print("\n=== PART DENGAN LEBIH DARI SATU HALAMAN INDEKS ===")
count = 0
for p in parts:
    pn = (p["part_number"] or "").strip().upper()
    entries = sorted(set(index_entries.get(pn, [])))
    pages = sorted(set(page for page, ref in entries))
    if len(pages) > 1:
        print(
            f"ID={p['id']} PN={pn} RefDB={p['catalog_ref']} "
            f"Indeks={entries}"
        )
        count += 1
        if count >= 40:
            print("...dibatasi 40 hasil pertama")
            break

con.close()
print("\nAUDIT SELESAI — DATABASE TIDAK DIUBAH.")
