import sqlite3
import re
from pathlib import Path
from collections import defaultdict

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")

if not DB.exists() or not TXT.exists():
    raise SystemExit("Database atau teks PDF tidak ditemukan.")

chunks = TXT.read_text(errors="replace").split("\f")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

parts = con.execute("""
    SELECT id, part_number, part_name, quantity, catalog_ref
    FROM parts
    WHERE machine_id = 43
    ORDER BY id
""").fetchall()

def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).upper()

# Cari nomor part dan nomor referensi pada baris yang sama.
# Potongan 45 dan potongan indeks akhir ditampilkan sebagai kandidat
# terpisah, bukan otomatis dianggap sebagai halaman utama.
hits_by_id = defaultdict(list)

for part in parts:
    pn = norm(part["part_number"])
    ref = norm(part["catalog_ref"])

    if not pn or not ref:
        continue

    for chunk_no, content in enumerate(chunks, start=1):
        for line_no, line in enumerate(content.splitlines(), start=1):
            line_n = norm(line)

            if pn not in line_n:
                continue

            if not re.match(rf"^{re.escape(ref)}(?:\s|$)", line_n):
                continue

            hits_by_id[part["id"]].append({
                "chunk": chunk_no,
                "line": line_no,
                "text": line.strip()
            })

# Ringkasan kecocokan
unmatched = []
matched_once = []
multiple = []

for p in parts:
    hits = hits_by_id.get(p["id"], [])

    if len(hits) == 0:
        unmatched.append(p)
    elif len(hits) == 1:
        matched_once.append((p, hits[0]))
    else:
        multiple.append((p, hits))

print("=== RINGKASAN ===")
print("Total part database       :", len(parts))
print("Cocok tepat satu baris    :", len(matched_once))
print("Cocok lebih dari satu     :", len(multiple))
print("Tidak ditemukan           :", len(unmatched))

print("\n=== JUMLAH KANDIDAT PER POTONGAN ===")
counts = defaultdict(int)
for hits in hits_by_id.values():
    for hit in hits:
        counts[hit["chunk"]] += 1

for chunk_no in sorted(counts):
    print(f"Potongan {chunk_no:02d}: {counts[chunk_no]} kandidat baris")

print("\n=== PART YANG COCOK DI BEBERAPA POTONGAN ===")
for p, hits in multiple:
    print(
        f"ID={p['id']} Ref={p['catalog_ref']} "
        f"PN={p['part_number']} Nama={p['part_name']}"
    )
    for hit in hits:
        print(
            f"  Potongan {hit['chunk']:02d}, baris {hit['line']}: "
            f"{hit['text']}"
        )

print("\n=== PART YANG TIDAK DITEMUKAN ===")
for p in unmatched:
    print(
        f"ID={p['id']} Ref={p['catalog_ref']} "
        f"PN={p['part_number']} Nama={p['part_name']}"
    )

print("\n=== KANDIDAT POTONGAN 45 (VARIAN) ===")
for p in parts:
    for hit in hits_by_id.get(p["id"], []):
        if hit["chunk"] == 45:
            print(
                f"ID={p['id']} Ref={p['catalog_ref']} "
                f"PN={p['part_number']} | {hit['text']}"
            )

con.close()
print("\nAUDIT SELESAI — DATABASE TIDAK DIUBAH.")
