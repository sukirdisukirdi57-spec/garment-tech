import sqlite3
import re
from pathlib import Path
from collections import defaultdict

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")

if not DB.exists() or not TXT.exists():
    raise SystemExit("Database atau teks katalog tidak ditemukan.")

chunks = TXT.read_text(errors="replace").split("\f")

def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).upper()

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

parts = con.execute("""
    SELECT id, part_number, part_name, quantity, catalog_ref
    FROM parts
    WHERE machine_id = 43
    ORDER BY id
""").fetchall()

table_chunks = []

for chunk_no, content in enumerate(chunks, start=1):
    upper = content.upper()
    if "NUMERICAL INDEX OF PARTS" in upper:
        continue
    if all(x in upper for x in ("REF.NO", "PART NO", "DESCRIPTION")):
        table_chunks.append(chunk_no)

hits_by_id = defaultdict(list)

for p in parts:
    pn = norm(p["part_number"])
    ref = norm(p["catalog_ref"])
    if not pn or not ref:
        continue

    for chunk_no in table_chunks:
        for line_no, line in enumerate(
            chunks[chunk_no - 1].splitlines(), start=1
        ):
            ln = norm(line)
            if pn not in ln:
                continue
            if not re.match(rf"^{re.escape(ref)}(?:\s|$)", ln):
                continue

            hits_by_id[p["id"]].append({
                "chunk": chunk_no,
                "line_no": line_no,
                "line": line.strip()
            })

print("=== RINGKASAN PEMETAAN KANDIDAT ===")
print("Jumlah part database:", len(parts))
print("Potongan tabel utama:", table_chunks)
print("Cocok satu kali:", sum(len(hits_by_id[p["id"]]) == 1 for p in parts))
print("Cocok ganda:", sum(len(hits_by_id[p["id"]]) > 1 for p in parts))
print("Tidak ditemukan:", sum(len(hits_by_id[p["id"]]) == 0 for p in parts))

print("\n=== JUMLAH KANDIDAT PER POTONGAN ===")
for chunk_no in table_chunks:
    count = sum(
        1 for p in parts
        for h in hits_by_id[p["id"]]
        if h["chunk"] == chunk_no
    )
    print(f"Potongan {chunk_no:02d} | PDF kandidat {chunk_no - 1:02d} | {count} kecocokan")

print("\n=== KECocOKAN GANDA ===")
for p in parts:
    hits = hits_by_id[p["id"]]
    if len(hits) <= 1:
        continue

    print(f"\nID {p['id']} | Ref {p['catalog_ref']} | {p['part_number']} | {p['part_name']}")
    for h in hits:
        print(f"  Potongan {h['chunk']} | baris {h['line_no']}: {h['line']}")

print("\n=== NOMOR PART ASSEMBLY ===")
components = con.execute("""
    SELECT id, component_name, part_number, diagram_page
    FROM components
    WHERE id BETWEEN 542 AND 558
    ORDER BY id
""").fetchall()

for c in components:
    target = norm(c["part_number"])
    print(f"\nKomponen {c['id']} | {c['component_name']} | PN={c['part_number']} | PDF tersimpan={c['diagram_page']}")

    for chunk_no in table_chunks:
        for line_no, line in enumerate(chunks[chunk_no - 1].splitlines(), start=1):
            if target and target in norm(line):
                print(f"  PDF kandidat {chunk_no - 1} | baris {line_no}: {line.strip()}")

con.close()
print("\nSELESAI — DATABASE TIDAK DIUBAH.")
