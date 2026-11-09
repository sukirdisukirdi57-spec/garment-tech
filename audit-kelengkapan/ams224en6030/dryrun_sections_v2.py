import re
from pathlib import Path

path = Path("audit-kelengkapan/ams224en6030/partslist.txt")
lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

sections = [
    {
        "name": "FRAME & MISCELLANEOUS COVER COMPONENTS (4)",
        "header": 670,
        "expected": 91,
    },
    {
        "name": "X-Y COMPONENTS (2)",
        "header": 2192,
        "expected": 96,
    },
]

# Baris data: ref, note opsional, part number, deskripsi, qty mentah.
row_re = re.compile(
    r"^\s*(\d{1,3})\s+"
    r"(#\d{2})?\s*"
    r"([A-Z0-9][A-Z0-9-]*)\s+"
    r"(.+?)\s+"
    r"(\(?\d+(?:\.\d+)?\)?)\s*$"
)

for sec in sections:
    print(f"\n=== {sec['name']} ===")
    header_idx = sec["header"] - 1

    if "REF.NO" not in lines[header_idx].upper() or "PART NO" not in lines[header_idx].upper():
        print("ERROR: baris header tidak sesuai; hentikan bagian ini.")
        continue

    rows = []
    errors = []
    expected_ref = 1

    for idx in range(header_idx + 1, len(lines)):
        line = lines[idx]

        # Baris kosong setelah tabel boleh dilewati.
        if not line.strip():
            continue

        m = row_re.match(line)
        if not m:
            # Bagian tabel berakhir pada baris non-data.
            break

        ref_s, note, part_no, description, qty_raw = m.groups()
        ref = int(ref_s)

        # Hindari menganggap tabel berikutnya sebagai kelanjutan.
        if ref != expected_ref:
            errors.append(
                f"Baris {idx + 1}: referensi {ref}, "
                f"seharusnya {expected_ref}; berhenti."
            )
            break

        rows.append({
            "line": idx + 1,
            "ref": ref,
            "note": note or "",
            "part_number": part_no,
            "part_name": description.strip(),
            "quantity_raw": qty_raw,
        })
        expected_ref += 1

        if ref >= sec["expected"]:
            break

    refs = [r["ref"] for r in rows]
    print(f"Header: baris {sec['header']}")
    print(f"Baris terparse: {len(rows)} / target {sec['expected']}")
    print(f"Referensi awal-akhir: {refs[0] if refs else '-'}–{refs[-1] if refs else '-'}")
    print(f"Referensi hilang: {sorted(set(range(1, sec['expected'] + 1)) - set(refs))}")
    print(f"Kesalahan urutan: {errors or 'tidak ada'}")

    print("\nBaris pertama:")
    for r in rows[:3]:
        print(r)

    print("\nBaris terakhir:")
    for r in rows[-3:]:
        print(r)

    if len(rows) == sec["expected"] and refs == list(range(1, sec["expected"] + 1)):
        print("STATUS: jumlah dan urutan referensi cocok.")
    else:
        print("STATUS: BELUM VALID — jangan impor.")

print("\nDry-run selesai. Database tidak dibuka atau diubah.")
