import sqlite3
import csv
import re
from pathlib import Path
from collections import Counter

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
OUT = Path("preview_daftar_part_juki.csv")

# Nomor halaman PDF yang sudah diverifikasi melalui nomor part assembly.
# Nomor potongan teks berasal dari hasil audit, bukan hasil hitung otomatis.
PAGE_CHUNK = {
    6: 7,
    8: 9,
    10: 11,
    12: 13,
    14: 15,
    16: 17,
    20: 21,
    22: 22,
    23: 23,
    28: 29,
    30: 31,
    32: 33,
}

def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).upper()

if not DB.exists() or not TXT.exists():
    raise SystemExit("Database atau teks katalog tidak ditemukan.")

chunks = TXT.read_text(errors="replace").split("\f")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

parts = con.execute("""
    SELECT id, part_number, part_name, quantity, catalog_ref, note
    FROM parts
    WHERE machine_id = 43
    ORDER BY id
""").fetchall()

rows = []
page_counts = Counter()

for page, chunk_no in PAGE_CHUNK.items():
    if chunk_no > len(chunks):
        print(f"PERINGATAN: potongan {chunk_no} tidak tersedia.")
        continue

    lines = chunks[chunk_no - 1].splitlines()

    for p in parts:
        pn = norm(p["part_number"])
        ref = norm(p["catalog_ref"])

        if not pn or not ref:
            continue

        for line_no, line in enumerate(lines, start=1):
            ln = norm(line)

            # Harus cocok dengan Ref. dan nomor part pada baris yang sama.
            if not re.match(rf"^{re.escape(ref)}(?:\s|$)", ln):
                continue

            if not re.search(rf"(?<![A-Z0-9-]){re.escape(pn)}(?![A-Z0-9-])", ln):
                continue

            rows.append({
                "pdf_page": page,
                "text_chunk": chunk_no,
                "line_no": line_no,
                "part_id": p["id"],
                "catalog_ref": p["catalog_ref"],
                "part_number": p["part_number"],
                "part_name_db": p["part_name"],
                "quantity_db": p["quantity"],
                "catalog_line": line.strip(),
                "status": "PERLU CEK" if "#" in line or "☆" in line else "KANDIDAT",
            })
            page_counts[page] += 1

fields = [
    "pdf_page", "text_chunk", "line_no", "part_id", "catalog_ref",
    "part_number", "part_name_db", "quantity_db", "catalog_line", "status"
]

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("=== PRATINJAU DAFTAR PART PER HALAMAN ===")
for page in PAGE_CHUNK:
    print(f"PDF halaman {page:02d}: {page_counts[page]} kecocokan")

print("\nTotal baris kandidat:", len(rows))
print("File CSV:", OUT)
print("Database tidak diubah.")

con.close()
