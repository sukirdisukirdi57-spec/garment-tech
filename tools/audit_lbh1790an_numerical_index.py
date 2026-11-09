import re
import sqlite3
from collections import Counter

PDF = "tmp/lbh1790an/numerical-index.txt"
DB = "database/garment.db"

pattern = re.compile(
    r'\b([A-Z0-9]+(?:-[A-Z0-9]+)+)\s+(\d{1,2})\s+(\d{1,2})\b'
)

index = []

with open(PDF, encoding="utf-8") as f:
    for line_no, line in enumerate(f, 1):
        for m in pattern.finditer(line):
            part_no, page, ref = m.groups()
            page_num = int(page)

            # PAGE 1–23: halaman diagram satu nomor sebelum halaman part.
            # PAGE 24 dan seterusnya: gunakan nomor halaman apa adanya.
            diagram_page = page_num if page_num == 24 else page_num - 1

            index.append((part_no, diagram_page, int(ref), line_no))

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

rows = db.execute("""
    SELECT part_number, diagram_page, catalog_ref
    FROM parts
    WHERE machine_id = 6
""").fetchall()

def norm_ref(value):
    if value is None:
        return ""
    value = str(value).strip()
    if value.isdigit():
        return str(int(value))
    return value

db_keys = Counter(
    (
        str(r["part_number"]).strip(),
        int(r["diagram_page"]) if r["diagram_page"] is not None else None,
        norm_ref(r["catalog_ref"])
    )
    for r in rows
)

index_keys = Counter(
    (pn, page, str(ref))
    for pn, page, ref, _ in index
)

missing = index_keys - db_keys
extra = db_keys - index_keys

print("=== AUDIT NUMERICAL INDEX LBH-1790AN ===")
print("Jumlah entri indeks terbaca :", len(index))
print("Jumlah baris parts database :", len(rows))
print("Kombinasi indeks unik       :", len(index_keys))
print("Kombinasi database unik     :", len(db_keys))

print("\n=== ENTRI INDEKS BELUM COCOK ===")
if not missing:
    print("Tidak ada.")
else:
    for (pn, page, ref), count in sorted(missing.items()):
        print(f"{pn:22} PAGE {page:2} REF {ref:>3} | jumlah {count}")

print("\n=== ENTRI DATABASE TIDAK ADA DI INDEKS ===")
if not extra:
    print("Tidak ada.")
else:
    for (pn, page, ref), count in sorted(extra.items()):
        print(f"{pn:22} diagram_page {page} REF {ref} | jumlah {count}")

db.close()
