import sqlite3
import csv
import re
from pathlib import Path
from collections import Counter

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
OUT = Path("staging_kemunculan_katalog_juki.csv")

PAGE_CHUNK = {
    6: 7, 8: 9, 10: 11, 12: 13, 14: 15, 16: 17,
    20: 21, 22: 22, 23: 23, 28: 29, 30: 31, 32: 33
}

if not DB.exists() or not TXT.exists():
    raise SystemExit("Database atau teks katalog tidak ditemukan.")

chunks = TXT.read_text(errors="replace").split("\f")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

db_parts = con.execute("""
    SELECT id, part_number, part_name, catalog_ref, quantity
    FROM parts
    WHERE machine_id = 43
""").fetchall()

by_pn = {}
for p in db_parts:
    by_pn.setdefault(
        re.sub(r"\s+", "", p["part_number"] or "").upper(), []
    ).append(p)

# Token nomor part berkode seperti 400-12345, SM-1234567-TP,
# atau B1411-552-0A0.
pn_pattern = re.compile(
    r"(?<![A-Z0-9])"
    r"[A-Z0-9]+(?:-[A-Z0-9]+)+"
    r"(?![A-Z0-9])",
    re.I
)

result = []

for pdf_page, chunk_no in PAGE_CHUNK.items():
    for line_no, raw in enumerate(
        chunks[chunk_no - 1].splitlines(), start=1
    ):
        line = raw.strip()

        # Ref harus menjadi angka pertama pada baris katalog.
        m = re.match(r"^(\d+)\s+(.+)$", line)
        if not m:
            continue

        ref = m.group(1)
        rest = m.group(2)

        # Abaikan baris yang bukan entri part.
        pns = pn_pattern.findall(rest)
        if not pns:
            continue

        # Biasanya nomor part adalah token berkode pertama setelah
        # Ref, simbol bintang, atau penanda varian.
        pn = pns[0].upper()
        key = re.sub(r"\s+", "", pn).upper()
        matches = by_pn.get(key, [])

        same_ref = [
            p for p in matches
            if str(p["catalog_ref"] or "").strip() == ref
        ]

        if same_ref:
            status = "PN_DAN_REF_COCOK"
        elif matches:
            status = "PN_ADA_REF_BERBEDA"
        else:
            status = "PN_BELUM_ADA"

        result.append({
            "pdf_page": pdf_page,
            "text_chunk": chunk_no,
            "line_no": line_no,
            "catalog_ref": ref,
            "part_number": pn,
            "catalog_line_original": line,
            "db_match_count": len(matches),
            "db_same_ref_count": len(same_ref),
            "db_part_ids": ",".join(str(p["id"]) for p in matches),
            "status": status,
        })

fields = [
    "pdf_page", "text_chunk", "line_no", "catalog_ref",
    "part_number", "catalog_line_original", "db_match_count",
    "db_same_ref_count", "db_part_ids", "status"
]

with OUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(result)

print("=== STAGING KATALOG JUKI ===")
print("Total kemunculan katalog:", len(result))

counts = Counter(r["status"] for r in result)
for status, count in counts.items():
    print(f"{status}: {count}")

print("\nJumlah per halaman:")
for page in PAGE_CHUNK:
    count = sum(r["pdf_page"] == page for r in result)
    print(f"PDF {page:02d}: {count} baris")

print("\nFile dibuat:", OUT)
print("Database tidak diubah.")
con.close()
