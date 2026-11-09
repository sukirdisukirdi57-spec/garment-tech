import csv
import re
from pathlib import Path

TXT = Path("assets/documents/juki/ams210en-parts.txt")
CSV_FILE = Path("preview_daftar_part_juki.csv")
OUT = Path("baris_belum_cocok_juki.csv")

PAGE_CHUNK = {
    6: 7, 8: 9, 10: 11, 12: 13, 14: 15, 16: 17,
    20: 21, 22: 22, 23: 23, 28: 29, 30: 31, 32: 33
}

chunks = TXT.read_text(errors="replace").split("\f")

with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
    matched = list(csv.DictReader(f))

matched_keys = {
    (int(r["pdf_page"]), int(r["line_no"]))
    for r in matched
}

result = []

for page, chunk_no in PAGE_CHUNK.items():
    for line_no, line in enumerate(
        chunks[chunk_no - 1].splitlines(), start=1
    ):
        s = line.strip()

        if not re.match(r"^\d+\s+", s):
            continue

        # Pastikan baris memiliki kandidat nomor part.
        if not re.search(r"\b[A-Z0-9]{2,}(?:-[A-Z0-9]+)+\b", s):
            continue

        if (page, line_no) in matched_keys:
            continue

        result.append({
            "pdf_page": page,
            "text_chunk": chunk_no,
            "line_no": line_no,
            "catalog_line": s,
        })

with OUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["pdf_page", "text_chunk", "line_no", "catalog_line"]
    )
    writer.writeheader()
    writer.writerows(result)

print("Baris diekspor:", len(result))
print("File:", OUT)
print("\nContoh 20 baris pertama:")
for row in result[:20]:
    print(
        f"PDF {row['pdf_page']} | Ref/baris {row['line_no']} | "
        f"{row['catalog_line']}"
    )
print("\nDatabase tidak diubah.")
