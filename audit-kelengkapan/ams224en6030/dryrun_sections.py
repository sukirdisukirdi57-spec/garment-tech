import re
from pathlib import Path

path = Path("audit-kelengkapan/ams224en6030/partslist.txt")
lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

sections = [
    {
        "name": "FRAME & MISCELLANEOUS COVER COMPONENTS (4)",
        "start": 620,
        "end": 750,
        "expected": 91,
    },
    {
        "name": "X-Y COMPONENTS (2)",
        "start": 2150,
        "end": 2290,
        "expected": 96,
    },
]

# Format tabel: nomor ref, note opsional, part number, deskripsi, quantity mentah.
row_re = re.compile(
    r"^\s*(\d{1,3})\s+"
    r"(?:(#\d{2})\s+)?"
    r"([A-Z0-9][A-Z0-9-]*)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)

total = 0
failed = 0

for section in sections:
    start = section["start"]
    end = section["end"]
    found = []
    bad_candidates = []

    for lineno in range(start, min(end, len(lines)) + 1):
        line = lines[lineno - 1]
        m = row_re.match(line)
        if m:
            ref, note, part_no, description, qty_raw = m.groups()
            found.append({
                "line": lineno,
                "ref": int(ref),
                "note": note or "",
                "part_no": part_no,
                "description": description.strip(),
                "qty_raw": qty_raw,
            })
        elif re.match(r"^\s*\d{1,3}\s+", line):
            # Tandai kandidat yang tampak seperti baris tabel,
            # tetapi tidak cocok dengan pola.
            if re.search(r"[A-Z]{1,}", line) and re.search(r"\d", line):
                bad_candidates.append((lineno, line.rstrip()))

    refs = [r["ref"] for r in found]
    missing = sorted(set(range(1, section["expected"] + 1)) - set(refs))
    duplicates = sorted({x for x in refs if refs.count(x) > 1})

    print(f"\n=== {section['name']} ===")
    print(f"Rentang baris teks: {start}-{end}")
    print(f"Baris terparse: {len(found)} / target {section['expected']}")
    print(f"Nomor referensi hilang: {missing or 'tidak ada'}")
    print(f"Nomor referensi duplikat: {duplicates or 'tidak ada'}")
    print(f"Kandidat baris gagal: {len(bad_candidates)}")

    if bad_candidates:
        for lineno, line in bad_candidates[:15]:
            print(f"  GAGAL baris {lineno}: {line}")

    print("\nContoh hasil parse (maksimal 5):")
    for row in found[:5]:
        print(row)

    total += len(found)
    failed += len(bad_candidates)

print("\n=== RINGKASAN DRY-RUN ===")
print(f"Total baris terparse: {total}")
print(f"Total kandidat gagal: {failed}")
print("Database tidak dibuka dan tidak diubah.")
