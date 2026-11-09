import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tmp/bas311hn/c5_staging_review.csv"

# Data ditranskripsi dari katalog resmi, C5, halaman cetak 13.
# Seluruh baris masih harus ditinjau sebelum impor.
rows = [
    (1, "SB4346001", 1, "FEED PLATE 311H", "Feed plate; perlu konfirmasi cakupan X-Y"),
    (2, "SA4852201", 1, "FEED PLATE 220X100", "Feed plate; perlu konfirmasi cakupan X-Y"),
    (3, "S55484001", 2, "BOLT SOCKET (S/P WASHER) M5X10", "Pengikat"),
    (4, "SB4343001", 1, "X SENSOR PLATE", "Pelat sensor X; kandidat"),
    (5, "018400836", 2, "BOLT SOCKET M4X8", "Pengikat"),
    (6, "SB4342001", 1, "Y SENSOR PLATE", "Pelat sensor Y; kandidat"),
    (7, "018400836", 2, "BOLT SOCKET M4X8", "Pengikat"),
    (8, "SB4458001", 1, "X-FEED MOTOR L ASSY", "Motor feed X; kandidat utama"),
    (9, "SB4275001", 1, "PULSE MOTOR ASSY X", "Motor pulsa X; kandidat utama"),
    (10, "SB4334001", 1, "X MOTOR SETTING PLATE", "Pelat pemasangan motor X"),
    (11, "018401036", 4, "BOLT SOCKET M4X10", "Pengikat"),
    (12, "SA3707101", 1, "GEAR 16", "Gear penggerak; kandidat"),
    (13, "012060536", 2, "SET SCREW SOCKET (FT) M6X5", "Pengikat"),
    (14, "SA6450101", 1, "BEARING HOLDER BASE", "Dudukan bearing; kandidat"),
    (15, "SA6451101", 1, "BEARING HOLDER ASSY", "Rakitan dudukan bearing; kandidat"),
    (16, "018401036", 2, "BOLT SOCKET M4X10", "Pengikat"),
    (17, "018501036", 2, "BOLT SOCKET M5X10", "Pengikat"),
    (18, "SA4224001", 1, "MARK ATTENTION 30X40", "Label peringatan"),
    (19, "S42446001", 3, "BOLT SOCKET (S/P WASHER) M6X14", "Pengikat"),
    (20, "SB4459201", 1, "Y-FEED MOTOR L ASSY", "Motor feed Y; kandidat utama"),
    (21, "SB4276001", 1, "PULSE MOTOR ASSY Y", "Motor pulsa Y; kandidat utama"),
    (22, "SB4188001", 1, "Y MOTOR SETTING PLATE", "Pelat pemasangan motor Y"),
    (23, "018401036", 4, "BOLT SOCKET M4X10", "Pengikat"),
    (24, "SA4197101", 1, "FEED GEAR", "Gear feed; kandidat"),
    (25, "012060536", 2, "SET SCREW SOCKET (FT) M6X5", "Pengikat"),
    (26, "SA6450101", 1, "BEARING HOLDER BASE", "Dudukan bearing; kandidat"),
    (27, "SB4364101", 2, "BEARING HOLDER SPACER", "Spacer dudukan bearing; kandidat"),
    (28, "SA6451101", 1, "BEARING HOLDER ASSY", "Rakitan dudukan bearing; kandidat"),
    (29, "018401236", 2, "BOLT SOCKET M4X12", "Pengikat"),
    (30, "018501036", 2, "BOLT SOCKET M5X10", "Pengikat"),
    (31, "SB5071001", 1, "Y-PLATE PACKING M", "Packing pelat Y; kandidat"),
    (32, "SB4181001", 1, "Y-PLATE PACKING", "Packing pelat Y; kandidat"),
    (33, "S55485001", 3, "BOLT SOCKET (S/P WASHER) M5X12", "Pengikat"),
]

fields = [
    "catalog_ref", "part_number", "quantity_raw", "part_name",
    "diagram_page", "mechanism", "verification", "review_note"
]

if len(rows) != 33:
    raise SystemExit(f"STOP: jumlah referensi {len(rows)}, seharusnya 33")

refs = [r[0] for r in rows]
if refs != list(range(1, 34)):
    raise SystemExit("STOP: referensi katalog tidak lengkap/berurutan")

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for ref, code, qty, name, note in rows:
        writer.writerow({
            "catalog_ref": ref,
            "part_number": code,
            "quantity_raw": qty,
            "part_name": name,
            "diagram_page": 13,
            "mechanism": "C5 Feed mechanism (BAS-311HN/326H)",
            "verification": "REVIEW_REQUIRED",
            "review_note": note,
        })

print("Staging dibuat:", OUTPUT.relative_to(ROOT))
print("Jumlah referensi:", len(rows))
print("Halaman katalog cetak: 13 (C5)")
print("Status: BELUM SIAP IMPOR")
print("Database diubah: TIDAK")
