import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tmp/bas311hn/h_staging_review.csv"

# H. Bobbin winder mechanism — halaman tercetak 37.
# Transkripsi awal; seluruh baris wajib diaudit sebelum impor.
rows = [
    (1, "SB4389001", "1", "TOP COVER 311H"),
    (2, "SA3290001", "1", "SHAFT, BW-LEVER"),
    (3, "012500536", "2", "SET SCREW SOCKET (FT) M5X5"),
    (4, "SA3291001", "1", "BOBBIN WINDER LEVER"),
    (5, "SA4171001", "1", "SPRING HOOK"),
    (6, "152936001", "1", "PLATE SPRING"),
    (7, "152937001", "1", "WASHER"),
    (8, "062350616", "1", "SCREW PAN M3.5X6"),
    (9, "155559021", "3", "WASHER PLAIN"),
    (10, "048050342", "3", "RETAINING RING E5"),
    (11, "SA3293001", "1", "STUD B-WINDER CLAW"),
    (12, "SA1984001", "1", "BOBBIN PRESSER ARM"),
    (13, "018401236", "1", "BOLT SOCKET M4X12"),
    (14, "SA3294001", "1", "BOBBIN PRESSER"),
    (15, "S23418002", "1", "SCREW M4X5"),
    (16, "SA3295001", "1", "CLAW B-WINDER"),
    (17, "012400436", "4", "SET SCREW SOCKET (FT) M4X4"),
    (18, "S10438001", "1", "SPRING, TWIST"),
    (19, "SA4796001", "1", "SPACER COLLER"),
    (20, "SA3296001", "1", "BOBBIN WINDER SHAFT"),
    (21, "SA3297001", "1", "WHEEL, B-WINDER"),
    (22, "120448001", "1", "BOBBIN WINDER RUBBER BAND"),
    (23, "SA1988001", "1", "BOBBIN SUPPORT"),
    (24, "S10268001", "1", "SPRING"),
    (25, "SA3298001", "1", "STPPER SHAFT, B-WINDER"),
    (26, "SA3299001", "1", "KNIFE"),
    (27, "062500616", "1", "SCREW PAN M5X6"),
    (28, "SB1253001", "1", "BOBBIN WINDER TENSION ASSY"),
    (29, "145446002", "2", "DISC TENSION"),
    (30, "100401022", "1", "TENSION SPRING"),
    (31, "S31032002", "1", "TENSION NUT"),
    (32, "S12441001", "1", "WASHER"),
    (33, "062061016", "6", "SCREW PAN M6X10"),
]

if OUTPUT.exists():
    raise SystemExit(f"STOP: staging sudah ada, tidak ditimpa: {OUTPUT}")

if [r[0] for r in rows] != list(range(1, 34)):
    raise SystemExit("STOP: referensi harus lengkap 1–33")

fields = [
    "catalog_ref", "part_number", "quantity_raw", "part_name",
    "diagram_page", "mechanism", "verification", "review_note",
]

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for ref, code, qty, name in rows:
        writer.writerow({
            "catalog_ref": ref,
            "part_number": code,
            "quantity_raw": qty,
            "part_name": name,
            "diagram_page": 37,
            "mechanism": "H Bobbin winder mechanism (BAS-311HN/326H)",
            "verification": "REVIEW_REQUIRED",
            "review_note": (
                "Transkripsi awal halaman tercetak 37; "
                "wajib dicocokkan dengan katalog sebelum impor."
            ),
        })

print("Staging dibuat:", OUTPUT.relative_to(ROOT))
print("Jumlah referensi:", len(rows))
print("Rentang ref: 1–33")
print("Halaman cetak/diagram_page: 37")
print("Semua status: REVIEW_REQUIRED")
print("Database diubah: TIDAK")
