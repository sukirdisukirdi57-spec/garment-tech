import csv
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

DB = "database/garment.db"
CSV_FILE = "tmp/catalog-audit/s6200a_parts_candidates.csv"
MACHINE_ID = 52
SOURCE_DOCUMENT_ID = 219
EXPECTED_MECHANISMS = 21
EXPECTED_PARTS = 623

path = Path(CSV_FILE)
if not path.is_file():
    raise SystemExit(f"CSV tidak ditemukan: {path}")

with path.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise SystemExit("CSV kosong.")

required = {
    "mechanism_id", "mechanism", "catalog_ref",
    "quantity_raw", "part_number", "part_name", "source_url"
}
missing_columns = required - set(rows[0].keys())
if missing_columns:
    raise SystemExit(f"Kolom CSV kurang: {sorted(missing_columns)}")

con = sqlite3.connect(DB)
try:
    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=?",
        (MACHINE_ID,)
    ).fetchone()
    document = con.execute(
        "SELECT id, machine_id, title FROM documents WHERE id=?",
        (SOURCE_DOCUMENT_ID,)
    ).fetchone()

    if not machine:
        raise SystemExit(f"Machine ID {MACHINE_ID} tidak ditemukan.")
    if not document:
        raise SystemExit(f"Document ID {SOURCE_DOCUMENT_ID} tidak ditemukan.")
    if document[1] != MACHINE_ID:
        raise SystemExit(
            f"Dokumen {SOURCE_DOCUMENT_ID} milik machine {document[1]}, "
            f"bukan {MACHINE_ID}."
        )

    existing = {
        "components": con.execute(
            "SELECT COUNT(*) FROM components WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0],
        "parts": con.execute(
            "SELECT COUNT(*) FROM parts WHERE machine_id=? AND source_document_id=?",
            (MACHINE_ID, SOURCE_DOCUMENT_ID)
        ).fetchone()[0],
        "links": con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            JOIN parts p ON p.id=cp.part_id
            WHERE c.machine_id=? AND p.machine_id=?
        """, (MACHINE_ID, MACHINE_ID)).fetchone()[0],
    }
finally:
    con.close()

mechanisms = {}
counts = Counter()
part_codes = defaultdict(list)
plus_refs = []
missing_refs = []
errors = []

for line_no, item in enumerate(rows, start=2):
    mid = item["mechanism_id"].strip()
    name = item["mechanism"].strip()
    ref = item["catalog_ref"].strip()
    qty_raw = item["quantity_raw"].strip()
    code = item["part_number"].strip()
    part_name = item["part_name"].strip()
    url = item["source_url"].strip()

    if not all((mid, name, code, part_name, qty_raw, url)):
        errors.append(f"Baris {line_no}: ada kolom wajib kosong.")
        continue

    try:
        int(mid)
        int(qty_raw)
    except ValueError:
        errors.append(
            f"Baris {line_no}: mechanism_id/quantity tidak valid "
            f"({mid!r}, {qty_raw!r})."
        )
        continue

    if mid in mechanisms and mechanisms[mid]["name"] != name:
        errors.append(f"ID mekanisme {mid} memiliki nama berbeda.")
    mechanisms[mid] = {"name": name, "url": url}
    counts[mid] += 1
    part_codes[code].append((mid, ref, part_name))

    if ref.endswith("+"):
        plus_refs.append((mid, ref, code, part_name))
    if not ref:
        missing_refs.append((mid, code, part_name))

print("===== PREVIEW IMPOR S-6200A — READ ONLY =====")
print(f"Mesin              : ID {machine[0]} / {machine[1]}")
print(f"Dokumen sumber     : ID {document[0]} / {document[2]}")
print(f"CSV                : {CSV_FILE}")
print(f"Jumlah baris       : {len(rows)}")
print(f"Mekanisme unik     : {len(mechanisms)}")
print(f"Komponen rencana   : {len(mechanisms)}")
print(f"Part rencana       : {len(rows)}")
print(f"Relasi rencana     : {len(rows)}")
print()
print("===== DATA S-6200A SEBELUM IMPOR =====")
for key, value in existing.items():
    print(f"{key:20}: {value}")

print()
print("===== JUMLAH PART PER MEKANISME =====")
for mid in sorted(mechanisms, key=int):
    print(f'{mid:>2} | {mechanisms[mid]["name"]} | {counts[mid]}')

print()
print("===== REFERENSI KHUSUS =====")
print(f"Ref berakhiran '+' : {len(plus_refs)}")
for mid, ref, code, name in plus_refs:
    print(f"  mekanisme {mid} | ref {ref} | {code} | {name}")

print()
print(f"Ref kosong         : {len(missing_refs)}")
for mid, code, name in missing_refs:
    print(f"  mekanisme {mid} | {code} | {name}")

duplicates = {
    code: values for code, values in part_codes.items()
    if len(values) > 1
}
print()
print("===== KODE PART BERULANG =====")
print(f"Kode berulang      : {len(duplicates)}")
for code, values in sorted(duplicates.items()):
    print(f"  {code}: {len(values)} baris")
    for mid, ref, name in values:
        print(f"    mekanisme {mid} | ref {ref or '(kosong)'} | {name}")

print()
print("===== VALIDASI =====")
checks = [
    ("Jumlah part sesuai", len(rows) == EXPECTED_PARTS),
    ("Jumlah mekanisme sesuai", len(mechanisms) == EXPECTED_MECHANISMS),
    ("Tidak ada kesalahan data dasar", not errors),
    ("Tidak ada komponen S-6200A sebelumnya", existing["components"] == 0),
    ("Tidak ada part dari dokumen ini sebelumnya", existing["parts"] == 0),
    ("URL sumber tiap mekanisme tersedia",
     all(m["url"].startswith("https://partsbook.brother.co.jp/")
         for m in mechanisms.values())),
]
for label, ok in checks:
    print(f'{"OK" if ok else "PERIKSA"} | {label}')

for err in errors:
    print("ERROR |", err)

print()
if all(ok for _, ok in checks):
    print("HASIL: PREVIEW LOLOS PEMERIKSAAN DASAR.")
    print("Belum ada perubahan database.")
    print("Ref '+' dan kode berulang tetap perlu ditangani dengan benar.")
else:
    print("HASIL: JANGAN IMPOR. Periksa laporan di atas.")

