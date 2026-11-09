import csv
import re
from pathlib import Path

FILE = Path("staging_kemunculan_katalog_juki.csv")

with FILE.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

parsed = []
errors = []

for row in rows:
    original = row["catalog_line_original"].rstrip()
    pn = row["part_number"].strip()
    page = row["pdf_page"]
    expected_ref = row["catalog_ref"]

    # Gunakan nomor part yang sudah diverifikasi pada staging.
    positions = [
        m.start() for m in re.finditer(re.escape(pn), original,
                                      flags=re.IGNORECASE)
    ]

    if len(positions) != 1:
        errors.append((row, f"PN muncul {len(positions)} kali di baris sumber"))
        continue

    start = positions[0]
    prefix = original[:start].strip()
    suffix = original[start + len(pn):].strip()

    # Ref adalah angka pertama di awal baris.
    ref_match = re.match(r"^(\d+)\b", prefix)
    if not ref_match:
        errors.append((row, "Ref tidak terbaca"))
        continue

    ref = ref_match.group(1)
    if ref != expected_ref:
        errors.append((row, f"Ref berbeda: {ref}"))
        continue

    # Ambil marker dari bagian sebelum nomor part.
    markers = re.findall(r"#\d+|☆", prefix)
    marker = " ".join(markers)

    # Kuantitas berada di ujung baris; pertahankan bentuk mentah.
    qty_match = re.search(r"(\(\s*\d+(?:\.\d+)?\s*\)|\d+(?:\.\d+)?)\s*$", suffix)
    if not qty_match:
        errors.append((row, "Kuantitas tidak terbaca"))
        continue

    qty = qty_match.group(1)
    name = suffix[:qty_match.start()].strip()

    if not name:
        errors.append((row, "Nama part kosong"))
        continue

    parsed.append({
        "page": page,
        "ref": ref,
        "marker": marker,
        "pn": pn,
        "name": name,
        "qty": qty,
        "original": original,
    })

print("=== HASIL AUDIT PARSER REVISI ===")
print("Total baris:", len(rows))
print("Berhasil dipisah:", len(parsed))
print("Perlu pemeriksaan:", len(errors))

print("\n=== CONTOH BARIS NORMAL ===")
for item in parsed[:8]:
    print(
        f'PDF {item["page"]} | Ref {item["ref"]} | '
        f'Marker={item["marker"]!r} | PN={item["pn"]} | '
        f'Nama={item["name"]!r} | Qty mentah={item["qty"]!r}'
    )

print("\n=== CONTOH BARIS BERTANDA VARIAN ===")
shown = 0
for item in parsed:
    if item["marker"]:
        print(
            f'PDF {item["page"]} | Ref {item["ref"]} | '
            f'Marker={item["marker"]!r} | PN={item["pn"]} | '
            f'Nama={item["name"]!r} | Qty={item["qty"]!r}'
        )
        shown += 1
        if shown >= 12:
            break

print("\n=== BARIS YANG PERLU DIPERIKSA ===")
for row, reason in errors[:20]:
    print(
        f'PDF {row["pdf_page"]} | Ref {row["catalog_ref"]} | '
        f'PN={row["part_number"]} | {reason}'
    )
    print("  Sumber:", row["catalog_line_original"])

if len(errors) > 20:
    print(f"... dan {len(errors) - 20} baris lainnya.")
