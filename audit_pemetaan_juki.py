import sqlite3
import re
from pathlib import Path
from collections import defaultdict

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")

if not DB.exists() or not TXT.exists():
    raise SystemExit("Database atau teks PDF tidak ditemukan.")

pages = TXT.read_text(errors="replace").split("\f")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

parts = con.execute("""
    SELECT id, part_number, part_name, quantity, catalog_ref
    FROM parts
    WHERE machine_id = 43
    ORDER BY id
""").fetchall()

components = con.execute("""
    SELECT id, component_name, part_number, diagram_page
    FROM components
    WHERE id BETWEEN 542 AND 558
    ORDER BY id
""").fetchall()

def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip()).upper()

# Cocokkan nomor part dan Ref. terhadap isi tiap potongan.
# Tidak mengubah tabel atau data database.
by_page = defaultdict(list)

for part in parts:
    pn = norm(part["part_number"])
    ref = str(part["catalog_ref"] or "").strip()

    if not pn or not ref:
        continue

    for chunk_no, content in enumerate(pages, 1):
        for line in content.splitlines():
            line_n = norm(line)
            if pn not in line_n:
                continue

            # Indeks gabungan di bagian belakang PDF biasanya menampilkan
            # nomor part bersama pasangan angka; tandai saja untuk ditinjau.
            if re.search(rf"^\s*{re.escape(ref)}\s+", line):
                by_page[chunk_no].append(
                    (part["id"], pn, ref, line.strip())
                )

print("=== JUMLAH POTONGAN TEKS ===", len(pages))
print("=== RINGKASAN KECocOKAN REF + NOMOR PART ===")

for chunk_no in sorted(by_page):
    rows = by_page[chunk_no]
    unique_ids = len({r[0] for r in rows})
    print(
        f"Potongan {chunk_no:02d}: "
        f"{len(rows)} kecocokan baris, {unique_ids} ID part"
    )

print("\n=== KOMPONEN: CEK NOMOR PART DI POTONGAN KANDIDAT ===")
for c in components:
    target = norm(c["part_number"])
    hits = []

    for chunk_no, content in enumerate(pages, 1):
        lines = [
            line.strip()
            for line in content.splitlines()
            if target and target in norm(line)
        ]
        if lines:
            hits.append((chunk_no, lines[:2]))

    print(
        f"\nID {c['id']} | {c['component_name']} | "
        f"PN {c['part_number']} | diagram_page={c['diagram_page']}"
    )
    for chunk_no, lines in hits:
        print(f"  Potongan {chunk_no}:")
        for line in lines:
            print("   ", line)

print("\n=== CONTOH PART YANG BELUM DIPETAKAN ===")
for p in parts[:15]:
    print(
        f"ID={p['id']} Ref={p['catalog_ref']} "
        f"PN={p['part_number']} Qty={p['quantity']} "
        f"Nama={p['part_name']}"
    )

con.close()
print("\nAUDIT SELESAI — DATABASE TIDAK DIUBAH.")
